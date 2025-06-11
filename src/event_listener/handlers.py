"""Event-specific webhook handlers that invoke the orchestrator."""

import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from .config import settings
from .event_processor import get_event_processor

logger = logging.getLogger(__name__)


class BaseEventHandler(ABC):
    """Abstract base class for GitHub event handlers."""

    def __init__(self, orchestrator=None):
        """Initialize handler with orchestrator instance.

        Args:
            orchestrator: The OrchestratorGraph instance to invoke (lazy loaded if None)
        """
        self._orchestrator = orchestrator
        self.event_processor = get_event_processor()

    @property
    def orchestrator(self):
        """Lazy load orchestrator when first accessed."""
        if self._orchestrator is None:
            self._orchestrator = self._create_orchestrator()
        return self._orchestrator

    def _create_orchestrator(self):
        """Create orchestrator instance with lazy imports."""
        try:
            from langgraph.checkpoint.memory import InMemorySaver
            from langgraph.store.memory import InMemoryStore

            from orchestrator.configuration import (
                Configuration as OrchestratorConfiguration,
            )
            from orchestrator.graph import OrchestratorGraph

            config = OrchestratorConfiguration()
            return OrchestratorGraph(
                agent_config=config, checkpointer=InMemorySaver(), store=InMemoryStore()
            )
        except Exception as e:
            logger.error(f"Failed to create orchestrator: {e}")
            raise RuntimeError(f"Orchestrator initialization failed: {e}") from e

    @abstractmethod
    async def can_handle(self, event: Dict[str, Any]) -> bool:
        """Check if this handler can process the given event.

        Args:
            event: GitHub webhook event data

        Returns:
            bool: True if handler can process this event
        """
        pass

    @abstractmethod
    async def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process the event and invoke orchestrator.

        Args:
            event: GitHub webhook event data

        Returns:
            dict: Processing result
        """
        pass

    async def invoke_orchestrator(self, state, thread_id: str) -> Dict[str, Any]:
        """Invoke the orchestrator with the given state.

        Args:
            state: The state object to process
            thread_id: Unique thread ID for this event

        Returns:
            dict: Orchestrator result
        """
        print(f"Invoking orchestrator with state: {state}")
        print(f"Thread ID: {thread_id}")

        try:
            from langchain_core.runnables import RunnableConfig

            # Create proper config
            config = RunnableConfig(
                recursion_limit=250, configurable={"thread_id": thread_id}
            )

            # Set timeout for orchestrator execution
            result = await asyncio.wait_for(
                self.orchestrator.compiled_graph.ainvoke(state, config),
                timeout=settings.orchestrator_timeout,
            )

            return {
                "status": "success",
                "thread_id": thread_id,
                "summary": result.get("summary", ""),
                "error": result.get("error", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except TimeoutError:
            logger.error(f"Orchestrator timeout for thread {thread_id}")
            return {
                "status": "timeout",
                "thread_id": thread_id,
                "error": f"Orchestrator execution timed out after {settings.orchestrator_timeout} seconds",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(
                f"Orchestrator error for thread {thread_id}: {str(e)}\n{traceback.format_exc()}"
            )
            return {
                "status": "error",
                "thread_id": thread_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def generate_thread_id(self, event: Dict[str, Any]) -> str:
        """Generate a unique thread ID for the event.

        Args:
            event: GitHub webhook event data

        Returns:
            str: Unique thread ID
        """
        repo = event.get("repository", {})
        repo_id = repo.get("id", "unknown")
        timestamp = int(datetime.utcnow().timestamp())

        # Include relevant identifiers based on event type
        if "pull_request" in event:
            pr_number = event["pull_request"].get("number", "unknown")
            return f"pr_{repo_id}_{pr_number}_{timestamp}"
        elif "issue" in event:
            issue_number = event["issue"].get("number", "unknown")
            return f"issue_{repo_id}_{issue_number}_{timestamp}"
        else:
            return f"event_{repo_id}_{timestamp}"


class AssignedIssueHandler(BaseEventHandler):
    """Handles issue assignment events only."""

    async def can_handle(self, event: Dict[str, Any]) -> bool:
        """Check if this is an issue assigned event we should handle."""
        event_type = event.get("X-GitHub-Event", "")
        if event_type != "issues":
            return False

        action = event.get("action", "")
        # Only handle assigned events
        return action == "assigned"

    async def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process issue assigned event."""
        event_type = "issues"

        # Check if we should process this event
        if not self.event_processor.should_process_event(event_type, event):
            return {
                "status": "skipped",
                "reason": "Event action not configured for processing",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Convert to State
        state = self.event_processor.process_event(event_type, event)

        # Generate thread ID
        thread_id = self.generate_thread_id(event)

        # Log processing
        issue_number = event.get("issue", {}).get("number", "unknown")
        assignee = event.get("issue", {}).get("assignee", {}).get("login", "unknown")
        repo_name = event.get("repository", {}).get("full_name", "unknown")
        logger.info(
            f"Processing issue assigned to {assignee} for issue #{issue_number} in {repo_name}"
        )

        # Invoke orchestrator
        return await self.invoke_orchestrator(state, thread_id)


class CommentTriggerHandler(BaseEventHandler):
    """Handles issue comment it shouldn with AI bot trigger phrases."""

    async def can_handle(self, event: Dict[str, Any]) -> bool:
        """Check if this is a comment event we should handle."""
        event_type = event.get("X-GitHub-Event", "")
        if event_type != "issue_comment":
            return False

        action = event.get("action", "")
        # Only handle created comment events
        return action == "created"

    async def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process comment trigger event."""
        event_type = "issue_comment"

        # Check if we should process this event (contains trigger phrases)
        if not self.event_processor.should_process_event(event_type, event):
            return {
                "status": "skipped",
                "reason": "Comment does not contain AI bot trigger phrases",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Convert to State
        state = self.event_processor.process_event(event_type, event)

        # Generate thread ID
        thread_id = self.generate_thread_id(event)

        # Log processing
        issue_number = event.get("issue", {}).get("number", "unknown")
        commenter = event.get("comment", {}).get("user", {}).get("login", "unknown")
        repo_name = event.get("repository", {}).get("full_name", "unknown")
        comment_body = event.get("comment", {}).get("body", "")[:100] + "..."
        logger.info(
            f"Processing AI bot trigger comment by {commenter} for issue #{issue_number} in {repo_name}"
        )
        logger.info(f"Comment preview: {comment_body}")

        # Invoke orchestrator
        return await self.invoke_orchestrator(state, thread_id)


class HandlerRegistry:
    """Registry for event handlers."""

    def __init__(self):
        """Initialize handler registry.
        """
        self._handlers: List[BaseEventHandler] = []
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default event handlers."""
        # Register both assignment and comment trigger handlers
        self.register(AssignedIssueHandler)
        self.register(CommentTriggerHandler)

    def register(self, handler_class: Type[BaseEventHandler]):
        """Register a new handler.

        Args:
            handler_class: Handler class to register
        """
        handler = handler_class()  # No orchestrator passed, will be lazy loaded
        self._handlers.append(handler)
        logger.info(f"Registered handler: {handler_class.__name__}")

    async def handle_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route event to appropriate handler.

        Args:
            event_type: GitHub event type
            event_data: Event payload

        Returns:
            dict: Handler result
        """
        # Add event type to data for handlers
        event_data["X-GitHub-Event"] = event_type

        # Find handler
        for handler in self._handlers:
            if await handler.can_handle(event_data):
                logger.info(f"Using handler: {handler.__class__.__name__}")
                return await handler.handle(event_data)

        # No handler found
        logger.warning(f"No handler found for event type: {event_type}")
        return {
            "status": "unhandled",
            "reason": f"No handler registered for event type: {event_type}",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global handler registry
_handler_registry: Optional[HandlerRegistry] = None


def get_handler_registry() -> HandlerRegistry:
    """Get or create global handler registry."""
    global _handler_registry
    if _handler_registry is None:
        _handler_registry = HandlerRegistry()
        logger.info("Created new HandlerRegistry")
    return _handler_registry


async def cleanup_handlers():
    """Cleanup global instances."""
    global _handler_registry
    _handler_registry = None
