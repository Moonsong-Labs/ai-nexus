"""State for the coder agent."""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class State(TypedDict):
    """State for the coder agent."""

    messages: Annotated[list[AnyMessage], add_messages]


__all__ = ["State"]
