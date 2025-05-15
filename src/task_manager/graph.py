"""Graphs that extract memories on a schedule."""

import logging
from datetime import datetime
from typing import Any, Coroutine, Optional

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

from common.graph import AgentGraph
from task_manager import tools
from task_manager.configuration import TASK_MANAGER_MODEL, Configuration
from task_manager.state import State

logger = logging.getLogger(__name__)

TASK_MANAGER_RECURSION_LIMIT = 100


def _create_call_model(
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    """Create an asynchronous function that retrieves recent user memories, formats them into a prompt, and invokes a language model with contextual information.

    The returned coroutine, when called, searches the memory store for recent relevant memories based on the user's latest messages, embeds these memories and the current timestamp into a system prompt, and calls the provided language model with this prompt and the conversation history.

    Args:
        llm_with_tools: A runnable language model instance capable of tool use.

    Returns:
        An asynchronous function that accepts the current state, configuration, and optional memory store, and returns a dictionary containing the model's response message.
    """

    async def call_model(
        state: State, config: RunnableConfig, *, store: BaseStore = None
    ) -> dict:
        """Extract the user's state from the conversation and update the memory."""
        # configurable = configuration.Configuration.from_runnable_config(config)

        user_id = config["configurable"]["user_id"]
        # Retrieve the most recent memories for context
        formatted = ""
        if store is not None:
            memories = await store.asearch(
                ("memories", user_id),
                query=str([m.content for m in state.messages[-3:]]),
                limit=10,
            )

            # Format memories for inclusion in the prompt
            formatted = "\n".join(
                f"[{mem.key}]: {mem.value} (similarity: {mem.score})"
                for mem in memories
            )
            if formatted:
                formatted = f"""
    <memories>
    {formatted}
    </memories>"""

        agent_config: Configuration = config["configurable"]["agent_config"]

        # Prepare the system prompt with user memories and current time
        # This helps the model understand the context and temporal relevance
        sys_prompt = agent_config.task_manager_system_prompt.format(
            user_info=formatted, time=datetime.now().isoformat()
        )

        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = TASK_MANAGER_RECURSION_LIMIT

        # Invoke the language model with the prepared prompt and tools
        msg = await llm_with_tools.ainvoke(
            [SystemMessage(content=sys_prompt), *state.messages],
            config_with_recursion,
        )
        return {"messages": [msg]}

    return call_model


class TaskManagerGraph(AgentGraph):
    """Task manager graph."""

    _config: Configuration

    def __init__(
        self,
        *,
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize a TaskManagerGraph for managing task workflows with optional configuration, checkpointer, and memory store.

        Args:
            agent_config: Optional configuration for the task manager agent.
            checkpointer: Optional checkpoint manager for graph state persistence.
            store: Optional memory store for user data and memories.
        """
        super().__init__(
            name="Task Manager",
            agent_config=agent_config or Configuration(),
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """Construct and returns the state graph for the task manager agent.

        Initializes the language model with file management tools, creates the model and tool nodes, and defines the control flow between them in the graph.
        """
        # Initialize the language model and the tools
        all_tools = [
            tools.read_file,
            tools.create_file,
            tools.list_files,
        ]

        llm = init_chat_model(model=TASK_MANAGER_MODEL).bind_tools(all_tools)
        tool_node = ToolNode(all_tools, name="tools")
        call_model = _create_call_model(llm)

        builder = StateGraph(State, config_schema=Configuration)
        builder.add_node(call_model)
        builder.add_node(tool_node.name, tool_node)

        builder.add_edge(START, call_model.__name__)
        builder.add_conditional_edges(call_model.__name__, tools_condition)
        builder.add_edge(tool_node.name, call_model.__name__)

        return builder


# For langsmith
graph = TaskManagerGraph().compiled_graph

__all__ = [TaskManagerGraph.__name__, "graph"]
