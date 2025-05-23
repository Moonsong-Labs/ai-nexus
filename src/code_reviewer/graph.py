"""Graph definition for the Code Reviewer agent."""

import logging
from dataclasses import dataclass
from typing import List

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

from code_reviewer.prompts import PR_REVIEW_PROMPT, SYSTEM_PROMPT
from code_reviewer.state import State


class DiffHunkFeedback(BaseModel):
    """Feedback specific to a code modification."""

    change_required: bool = Field(
        description="Whether or not the feedback necessitates a change"
    )
    file: str = Field(description="Filepath of the diff that this feedback relates to")
    offset: int = Field(
        description="Offset (line number) in the file that this feedback relates to"
    )
    comment: str = Field(description="Comments about the diff hunk")


class DiffFeedback(BaseModel):
    """Feedback for an overall diff."""

    requests_changes: bool = Field(
        description="Whether or not any changes are requested for the diff"
    )
    overall_comment: str = Field(description="Comments about the overall diff")
    feedback: List[DiffHunkFeedback] = Field(
        description="Individual feedback for subsections of this diff"
    )


logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model("google_genai:gemini-2.0-flash")


@dataclass
class CodeReviewerInstanceConfig:
    """Configuration for a code_reviewer instance."""

    name: str
    system_prompt: str
    github_tools: List[str]

    def graph_builder(self, github_toolset: list[Tool]):
        builder = graph_builder(self.filter_tools(github_toolset), self.system_prompt)
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
        if len(filtered_tools) != len(self.github_tools):
            raise ValueError(
                f"Tool mismatch. Expected {len(self.github_tools)} tools, got {len(filtered_tools)}. "
                f"Expected tools: {self.github_tools}, Got tools: {[t.name for t in filtered_tools]}"
            )
        return filtered_tools


def non_github_code_reviewer_config():
    """Instance config for code reviewer without GitHub tools."""
    return CodeReviewerInstanceConfig(
        name="NonGithubCodeReviewer", system_prompt=SYSTEM_PROMPT, github_tools=[]
    )


def github_code_reviewer_config():
    """Instance config for code reviewer with GitHub tools."""
    return CodeReviewerInstanceConfig(
        name="GithubCodeReviewer",
        system_prompt=PR_REVIEW_PROMPT,
        github_tools=[
            "get_files_from_a_directory",
            "read_file",
            "get_pull_request",
            "get_pull_request_diff",
            "create_pull_request_review",
        ],
    )


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


def graph_builder(github_toolset: list[Tool], system_prompt: str) -> StateGraph:
    """Return code_reviewer graph builder."""
    builder = StateGraph(State)

    tool_node = ToolNode(tools=github_toolset)

    builder.add_node("call_model", CallModel(github_toolset, system_prompt))
    builder.add_node("tools", tool_node)

    builder.add_edge("__start__", "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder


__all__ = [
    "non_github_code_reviewer_config",
    "github_code_reviewer_config",
]
