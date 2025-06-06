"""Define the shared values."""

from __future__ import annotations

from dataclasses import dataclass
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

    project: Optional[Project] = None
    """The active project."""

    summary: str = ""
    """The code review summary."""
    error: str = ""
    """If any fatal error occurred."""


__all__ = [
    "State",
]
