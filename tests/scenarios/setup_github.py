import os
import sys
from typing import List

import dotenv
from github import Repository

from common.logging import get_logger
from common.utils import github as github_utils
from scenarios import BASE_BRANCHES

dotenv.load_dotenv()


logger = get_logger(__name__)


def create_base_branches(repo: Repository, base_branches: List[str]) -> None:
    """Create base branches if they don't exist."""
    logger.info(f"Repository: {repo.full_name}")
    logger.info(f"Default branch: {repo.default_branch}")

    for branch in base_branches:
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
                logger.error(f"Failed to create branch '{branch}': {str(e)}")
                sys.exit(1)


def main():
    print("Getting github client")
    github_client = github_utils.app_get_client_from_credentials()
    github_repo_name = os.getenv("GITHUB_REPOSITORY")
    try:
        repo = github_client.get_repo(github_repo_name)
    except Exception as e:
        logger.error(f"Error accessing repository: {str(e)}")
        sys.exit(1)

    create_base_branches(repo, BASE_BRANCHES)


if __name__ == "__main__":
    main()
