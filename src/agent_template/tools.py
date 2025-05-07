"""Define the agent's tools."""

import uuid
from typing import Annotated, List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, Tool
from langgraph.store.base import BaseStore

from agent_template.configuration import Configuration
from agent_template.memory import upsert_memory, get_langmem_tools

def get_memory_tools(config: Configuration) -> List[Tool]:
    """Get the appropriate memory tools based on configuration.
    
    Args:
        config: The runnable configuration.
        
    Returns:
        A list of memory tools.
    """
    
    # Use LangMem tools
    return get_langmem_tools(config.user_id)
    
