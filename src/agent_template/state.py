"""Define the shared values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any
import logging

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated

from agent_template.memory import SemanticMemory, load_static_memories
from agent_template.configuration import Configuration

logger = logging.getLogger(__name__)

@dataclass(kw_only=True)
class State:
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages] = field(default_factory=list)
    """The messages in the conversation."""
    
    semantic_memory: SemanticMemory = None
    """The semantic memory used by the agent for personalized memories."""
        
    user_id: str = "default"
    """The user ID used for memory management."""
    
    def initialize_memories(self, config: Optional[Configuration] = None) -> None:
        """Initialize memory systems based on configuration.
        
        Args:
            config: Optional configuration object with memory enablement flags.
                   If None, defaults to enabling all memory systems.
        """
        # Set defaults if no config provided
        use_static = True
        
        # Override with config values if provided
        if config:
            use_static = config.use_static_mem
            self.user_id = config.user_id
        
        # Initialize semantic memory
        if not self.semantic_memory:
            self.semantic_memory = SemanticMemory(user_id=self.user_id)
            # Load static memories directly if enabled
            if use_static:
                load_static_memories(self.semantic_memory.store, self.user_id)

            logger.info(f"Memory initialized for user {self.user_id}")


__all__ = [
    "State",
]
