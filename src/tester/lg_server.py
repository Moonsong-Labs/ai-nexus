"""Tester graph for LangGraph Server."""

from common.components.github_mocks import maybe_mock_github
from common.components.github_tools import get_github_tools
from tester.graph import TesterAgentGraph

github_source = maybe_mock_github()
github_tools = get_github_tools(github_source)

graph = TesterAgentGraph(github_tools=github_tools).compiled_graph

__all__ = ["graph"]
