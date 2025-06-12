"""Graphs that extract memories on a schedule."""

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

import common.tools
from common import utils
from common.chain import prechain, skip_on_summary_and_tool_errors
from common.graph import AgentGraph
from common.logging import get_logger
from task_manager.configuration import TASK_MANAGER_MODEL, Configuration
from task_manager.state import State

logger = get_logger(__name__)

TASK_MANAGER_RECURSION_LIMIT = 100


def _create_call_model(
    agent_config: Configuration,
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    """Create an asynchronous function that retrieves recent user memories, formats them into a prompt, and invokes a language model with contextual information.

    The returned coroutine, when called, searches the memory store for recent relevant memories based on the user's latest messages, embeds these memories and the current timestamp into a system prompt, and calls the provided language model with this prompt and the conversation history.

    Args:
        llm_with_tools: A runnable language model instance capable of tool use.

    Returns:
        An asynchronous function that accepts the current state, configuration, and optional memory store, and returns a dictionary containing the model's response message.
    """

    @prechain(skip_on_summary_and_tool_errors())
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

        project_name = "unnamed_project"
        project_path = "projects/"

        # Use hardcoded values when running with stubs
        if agent_config.use_stub:
            project_name = "simplestack"
            project_path = "projects/simplestack"

        if state.project:
            if isinstance(state.project, dict):
                # If it's a dictionary, extract name and path directly
                project_name = state.project.get("name", project_name)
                project_path = state.project.get("path", project_path)
            else:
                # Otherwise assume it's a Project object
                project_name = state.project.name
                project_path = state.project.path

        # This helps the model understand the context and temporal relevance
        sys_prompt = agent_config.task_manager_system_prompt.format(
            user_info=formatted,
            time=datetime.now().isoformat(),
            project_name=project_name,
            project_path=project_path,
            project_context="",
        )

        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = TASK_MANAGER_RECURSION_LIMIT

        # Invoke the language model with the prepared prompt and tools
        msg = await llm_with_tools.ainvoke(
            [SystemMessage(content=sys_prompt), *state.messages],
            config_with_recursion,
        )

        print(utils.format_message(msg, actor="TASK MANAGER"))  # noqa: T201

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
            common.tools.create_directory,
            common.tools.create_file,
            common.tools.list_files,
            common.tools.read_file,
            common.tools.create_summarize_tool(self._name),
        ]

        llm = init_chat_model(model=TASK_MANAGER_MODEL).bind_tools(all_tools)
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
graph = TaskManagerGraph().compiled_graph

__all__ = [TaskManagerGraph.__name__, "graph"]
