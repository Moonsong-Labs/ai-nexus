"""Enrichment for a pre-defined schema."""

from code_reviewer.graph import graph_builder
from coder.mocks import MockGithubApi
from common.components.github_tools import get_github_tools

mock_api = MockGithubApi()
github_tools = get_github_tools(mock_api)
graph = graph_builder(github_tools).compile()
graph.name = "CodeReviewer"

__all__ = ["graph"]
