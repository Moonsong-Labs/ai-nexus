import os
import sys
from typing import List

import dotenv
from github import GithubException, Repository

from common.logging import get_logger
from common.utils import github as github_utils
from scenarios import BASE_BRANCHES

dotenv.load_dotenv()


logger = get_logger(__name__)


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


def main():
    github_client = github_utils.get_client_from_app_credentials()
    github_repo_name = os.getenv("GITHUB_REPOSITORY")
    try:
        repo = github_client.get_repo(github_repo_name)
    except Exception as e:
        logger.error(f"Error accessing repository: {str(e)}")
        sys.exit(1)

    cleanup_branches(repo, BASE_BRANCHES)


if __name__ == "__main__":
    main()
