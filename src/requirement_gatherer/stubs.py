"""Stub implementations for the requirement gatherer component."""

from common.utils.stubs import MessageWheel

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
