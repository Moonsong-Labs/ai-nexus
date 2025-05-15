"""Graph implementation for agent template using AgentGraph."""

import logging
from typing import Any, Callable, Coroutine, Dict, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from agent_template.configuration import Configuration
from agent_template.prompts import SYSTEM_PROMPT
from agent_template.state import State
from common.components.memory import MemoryConfiguration
from common.graph import AgentGraph

logger = logging.getLogger(__name__)


def _create_call_model(
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Callable[..., Coroutine[Any, Any, Dict]]:
    """Create a function that calls the model.

    This is a basic implementation that derived classes can override.

    Args:
        llm: A runnable language model

    Returns:
        A coroutine function that processes the state and invokes the model
    """

    async def call_model(
        state: Any, config: RunnableConfig, *, store: BaseStore = None
    ) -> Dict:
        """Call the model with the current state."""
        # Get system prompt from config
        # After _merge_config, "agent_config" should always be a key in configurable.
        agent_config: Configuration = config["configurable"]["agent_config"]

        system_prompt = agent_config.system_prompt
        if system_prompt is None:
            logger.info(
                "system_prompt was None in the configuration. Using default prompt."
            )
            system_prompt = "You are a helpful AI assistant."

        system = SystemMessage(content=system_prompt)
        msg = await llm.ainvoke([system, *state.messages])
        return {"messages": [msg]}

    return call_model


class AgentTemplateGraph(AgentGraph):
    """Agent template graph implementation extending AgentGraph."""

    _agent_config: Configuration

    def __init__(
        self,
        *,
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize AgentTemplateGraph.

        Args:
            base_config: Optional AgentConfiguration instance.
            checkpointer: Optional Checkpointer instance.
            store: Optional BaseStore instance.
        """
        # Create config with any custom fields needed
        agent_config = agent_config or Configuration(
            memory=MemoryConfiguration(use_memory=True), system_prompt=SYSTEM_PROMPT
        )

        super().__init__(
            name="Agent Template",
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        # Create the graph
        builder = StateGraph(State)

        # Get all tools
        all_tools = []
        if self._memory:
            all_tools += self._memory.get_tools()

        # Init model
        llm = init_chat_model(self._agent_config.model)

        # Bind tools to the LLM if there are any
        if all_tools:
            llm = llm.bind_tools(all_tools)

        # Add nodes to the graph
        call_model = _create_call_model(llm)

        builder.add_node(call_model)

        if all_tools:
            tool_node = ToolNode(all_tools, name="tools")
            builder.add_node(tool_node)

            # Define the flow
            builder.add_edge(START, call_model.__name__)
            builder.add_conditional_edges(call_model.__name__, tools_condition)
            builder.add_edge(tool_node.name, call_model.__name__)
        else:
            builder.add_edge(START, call_model.__name__)
            builder.add_edge(call_model.__name__, END)

        return builder


# For langsmith and backwards compatibility
graph = AgentTemplateGraph().compiled_graph


__all__ = ["AgentTemplateGraph", "graph"]
