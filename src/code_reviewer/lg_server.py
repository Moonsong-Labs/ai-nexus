"""Prepare final graphs for langgraph."""

from code_reviewer.graph import non_github_code_reviewer_config
from common.components.github_mocks import maybe_mock_github
from common.components.github_tools import get_github_tools

github_source = maybe_mock_github()
github_tools = get_github_tools(github_source)

graph_non_github = (
    non_github_code_reviewer_config().graph_builder(github_tools).compile()
)

__all__ = ["graph_non_github"]
