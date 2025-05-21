"""State for the graph."""

from dataclasses import dataclass, field
from typing import Optional

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated

from common.state import Project


@dataclass(kw_only=True)
class State:
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages]
    """The messages in the conversation."""
    summary: str = ""
    """The orchestrator summary."""
    project: Optional[Project] = None


__all__ = [
    "State",
]
