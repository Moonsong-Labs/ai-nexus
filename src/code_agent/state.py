"""State for the code agent."""

from typing import List

from langchain_core.messages import BaseMessage


class State:
    """State for the code agent."""

    messages: List[BaseMessage] 