"""State for the coder agent."""

from dataclasses import dataclass
from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


@dataclass(kw_only=True)
class State:
    """State for the coder agent."""

    messages: Annotated[list[AnyMessage], add_messages]
    summary: str = ""
    """The coding summary."""


__all__ = ["State"]
