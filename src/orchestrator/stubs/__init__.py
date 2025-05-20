"""Stubs for tests."""

# ruff: noqa: D107 D101 D102

from typing import Any, List, Optional

from langchain_core.messages import (
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.configuration import AgentConfiguration
from common.graph import AgentGraph
from orchestrator.state import State


class MessageWheel:
    def __init__(self, messages: List[str]):
        self.messages = messages
        self.idx = 0

    def peek(self) -> str:
        return self.messages[self.idx]

    def next(self) -> str:
        msg = self.messages[self.idx]
        self.idx = (self.idx + 1) % len(self.messages)
        return msg


model_requirements_messages = MessageWheel(
    [
        """
        I collected all the details. Here are the requirements:    
            User wants a clean HTML website, with clean design.
            
        Additionally update memory: Always ask me questions starting with "Ola!""",
        """
        I collected all the details. Here are the requirements:
            User wants a clean HTML website, with clean design. It should focus on the mobile market,
            have a light scheme, be fast, responsive and load within 0.3 seconds.
            These are the complete requirements, nothing more is necessary.
        
        Additionally update memory: Always ask me questions starting with "Ola!
        """,
    ]
)
model_coder_messages = MessageWheel(
    [
        """I have finished coding.""",
        """I fixed the required issue.""",
    ]
)
model_tester_messages = MessageWheel(
    [
        """I found issues with code. Here are the details:
    HTML should have <!doctype> tag.
    """,
        """Everything looks good.""",
        """I found issues with code. Here are the details:
    <p> tag missing.
    """,
        """Everything looks good.""",
    ]
)
model_reviewer_messages = MessageWheel(
    [
        """I found issues with code. Here are the details:
    Add a new line in the end.
    """,
        """Everything looks good.""",
    ]
)


class RequirementsGathererStub(AgentGraph):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize the RequirementsGathererStub with optional configuration, checkpointer, and store.

        Args:
            agent_config: Optional agent configuration for the stub.
            checkpointer: Optional checkpointer for state persistence.
            store: Optional store for data management.
        """
        super().__init__(
            "Requirements Gatherer Stub", agent_config, checkpointer, store
        )

        # stub the compiled_graph
        def runnable(state: State, config: RunnableConfig, store: BaseStore):
            return {
                "messages": state.messages,
                "summary": model_requirements_messages.next(),
            }

        self._compiled_graph = runnable

    def create_builder(self) -> StateGraph:
        """Return None to indicate that no builder is provided for this stub implementation."""
        return None


class ArchitectStub(AgentGraph):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__("Architect Stub", agent_config, checkpointer, store)

        # stub the compiled_graph
        def runnable(state: State, config: RunnableConfig, store: BaseStore):
            return {
                "messages": state.messages,
                "summary": """I am finished with the design. Here are the details:
                    The design should be simple HTML file with CSS styling.
                    """,
            }

        self._compiled_graph = runnable

    def create_builder(self) -> StateGraph:
        """Return None to indicate that no builder is provided for this stub implementation."""
        return None


class CoderStub(AgentGraph):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__("Coder Stub", agent_config, checkpointer, store)

        # stub the compiled_graph
        def runnable(state: State, config: RunnableConfig, store: BaseStore):
            return {
                "messages": state.messages,
                "summary": model_coder_messages.next(),
            }

        self._compiled_graph = runnable

    def create_builder(self) -> StateGraph:
        """Return None to indicate that no builder is provided for this stub implementation."""
        return None


class TesterStub(AgentGraph):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__("Tester Stub", agent_config, checkpointer, store)

        # stub the compiled_graph
        def runnable(state: State, config: RunnableConfig, store: BaseStore):
            return {
                "messages": state.messages,
                "summary": model_tester_messages.next(),
            }

        self._compiled_graph = runnable

    def create_builder(self) -> StateGraph:
        """Return None to indicate that no builder is provided for this stub implementation."""
        return None


class ReviewerStub(AgentGraph):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__("Reviewer Stub", agent_config, checkpointer, store)

        # stub the compiled_graph
        def runnable(state: State, config: RunnableConfig, store: BaseStore):
            return {
                "messages": state.messages,
                "summary": model_reviewer_messages.next(),
            }

        self._compiled_graph = runnable

    def create_builder(self) -> StateGraph:
        """Return None to indicate that no builder is provided for this stub implementation."""
        return None


def memorizer(state: State, config: RunnableConfig, store: BaseStore):
    """Memorize instructions."""
    message = state.messages[-1]
    tool_call_id = message.tool_calls[0]["id"]
    origin = message.tool_calls[0]["args"]["origin"]
    content = message.tool_calls[0]["args"]["content"]
    # msg = f"[MEMORIZE] for {origin}: {content}"
    # print(msg)  # noqa: T201
    return {
        "messages": [
            ToolMessage(
                content=f"Memorized '{content}' for '{origin}'",
                tool_call_id=tool_call_id,
            )
        ]
    }
