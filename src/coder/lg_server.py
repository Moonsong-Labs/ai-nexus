"""Coder graph for LangGraph Server."""

from coder.graph import coder_change_request_config, coder_new_pr_config
from coder.mocks import MockGithubApi
from coder.tools import get_github_tools

# graph for LangGraph Server
# TODO: maybe we can setup this to use mock/real github api depending on env/config
mock_api = MockGithubApi()
github_tools = get_github_tools(mock_api)

graph_new_pr = coder_new_pr_config().graph_builder(github_tools).compile()
graph_change_request = (
    coder_change_request_config().graph_builder(github_tools).compile()
)

__all__ = ["graph_new_pr", "graph_change_request"]
