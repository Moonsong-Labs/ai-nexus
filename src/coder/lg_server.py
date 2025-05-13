"""Coder graph for LangGraph Server."""

import logging

from coder.graph import coder_change_request_config, coder_new_pr_config
from common.components.github_mocks import maybe_mock_github
from common.components.github_tools import get_github_tools

logger = logging.getLogger(__name__)



# Use the function to get the appropriate GitHub source
github_source = maybe_mock_github()
github_tools = get_github_tools(github_source)

graph_new_pr = coder_new_pr_config().graph_builder(github_tools).compile()
graph_change_request = (
    coder_change_request_config().graph_builder(github_tools).compile()
)

__all__ = ["graph_new_pr", "graph_change_request"]
