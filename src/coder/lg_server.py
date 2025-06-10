"""Coder graph for LangGraph Server."""


from coder.graph import CoderChangeRequestGraph, CoderNewPRGraph
from common.components.github_mocks import maybe_mock_github
from common.components.github_tools import get_github_tools
from common.logging import get_logger

logger = get_logger(__name__)

# Use the function to get the appropriate GitHub source
github_source = maybe_mock_github()
github_tools = get_github_tools(github_source)

graph_new_pr = CoderNewPRGraph(github_tools=github_tools).compiled_graph
graph_change_request = CoderChangeRequestGraph(github_tools=github_tools).compiled_graph

__all__ = ["graph_new_pr", "graph_change_request"]
