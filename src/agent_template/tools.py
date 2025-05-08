"""Define the agent's tools."""

from typing import List

from langchain_core.tools import Tool

from agent_template.configuration import Configuration
from agent_template.memory import get_langmem_tools


def get_memory_tools(config: Configuration) -> List[Tool]:
    """Get the appropriate memory tools based on configuration.

    Args:
        config: The runnable configuration.

    Returns:
        A list of memory tools.
    """
    # Use LangMem tools
    return get_langmem_tools(config.user_id)
