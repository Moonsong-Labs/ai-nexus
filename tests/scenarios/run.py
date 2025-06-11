"""Run all scenarios."""

import os
import sys
from typing import List

import fibonacci.run as fibonacci
import stack.run as stack
from github import GithubException, Repository

from common.logging import get_logger
from common.utils import github as github_utils
from scenarios import BASE_BRANCHES

logger = get_logger(__name__)


def create_branches(repo: Repository, branches: List[str]):
    """Create base branches if they don't exist."""
    logger.info(f"Repository: {repo.full_name}")
    logger.info(f"Default branch: {repo.default_branch}")

    for branch in branches:
        try:
            repo.get_branch(branch)
            logger.info(f"Branch '{branch}' already exists")
        except Exception:
            try:
                default_branch = repo.default_branch
                source = repo.get_branch(default_branch)
                ref = f"refs/heads/{branch}"
                repo.create_git_ref(ref, source.commit.sha)
                logger.info(f"Created branch '{branch}' from '{default_branch}'")
            except Exception as e:
                raise Exception(f"Failed to create branch '{branch}': {str(e)}")


def cleanup_branches(repo: Repository, base_branches: List[str]) -> None:
    """Delete branches that are not in base_branches."""
    logger.info(f"Repository: {repo.full_name}")
    logger.info(f"Default branch: {repo.default_branch}")

    # Get all branches
    all_branches = [branch.name for branch in repo.get_branches()]
    print(f"Current branches: {all_branches}")

    # Delete branches not in base_branches
    for branch in all_branches:
        if branch not in base_branches and branch != repo.default_branch:
            try:
                ref = f"heads/{branch}"
                git_ref = repo.get_git_ref(ref)
                git_ref.delete()
                logger.info(f"Deleted branch: {branch}")
            except GithubException as e:
                logger.error(f"Failed to delete branch '{branch}': {str(e)}")


def init_github():
    client = github_utils.app_get_client_from_credentials()
    repo_name = os.getenv("GITHUB_REPOSITORY")

    try:
        repo = client.get_repo(repo_name)
    except Exception as e:
        logger.error(f"Error accessing repository: {str(e)}")
        sys.exit(1)

    return repo


if __name__ == "__main__":
    repo = init_github()

    create_branches(repo, BASE_BRANCHES)

    stack.run(True)
    fibonacci.run(True)

    cleanup_branches(repo, BASE_BRANCHES)
