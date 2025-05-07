from coder.graph import graph_builder
from coder.mocks import MockGithubApi
from coder.tools import get_github_tools

# graph for LangGraph Server
# TODO: maybe we can setup this to use mock/real github api depending on env/config
mock_api = MockGithubApi()
github_tools = get_github_tools(mock_api)
graph = graph_builder(github_tools).compile()
graph.name = "Coder"

__all__ = ["graph"]
