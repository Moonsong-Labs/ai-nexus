"""Stub implementations for the requirement gatherer component."""

from typing import Any
from common.utils.stubs import MessageWheel
from langchain_core.runnables import RunnableConfig
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


async def call_model_stub(state: Any, config: RunnableConfig | None = None):
    """Async invoke."""
    return {
        "messages": state.messages,
        "summary": model_requirements_messages.next(),
    }