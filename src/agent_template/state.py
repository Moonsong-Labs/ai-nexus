"""Define the shared values."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated

from agent_template.configuration import Configuration
from agent_template.memory import SemanticMemory, load_static_memories

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class State:
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages] = field(default_factory=list)
    """The messages in the conversation."""

    user_id: str = "default"
    """The user ID used for memory management."""

__all__ = [
    "State",
]
