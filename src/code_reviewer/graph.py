"""Graph definition for the Code Reviewer agent."""

from dataclasses import dataclass
from typing import List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

import common.tools
from code_reviewer.prompts import LOCAL_REVIEW_PROMPT, PR_REVIEW_PROMPT, SYSTEM_PROMPT
from code_reviewer.state import State
from common.configuration import AgentConfiguration
from common.graph import AgentGraph
from common.logging import get_logger

logger = get_logger(__name__)

# Model will be initialized with configuration in CallModel


@dataclass
class CodeReviewerInstanceConfig:
    """Configuration for a code_reviewer instance."""

    name: str
    system_prompt: str
    github_tools_filter: List[str]
    other_tools: List[Tool]

    def graph_builder(self, github_toolset: list[Tool], model: str):
        tools = self.other_tools + self.filter_github_tools(github_toolset)
        builder = _graph_builder(tools, self.system_prompt, model)
        builder.name = self.name
        return builder

    def filter_github_tools(self, tools: List[Tool]) -> List[Tool]:
        """Filter the github tools to only include those specified in github_tools_filter.

        Args:
            tools: List of all available tools
        Returns:
            List of tools that match the names in github_tools
        Raises:
            AssertionError: If the number of filtered tools doesn't match github_tools
        """
        filtered_tools = [
            tool for tool in tools if tool.name in self.github_tools_filter
        ]
        if len(filtered_tools) != len(self.github_tools_filter):
            raise ValueError(
                f"Tool mismatch. Expected {len(self.github_tools_filter)} tools, got {len(filtered_tools)}. "
                f"Expected tools: {self.github_tools_filter}, Got tools: {[t.name for t in filtered_tools]}"
            )
        return filtered_tools


def local_code_reviewer_config():
    """Instance config for code reviewer with tools to use the local environment for code."""
    return CodeReviewerInstanceConfig(
        name="LocalCodeReviewer",
        system_prompt=LOCAL_REVIEW_PROMPT,
        github_tools_filter=[],
        other_tools=[
            common.tools.summarize,
            common.tools.list_files,
            common.tools.read_file,
        ],
    )


def non_github_code_reviewer_config():
    """Instance config for code reviewer without GitHub tools."""
    return CodeReviewerInstanceConfig(
        name="NonGithubCodeReviewer",
        system_prompt=SYSTEM_PROMPT,
        github_tools_filter=[],
        other_tools=[],
    )


def github_code_reviewer_config():
    """Instance config for code reviewer with GitHub tools."""
    return CodeReviewerInstanceConfig(
        name="GithubCodeReviewer",
        system_prompt=PR_REVIEW_PROMPT,
        github_tools_filter=[
            "get_files_from_a_directory",
            "read_file",
            "get_pull_request",
            "get_pull_request_diff",
            "create_pull_request_review",
        ],
        other_tools=[],
    )


class CodeReviewerGraph(AgentGraph):
    """CodeReviewer non-Github graph."""

    def __init__(
        self,
        *,
        github_tools: List[Tool],
        config: CodeReviewerInstanceConfig,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize the CodeReviewerGraph.

        Args:
            github_tools: List of GitHub tools to be used in the graph.
            agent_config: Optional configuration for the code reviewer agent. If not provided, a default configuration is used.
            checkpointer: Optional checkpointer for managing workflow state persistence.
            store: Optional storage backend for conversation or workflow data.
        """
        super().__init__(
            name="CodeReviewer",
            agent_config=agent_config or AgentConfiguration(),
            checkpointer=checkpointer,
            store=store,
        )
        self._github_tools = github_tools
        self._config = config

    def create_builder(self) -> StateGraph:
        """Create a graph builder with the configured model."""
        model = (
            self._agent_config.model
            if self._agent_config
            else "google_genai:gemini-2.0-flash"
        )
        return self._config.graph_builder(self._github_tools, model)


class CallModel:
    def __init__(self, github_tools: list[Tool], system_prompt: str, model: str):
        self.github_tools = github_tools
        self.system_prompt = system_prompt
        self.model = model

    async def __call__(self, state: State) -> dict:
        llm = init_chat_model(self.model)
        project_path = state.project.path if state.project else "Unknown"

        system_prompt = self.system_prompt.format(
            project_path=project_path,
        )

        system_msg = SystemMessage(system_prompt)
        messages = [system_msg] + state.messages
        messages_after_invoke = await llm.bind_tools(self.github_tools).ainvoke(
            messages
        )
        return {"messages": messages_after_invoke, "project": state.project}


def _graph_builder(github_toolset: list[Tool], system_prompt: str, model: str):
    """Return code_reviewer graph builder."""
    builder = StateGraph(State)

    tool_node = ToolNode(tools=github_toolset)

    builder.add_node("call_model", CallModel(github_toolset, system_prompt, model))
    builder.add_node("tools", tool_node)

    builder.add_edge("__start__", "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder


__all__ = [
    "non_github_code_reviewer_config",
    "github_code_reviewer_config",
    "local_code_reviewer_config",
    "CodeReviewerGraph",
]
