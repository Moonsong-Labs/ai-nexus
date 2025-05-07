"""State for the coder agent."""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class State(TypedDict):
    """State for the coder agent."""

    messages: Annotated[list, add_messages]
