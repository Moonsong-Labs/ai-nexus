import os
import sys
from typing import List

import dotenv
from github import Auth, GithubException, GithubIntegration, Repository

from common.logging import get_logger
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
    github_repo_name = os.getenv("GITHUB_REPOSITORY")
    if not github_repo_name:
        print(
            "Error: GITHUB_REPOSITORY environment variable must be set", file=sys.stderr
        )
        sys.exit(1)

    github_app_id = os.getenv("GITHUB_APP_ID")
    github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")

    if not github_app_id or not github_app_private_key:
        print(
            "Error: GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY environment variables must be set",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        # interpret the key as a file path
        # fallback to interpreting as the key itself
        with open(github_app_private_key, "r") as f:
            github_app_private_key = f.read()
    except FileNotFoundError:
        # Treat as direct key content
        pass
    except Exception as e:
        print(f"Error reading private key file: {str(e)}", file=sys.stderr)
        sys.exit(1)

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
    except ValueError as e:
        raise ValueError(
            f"Please make sure to give correct github parameters Error message: {e}"
        )

    github_client = installation.get_github_for_installation()

    try:
        repo = github_client.get_repo(github_repo_name)
    except Exception as e:
        logger.error(f"Error accessing repository: {str(e)}")
        sys.exit(1)

    cleanup_branches(repo, BASE_BRANCHES)


if __name__ == "__main__":
    main()
