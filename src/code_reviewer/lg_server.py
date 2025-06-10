"""Prepare final graphs for langgraph."""

from code_reviewer.graph import (
    github_code_reviewer_config,
    local_code_reviewer_config,
    non_github_code_reviewer_config,
)
from common.components.github_mocks import maybe_mock_github
from common.components.github_tools import get_github_tools
from common.configuration import AgentConfiguration

github_source = maybe_mock_github()
github_tools = get_github_tools(github_source)

# Use default model configuration
default_model = AgentConfiguration().model

graph_with_github_tools = (
    github_code_reviewer_config().graph_builder(github_tools, default_model).compile()
)
graph_no_github_tools = (
    non_github_code_reviewer_config().graph_builder(github_tools, default_model).compile()
)
graph_local = local_code_reviewer_config().graph_builder(github_tools, default_model).compile()

__all__ = [
    "graph_with_github_tools",
    "graph_no_github_tools",
    "graph_local",
]
