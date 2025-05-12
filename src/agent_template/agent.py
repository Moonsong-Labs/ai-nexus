"""Agent implementation that uses semantic memory."""

import logging
from typing import Dict, List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import Tool

from agent_template import configuration, prompts
from agent_template.configuration import Configuration
from agent_template.state import State
from agent_template.tools import create_file_dump_tool
from common.components.memory import (
    SemanticMemory,
)

logger = logging.getLogger(__name__)

# Tool category constants
MEMORY_TOOLS = "memory"
UTILITY_TOOLS = "utility"
DEFAULT_USER_ID = "default_user"


class Agent:
    """Agent class that handles LLM interactions with semantic memory capabilities."""

    def __init__(self, config: Configuration):
        """Initialize the Agent with configuration.

        Args:
            config: Configuration object containing model and memory settings.
        """
        self.llm = init_chat_model(config.model)
        self.tools: Dict[str, List[Tool]] = {MEMORY_TOOLS: [], UTILITY_TOOLS: []}
        self.semantic_memory: Optional[SemanticMemory] = None
        self.initialized = False
        self.name = configuration.AGENT_NAME
        # Ensure self.user_id is never None or empty
        self.user_id = (
            config.user_id
            if hasattr(config, "user_id") and config.user_id
            else DEFAULT_USER_ID
        )

    def initialize(self, config: Configuration):
        """Initialize the agent's memories."""
        # Ensure agent's main user_id is robustly set before initializing memory
        current_agent_user_id = config.user_id if config.user_id else DEFAULT_USER_ID
        self.user_id = current_agent_user_id

        # Initialize semantic memory if not already initialized
        if not self.semantic_memory:
            # agent_name in SemanticMemory is derived from config.user_id
            self.semantic_memory = SemanticMemory(
                agent_name=current_agent_user_id, config=config
            )
            logger.info(f"Agent memory initialized for user {current_agent_user_id}")

        # Bind memory tools to the LLM
        self.tools[MEMORY_TOOLS] = self.semantic_memory.get_tools()

        # Initialize utility tools
        self.tools[UTILITY_TOOLS] = [create_file_dump_tool()]

        # Bind all tools to the LLM
        all_tools = self.tools[MEMORY_TOOLS] + self.tools[UTILITY_TOOLS]
        self.llm = self.llm.bind_tools(all_tools)

        self.initialized = True
        logger.info("Agent initialized")

    async def __call__(self, state: State, config: RunnableConfig) -> dict:
        """Process the input state with the LLM and return updated messages.

        Args:
            state: Current conversation state
            config: Runtime configuration

        Returns:
            Dictionary containing updated messages
        """
        if not self.initialized:
            raise Exception("Agent not initialized")

        # Ensure 'configurable' exists in the runtime config
        if "configurable" not in config:
            config["configurable"] = {}

        # Ensure 'user_id' in 'configurable' is not empty for LangMem tools
        # LangMem tools use config["configurable"]["user_id"] to resolve "{user_id}" in namespace
        runtime_user_id = config["configurable"].get("user_id")
        if not runtime_user_id:  # Handles None or empty string
            # Fallback to the agent's initialized user_id if runtime one is missing/empty
            config["configurable"]["user_id"] = self.user_id

        system_msg = SystemMessage(content=prompts.SYSTEM_PROMPT)
        messages = [system_msg] + state.messages
        messages_after_invoke = await self.llm.ainvoke(messages, config=config)

        return {"messages": messages_after_invoke}

    def get_tools(self) -> List[Tool]:
        """Get all tools available to this agent.

        Returns:
            List of tools for accessing semantic memory and utilities
        """
        if not self.initialized:
            raise Exception("Agent not initialized")

        # Return all tools
        return self.tools[MEMORY_TOOLS] + self.tools[UTILITY_TOOLS]
