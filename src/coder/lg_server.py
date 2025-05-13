"""Coder graph for LangGraph Server."""

import logging
import os
from typing import Union

from langchain_community.utilities.github import GitHubAPIWrapper

from coder.graph import coder_change_request_config, coder_new_pr_config
from coder.mocks import MockGithubApi
from common.components.github_tools import get_github_tools

logger = logging.getLogger(__name__)


def get_github_source() -> Union[GitHubAPIWrapper, MockGithubApi]:
    """Get either a real GitHub API wrapper or a mock based on environment variables.

    Required environment variables for real GitHub API:
    - GITHUB_APP_ID
    - GITHUB_APP_PRIVATE_KEY
    - GITHUB_REPOSITORY
    """
    required_vars = ["GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", "GITHUB_REPOSITORY"]

    if all(os.getenv(var) for var in required_vars):
        logger.debug("Using live GitHub API toolkit")
        return GitHubAPIWrapper(
            github_app_id=os.getenv("GITHUB_APP_ID"),
            github_app_private_key=os.getenv("GITHUB_APP_PRIVATE_KEY"),
            github_repository=os.getenv("GITHUB_REPOSITORY"),
        )

    if any(os.getenv(var) for var in required_vars):
        logger.warning(
            "Some but not all required GitHub environment variables are set. Falling back mock GitHub toolset."
        )

    logger.debug("Using mock GitHub API toolkit")

    return MockGithubApi()


# Use the function to get the appropriate GitHub source
github_source = get_github_source()
github_tools = get_github_tools(github_source)

graph_new_pr = coder_new_pr_config().graph_builder(github_tools).compile()
graph_change_request = (
    coder_change_request_config().graph_builder(github_tools).compile()
)

__all__ = ["graph_new_pr", "graph_change_request"]
