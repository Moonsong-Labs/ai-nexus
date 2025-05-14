"""Graph implementation for agent template using AgentGraph."""

import logging
from typing import Any, Callable, Coroutine, Dict, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from agent_template.configuration import Configuration
from agent_template.prompts import SYSTEM_PROMPT
from agent_template.state import State
from common.config import BaseConfiguration
from common.graph import AgentGraph

logger = logging.getLogger(__name__)


class AgentTemplateGraph(AgentGraph):
    """Agent template graph implementation extending AgentGraph."""

    def __init__(
        self,
        *,
        base_config: Optional[BaseConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize AgentTemplateGraph.

        Args:
            base_config: Optional BaseConfiguration instance.
            checkpointer: Optional Checkpointer instance.
            store: Optional BaseStore instance.
        """
        # Create config with any custom fields needed
        config = (
            Configuration(**base_config.__dict__) if base_config else Configuration()
        )

        # Set specific configurations for this agent
        config.name = "Agent Template"
        config.memory.use_memory = True
        config.system_prompt = SYSTEM_PROMPT

        super().__init__(config, checkpointer, store)

    def _create_call_model(
        self, llm: Runnable[LanguageModelInput, BaseMessage]
    ) -> Callable[..., Coroutine[Any, Any, Dict]]:
        """Create a function that calls the model.

        This example shows how to override the parent method while still using
        its implementation. Agents can customize this method to create specialized
        model calling behavior.

        Args:
            llm: A runnable language model

        Returns:
            A coroutine function that processes the state and invokes the model
        """
        # Simply call the parent implementation
        return super()._create_call_model(llm)

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        # Create the graph
        builder = StateGraph(State)

        # Initialize the LLM here instead of in __init__
        llm = init_chat_model(self._base_config.model)

        # Get all tools
        all_tools = []
        if self._memory:
            all_tools += self._memory.get_tools()

        # Bind tools to the LLM if there are any
        if all_tools:
            llm = llm.bind_tools(all_tools)

        # Add nodes to the graph
        builder.add_node("call_model", self._create_call_model(llm))

        if all_tools:
            tool_node = ToolNode(all_tools, name="tools")
            builder.add_node("tools", tool_node)

            # Define the flow
            builder.add_edge("__start__", "call_model")
            builder.add_conditional_edges("call_model", tools_condition)
            builder.add_edge("tools", "call_model")
        else:
            builder.add_edge("__start__", "call_model")
            builder.add_edge("call_model", END)

        return builder


# For langsmith and backwards compatibility
graph = AgentTemplateGraph().compiled_graph


__all__ = ["AgentTemplateGraph", "graph"]
