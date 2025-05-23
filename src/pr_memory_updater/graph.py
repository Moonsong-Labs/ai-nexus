"""Graph implementation for PR Memory Updater agent using AgentGraph."""

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

from pr_memory_updater.configuration import Configuration
from pr_memory_updater.prompts import SYSTEM_PROMPT
from pr_memory_updater.state import State
from common.components.memory import MemoryConfiguration
from common.graph import AgentGraph

logger = logging.getLogger(__name__)


def _create_call_model(
    agent_config: Configuration,
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Callable[..., Coroutine[Any, Any, Dict]]:
    """Create an asynchronous function that invokes a language model with a system prompt and conversation history.

    The returned coroutine takes the current state and configuration, retrieves the system prompt from the agent configuration (using a default if none is set), constructs a system message, and calls the language model with the system message and the state's messages. The model's response is returned as a dictionary containing the new message.
    """

    async def call_model(
        state: Any, config: RunnableConfig, *, store: BaseStore = None
    ) -> Dict:
        """Invoke the language model with the current conversation state and system prompt.

        Args:
            state: The current conversation state, expected to have a 'messages' attribute.
            config: Runnable configuration containing the agent's configuration.
            store: Optional storage backend.

        Returns:
            A dictionary containing the model's response message under the 'messages' key.
        """
        # Get system prompt from config
        system_prompt = agent_config.system_prompt
        if system_prompt is None:
            logger.info(
                "system_prompt was None in the configuration. Using default prompt."
            )
            system_prompt = "You are a helpful AI assistant."

        system = SystemMessage(content=system_prompt)
        msg = await llm.ainvoke([system, *state.messages], config)
        return {"messages": [msg]}

    return call_model


class PRMemoryUpdaterGraph(AgentGraph):
    """PR Memory updater graph implementation extending AgentGraph."""

    _agent_config: Configuration

    def __init__(
        self,
        *,
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize a PRMemoryUpdaterGraph with the specified configuration, checkpointer, and store.

        If no agent configuration is provided, a default configuration with memory enabled and a predefined system prompt is used.
        """
        # Create config with any custom fields needed
        agent_config = agent_config or Configuration(
            memory=MemoryConfiguration(use_memory=True), system_prompt=SYSTEM_PROMPT
        )

        super().__init__(
            name="PR Memory Updater",
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """Construct and configures a StateGraph for the agent, integrating the language model and optional tools.

        Returns:
            A StateGraph instance representing the agent's execution flow, with nodes and edges set up for model calls and tool usage as appropriate.
        """
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
        call_model = _create_call_model(self._agent_config, llm)

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
graph = PRMemoryUpdaterGraph().compiled_graph


__all__ = ["PRMemoryUpdaterGraph", "graph"]
