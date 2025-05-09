"""Graphs that extract memories on a schedule."""

import logging
from typing import List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import Tool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent_template import configuration, prompts
from agent_template.configuration import Configuration
from agent_template.memory import (
    SemanticMemory,
    create_memory_store,
    create_memory_tools,
    load_static_memories,
)
from agent_template.state import State

logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, config: Configuration):
        self.llm = init_chat_model(config.model)
        self.tools = []
        self.semantic_memory: Optional[SemanticMemory] = None
        self.initialized = False
        self.name = configuration.AGENT_NAME

    def initialize_memories(self, config: Configuration) -> None:
        """Initialize agent's memory systems based on configuration.

        Args:
            config: Configuration object with memory enablement flags.
        """
        # Initialize semantic memory if not already initialized
        if not self.semantic_memory:
            self.semantic_memory = SemanticMemory(agent_name=config.user_id)
            if config.use_static_mem:
                load_static_memories(self.semantic_memory.store, config.user_id)
            logger.info(f"Agent memory initialized for user {config.user_id}")

    def initialize(self, config: RunnableConfig):
        """Initialize the agent's memories."""
        # Initialize semantic memory
        self.initialize_memories(config)

        # Bind memory tools to the LLM
        self.tools = self.semantic_memory.get_tools()
        self.llm = self.llm.bind_tools(self.tools)
        self.initialized = True
        logger.info("Agent initialized")

    async def __call__(self, state: State, config: RunnableConfig) -> dict:
        if not self.initialized:
            raise Exception("Agent not initialized")

        system_msg = SystemMessage(content=prompts.SYSTEM_PROMPT)
        messages = [system_msg] + state.messages
        messages_after_invoke = await self.llm.ainvoke(messages)

        # Debug logs
        logger.debug(f"Semantic Memory: {self.semantic_memory}")

        return {"messages": messages_after_invoke}

    def get_tools(self) -> List[Tool]:
        if self.semantic_memory:
            return self.semantic_memory.get_tools()
        else:
            # Fallback if called before semantic_memory is initialized
            store = create_memory_store()
            return create_memory_tools("memo", store)

    def route_message(self, state: State) -> str:
        """Routes to agent_init if not initialized, otherwise to call_model."""
        if self.initialized:
            return "call_model"
        else:
            return "agent_init"


def graph_builder() -> StateGraph:
    # Create the graph + all nodes
    builder = StateGraph(State)

    # Create the configuration instance
    config = Configuration()
    config.use_static_mem = True

    # Create the agent instance
    agent = Agent(config)
    agent.initialize(config)

    # Add nodes to the graph
    builder.add_node("call_model", agent.__call__)

    tool_node = ToolNode(agent.get_tools())
    builder.add_node("tools", tool_node)

    # Define the flow
    builder.add_edge("__start__", "call_model")
    # builder.add_conditional_edges("__start__", agent.route_message, ["agent_init", "call_model"])
    builder.add_conditional_edges("call_model", tools_condition)
    # builder.add_edge("agent_init", "call_model")
    builder.add_edge("tools", "call_model")
    builder.add_edge("call_model", END)

    return builder


graph = graph_builder().compile()
graph.name = "Agent Template"


__all__ = ["graph"]
