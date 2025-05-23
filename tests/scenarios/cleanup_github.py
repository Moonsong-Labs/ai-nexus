#!/usr/bin/env python3

import os
import sys
from typing import List

import dotenv
from github import Auth, GithubIntegration, Repository

from scenarios import BASE_BRANCHES

dotenv.load_dotenv()


def cleanup_branches(repo: Repository, base_branches: List[str]) -> None:
    """Delete branches that are not in base_branches."""
    print(f"Repository: {repo.full_name}")
    print(f"Default branch: {repo.default_branch}")

    # Get all branches
    all_branches = [branch.name for branch in repo.get_branches()]
    print(f"Current branches: {all_branches}")

    # Delete branches not in base_branches
    for branch in all_branches:
        if branch not in base_branches and branch != repo.default_branch:
            try:
                ref = f"heads/{branch}"
                print(f"Deleting branch: {branch}")
                git_ref = repo.get_git_ref(ref)
                print("got ref")
                print(f"Git ref: {git_ref}")
                git_ref.delete()
            except Exception as e:
                print(f"Failed to delete branch '{branch}': {str(e)}", file=sys.stderr)


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
    except ValueError as e:
        raise ValueError(
            f"Please make sure to give correct github parameters Error message: {e}"
        )

    github_client = installation.get_github_for_installation()

    try:
        repo = github_client.get_repo(github_repo_name)
    except Exception as e:
        print(f"Error accessing repository: {str(e)}", file=sys.stderr)
        sys.exit(1)

    cleanup_branches(repo, BASE_BRANCHES)


if __name__ == "__main__":
    main()
