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

import pr_memory_updater.prompts as prompts
import pr_memory_updater.tools as AgentTools
from common.components.memory import MemoryConfiguration
from common.graph import AgentGraph
from pr_memory_updater.configuration import Configuration
from pr_memory_updater.state import State

logger = logging.getLogger(__name__)


def _create_call_model(
    agent_config: Configuration,
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Callable[..., Coroutine[Any, Any, Dict]]:
    """
    Creates an asynchronous callable that invokes a language model with a system prompt and conversation history.
    
    The returned coroutine accepts the current state and configuration, retrieves the system prompt from the agent configuration (falling back to a default if unset), constructs a system message, and calls the language model with the system and conversation messages. The model's response is returned as a dictionary under the "messages" key.
    """

    async def call_model(
        state: Any, config: RunnableConfig, *, store: BaseStore = None
    ) -> Dict:
        """
        Invokes the language model asynchronously using the system prompt and conversation history.
        
        Args:
            state: The current conversation state, which must include a 'messages' attribute.
            config: Configuration for the language model invocation.
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
        """
        Initializes a PRMemoryUpdaterGraph with optional configuration, checkpointer, and store.
        
        If no agent configuration is provided, uses a default model, disables memory, and sets a predefined system prompt.
        """
        # Create config with any custom fields needed
        agent_config = agent_config or Configuration(
            model = "google_genai:gemini-2.5-flash-preview-05-20",
            memory=MemoryConfiguration(use_memory=False), system_prompt=prompts.NEW_SYSTEM_PROMPT
        )

        super().__init__(
            name="PR Memory Updater",
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """
        Builds and configures a StateGraph representing the agent's execution flow.
        
        The graph integrates the language model and, if enabled, relevant tools for PR memory updating. Nodes and edges are added to support model calls and conditional tool usage based on the agent's configuration.
        
        Returns:
            A StateGraph instance defining the agent's operational flow.
        """
        # Create the graph
        builder = StateGraph(State)

        # Get all tools
        all_tools = []
        if self._memory:
            all_tools += self._memory.get_tools()

        all_tools.append(AgentTools.invoke_pr_details)
        all_tools.append(AgentTools.fetch_project_global_memory)
        all_tools.append(AgentTools.store_project_global_memory)

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
