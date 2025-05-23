"""Graphs that extract memories on a schedule."""

from dataclasses import dataclass
from typing import List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from coder.prompts import CHANGE_REQUEST_SYSTEM_PROMPT, NEW_PR_SYSTEM_PROMPT
from coder.state import State
from common.configuration import AgentConfiguration
from common.graph import AgentGraph

llm = init_chat_model("google_genai:gemini-2.0-flash")


@dataclass
class CoderInstanceConfig:
    """Configuration for a coder instance."""

    name: str
    system_prompt: str
    github_tools: List[str]

    def graph_builder(self, github_toolset: list[Tool]):
        builder = _graph_builder(self.filter_tools(github_toolset), self.system_prompt)
        builder.name = self.name
        return builder

    def filter_tools(self, tools: List[Tool]) -> List[Tool]:
        """Filter tools to only include those specified in github_tools.

        Args:
            tools: List of all available tools

        Returns:
            List of tools that match the names in github_tools

        Raises:
            AssertionError: If the number of filtered tools doesn't match github_tools
        """
        filtered_tools = [tool for tool in tools if tool.name in self.github_tools]
        assert len(filtered_tools) == len(self.github_tools), (
            f"Tool mismatch. Expected {len(self.github_tools)} tools, got {len(filtered_tools)}. "
            f"Expected tools: {self.github_tools}, Got tools: {[t.name for t in filtered_tools]}"
        )
        return filtered_tools


def coder_new_pr_config():
    """Instance config for Coder | New PR. Invoked when directed to create a new PR."""
    return CoderInstanceConfig(
        name="Coder | New PR",
        system_prompt=NEW_PR_SYSTEM_PROMPT,
        github_tools=[
            "set_active_branch",
            "create_a_new_branch",
            "get_files_from_a_directory",
            "create_pull_request",
            "create_file",
            "update_file",
            "read_file",
            "delete_file",
            "get_latest_pr_workflow_run",
        ],
    )


def coder_change_request_config():
    """Instance config for Coder | Change Request. Invoked when directed to make a changes to an existing PR."""
    return CoderInstanceConfig(
        name="Coder | Change Request",
        system_prompt=CHANGE_REQUEST_SYSTEM_PROMPT,
        github_tools=[
            "set_active_branch",
            "get_files_from_a_directory",
            "create_file",
            "update_file",
            "read_file",
            "delete_file",
            "get_pull_request",
            "list_pull_requests_files",
            "get_pull_request_head_branch",
            "get_latest_pr_workflow_run",
        ],
    )


class CoderNewPRGraph(AgentGraph):
    """Coder | New PR graph."""

    def __init__(
        self,
        *,
        github_tools: List[Tool],
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize CoderNewPRGraph.

        Args:
            github_tools: Github toolkit to base the agent from
            agent_config: Optional Configuration instance.
            checkpointer: Optional Checkpointer instance.
            store: Optional BaseStore instance.
        """
        super().__init__(
            name="Coder | New PR",
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )
        self._github_tools = github_tools

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        return coder_new_pr_config().graph_builder(self._github_tools)


class CoderChangeRequestGraph(AgentGraph):
    """Coder | Change Request graph."""

    def __init__(
        self,
        *,
        github_tools: List[Tool],
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize CoderChangeRequestGraph.

        Args:
            github_tools: Github toolkit to base the agent from
            agent_config: Optional Configuration instance.
            checkpointer: Optional Checkpointer instance.
            store: Optional BaseStore instance.
        """
        super().__init__(
            name="Coder | Change Request",
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )
        self._github_tools = github_tools

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        return coder_change_request_config().graph_builder(self._github_tools)


class CallModel:
    def __init__(self, github_tools: list[Tool], system_prompt: str):
        self.github_tools = github_tools
        self.system_prompt = system_prompt

    async def __call__(self, state: State) -> dict:
        system_msg = SystemMessage(content=self.system_prompt)
        messages = [system_msg] + state.messages
        messages_after_invoke = await llm.bind_tools(self.github_tools).ainvoke(
            messages
        )
        return {"messages": messages_after_invoke}


def _graph_builder(github_toolset: list[Tool], system_prompt: str):
    """Return coder graph builder."""
    builder = StateGraph(State)

    tool_node = ToolNode(tools=github_toolset)

    builder.add_node("call_model", CallModel(github_toolset, system_prompt))
    builder.add_node("tools", tool_node)

    builder.add_edge("__start__", "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder


__all__ = [CoderNewPRGraph.__name__, CoderChangeRequestGraph.__name__]
