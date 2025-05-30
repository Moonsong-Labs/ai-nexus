"""Test Agent Graph Implementation."""

import logging
from datetime import datetime
from typing import Any, Coroutine, List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import Tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.chain import prechain, skip_on_summary_and_tool_errors
from common.graph import AgentGraph
from common.tools.list_files import list_files
from common.tools.read_file import read_file
from common.tools.summarize import summarize
from tester.configuration import Configuration
from tester.state import State

logger = logging.getLogger(__name__)


def get_tester_github_tools():
    """Get the list of GitHub tools needed for the test agent."""
    return [
        "set_active_branch",
        "create_a_new_branch",
        "get_files_from_a_directory",
        "create_pull_request",
        "create_file",
        "update_file",
        "read_file",
        "delete_file",
        "get_latest_pr_workflow_run",
    ]


def filter_github_tools(
    all_tools: List[Tool], required_tool_names: List[str]
) -> List[Tool]:
    """Filter GitHub tools to only include those needed for testing.

    Args:
        all_tools: List of all available GitHub tools
        required_tool_names: List of tool names needed for testing

    Returns:
        List of filtered GitHub tools

    Raises:
        AssertionError: If not all required tools are found
    """
    filtered_tools = [tool for tool in all_tools if tool.name in required_tool_names]
    found_tool_names = [tool.name for tool in filtered_tools]

    missing_tools = set(required_tool_names) - set(found_tool_names)
    if missing_tools:
        logger.warning(f"Missing required GitHub tools: {missing_tools}")
        logger.info(f"Available tools: {[tool.name for tool in all_tools]}")

    return filtered_tools


def _create_call_model(
    agent_config: Configuration,
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    @prechain(skip_on_summary_and_tool_errors())
    async def call_model(
        state: State, config: RunnableConfig, *, store: Optional[BaseStore] = None
    ) -> dict:
        """Process the conversation based on the current workflow stage."""
        try:
            formatted = ""

            # Only try to retrieve memories if store is not None
            if store is not None:
                try:
                    user_id = config["configurable"]["user_id"]
                    # Retrieve the most recent memories for context
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
                except Exception as e:
                    logger.warning(f"Error retrieving memories: {e}")
                    formatted = ""

            # Prepare the system prompt with memories, and current time
            sys_prompt = agent_config.system_prompt.format(
                user_info=formatted,
                project_path=state.project.path,
                time=datetime.now().isoformat(),
            )

            # Invoke the language model with the prepared prompt and tools
            msg = await llm_with_tools.ainvoke(
                [SystemMessage(content=sys_prompt), *state.messages],
                config=config,
            )

            return {"messages": [msg]}
        except Exception as e:
            logger.error(f"Error in call_model: {str(e)}")
            # Return a error message instead of failing completely
            return {
                "messages": [
                    SystemMessage(
                        content=f"There was an error processing your request: {str(e)}. Please try a different approach."
                    )
                ]
            }

    return call_model


def _create_workflow(call_model_name: str, tool_node_name: str):
    async def workflow(state: State, config: RunnableConfig):
        # If the last message has tool calls, route to the tool node
        if (
            state.messages
            and hasattr(state.messages[-1], "tool_calls")
            and state.messages[-1].tool_calls
        ):
            return tool_node_name

        return END

    return workflow


class TesterAgentGraph(AgentGraph):
    """Test agent graph."""

    _config: Configuration
    _github_tools: List[Tool]

    def __init__(
        self,
        *,
        github_tools: List[Tool],
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize TesterAgentGraph.

        Args:
            github_tools: GitHub tools for repository operations.
            agent_config: Optional Configuration instance.
            checkpointer: Optional Checkpointer instance.
            store: Optional BaseStore instance.
        """
        super().__init__(
            name="tester",
            agent_config=agent_config or Configuration(),
            checkpointer=checkpointer,
            store=store,
        )
        self._github_tools = github_tools

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        # Filter GitHub tools to get only what we need for testing
        required_github_tools = get_tester_github_tools()
        filtered_github_tools = filter_github_tools(
            self._github_tools, required_github_tools
        )

        # Initialize the language model and the tools
        all_tools = [*filtered_github_tools, summarize, list_files, read_file]

        # Define node names explicitly to avoid confusion
        call_model_name = "call_model"
        tool_node_name = "tools"

        llm = init_chat_model(self._agent_config.model).bind_tools(all_tools)
        tool_node = ToolNode(all_tools, name=tool_node_name)
        call_model = _create_call_model(self._agent_config, llm)
        workflow = _create_workflow(call_model_name, tool_node_name)

        # Create the graph
        builder = StateGraph(State, config_schema=Configuration)
        builder.add_node(call_model_name, call_model)
        builder.add_node(tool_node_name, tool_node)

        # Define the graph flow
        builder.add_edge(START, call_model_name)
        builder.add_conditional_edges(
            call_model_name,
            workflow,
            [tool_node_name, call_model_name, END],
        )
        builder.add_edge(tool_node_name, call_model_name)

        return builder


__all__ = [TesterAgentGraph.__name__]
