import os
import sys
from typing import List

import dotenv
from github import Auth, GithubIntegration, Repository

from common.logging import get_logger
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
    github_repo_name = os.getenv("GITHUB_REPOSITORY")
    if not github_repo_name:
        print(
            "Error: GITHUB_REPOSITORY environment variable must be set", file=sys.stderr
        )
        sys.exit(1)

    github_app_id = os.getenv("GITHUB_APP_ID")
    github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")

    try:
        # interpret the key as a file path
        # fallback to interpreting as the key itself
        with open(github_app_private_key, "r") as f:
            github_app_private_key = f.read()

    except Exception:
        pass

    auth = Auth.AppAuth(
        github_app_id,
        github_app_private_key,
    )

    gi = GithubIntegration(auth=auth)
    installation = gi.get_installations()
    if not installation:
        raise ValueError(
            f"Please make sure to install the created github app with id "
            f"{github_app_id} on the repo: {github_repo_name}"
            "More instructions can be found at "
            "https://docs.github.com/en/apps/using-"
            "github-apps/installing-your-own-github-app"
        )
    try:
        installation = installation[0]
    except IndexError as e:
        raise ValueError(
            f"Please make sure to give correct github parameters Error message: {e}"
        )

    github_client = installation.get_github_for_installation()

    try:
        repo = github_client.get_repo(github_repo_name)
    except Exception as e:
        logger.error(f"Error accessing repository: {str(e)}")
        sys.exit(1)

    create_base_branches(repo, BASE_BRANCHES)


if __name__ == "__main__":
    main()
