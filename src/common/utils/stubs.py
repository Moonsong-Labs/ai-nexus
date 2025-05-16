"""Utilities for managing message rotation and sequence in stubs."""

from typing import List


class MessageWheel:
    """A class for cycling through a list of messages in a circular fashion."""

    def __init__(self, messages: List[str]):
        """Initialize the MessageWheel with a list of messages.

        Args:
            messages: A list of string messages to cycle through.
        """
        self.messages = messages
        self.idx = 0

    def peek(self) -> str:
        """Return the current message without advancing the index.

        Returns:
            The current message.
        """
        return self.messages[self.idx]

    def next(self) -> str:
        """Return the current message and advance to the next message.

        Returns:
            The current message.
        """
        msg = self.messages[self.idx]
        self.idx = (self.idx + 1) % len(self.messages)
        return msg
