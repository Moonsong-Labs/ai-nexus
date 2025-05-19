"""Graphs that extract memories on a schedule."""

import logging
from datetime import datetime
from typing import Optional, Awaitable, Callable

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from architect import tools
from architect.configuration import Configuration
from architect.state import State
from common.graph import AgentGraph

logger = logging.getLogger(__name__)


def _create_call_model(
    agent_config: Configuration,
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
) -> Callable[[State, RunnableConfig], Awaitable[dict]]:
    """Create an asynchronous function that queries recent user memories and invokes a language model with contextual prompts.

    The returned coroutine retrieves the user's recent memories from the store, formats them for context, constructs a system prompt including these memories and the current timestamp, and asynchronously calls the language model with the prompt and conversation history. Returns a dictionary containing the model's response message.
    """

    async def call_model(
        state: State, config: RunnableConfig, *, store: BaseStore
    ) -> dict:
        """Extract the user's state from the conversation and update the memory."""
        try:
            user_id = config["configurable"]["user_id"]
        except KeyError as exc:
            raise KeyError("`user_id` not found in RunnableConfig.configurable") from exc
        
        # Retrieve the most recent memories for context
        try:
            query_content = str([m.content for m in state.messages[-3:]]) if state.messages else ""
            memories = await store.asearch(
                ("memories", user_id),
                query=query_content,
                limit=10,
            )
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            memories = []

        # Format memories for inclusion in the prompt
        formatted = "\n".join(
            f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories
        )
        if formatted:
            formatted = f"""
        <memories>
        {formatted}
        </memories>"""

        # Prepare the system prompt with user memories and current time
        # This helps the model understand the context and temporal relevance
        sys_prompt = agent_config.architect_system_prompt.format(
            user_info=formatted, time=datetime.now().isoformat()
        )

        # Invoke the language model with the prepared prompt and tools
        msg = await llm_with_tools.ainvoke(
            [SystemMessage(content=sys_prompt), *state.messages],
            config=config,
        )

        return {"messages": [msg]}

    return call_model


class ArchitectGraph(AgentGraph):
    """Architect graph."""

    _agent_config: Configuration

    def __init__(
        self,
        *,
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize ArchitectGraph.

        Args:
            agent_config: Optional Configuration instance.
            checkpointer: Optional Checkpointer instance.
            store: Optional BaseStore instance.
        """
        super().__init__(
            name="Architect",
            agent_config=agent_config or Configuration(),
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        # Initialize the language model and the tools
        all_tools = [
            tools.create_memorize_tool(self._agent_config),
            tools.create_recall_tool(self._agent_config),
            tools.read_file,
            tools.create_file,
            tools.list_files,
        ]

        llm = init_chat_model(self._agent_config.model).bind_tools(all_tools)
        tool_node = ToolNode(all_tools, name="tools")
        call_model = _create_call_model(self._agent_config, llm)

        builder = StateGraph(State, config_schema=Configuration)
        builder.add_node(call_model)
        builder.add_node(tool_node.name, tool_node)

        builder.add_edge(START, call_model.__name__)
        builder.add_conditional_edges(call_model.__name__, tools_condition)
        builder.add_edge(tool_node.name, call_model.__name__)

        return builder


# For langsmith
graph = ArchitectGraph().compiled_graph

__all__ = [ArchitectGraph.__name__, "graph"]
