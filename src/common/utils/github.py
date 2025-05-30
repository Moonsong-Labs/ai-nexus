"""Utility functions for interacting with GitHub."""

import os
import sys

from github import Auth, Github, GithubIntegration

from common.logging import get_logger

logger = get_logger(__name__)


def app_get_integration() -> GithubIntegration:
    """Get the installation of the github app given the proper environment variables."""
    github_repo_name = os.getenv("GITHUB_REPOSITORY")
    github_app_id = os.getenv("GITHUB_APP_ID")
    github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")

    if not github_app_id or not github_app_private_key or not github_repo_name:
        logger.error(
            "Error: GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY and GITHUB_REPOSITORY environment variables must be set"
        )
        sys.exit(1)

    try:
        # interpret the key as a file path
        # fallback to interpreting as the key itself
        with open(github_app_private_key) as f:
            github_app_private_key = f.read()
    except FileNotFoundError:
        # Treat as direct key content
        pass
    except Exception as e:
        logger.error(f"Error reading private key file: {str(e)}", file=sys.stderr)
        sys.exit(0)

    auth = Auth.AppAuth(
        github_app_id,
        github_app_private_key,
    )

    return GithubIntegration(auth=auth)


def app_get_installation(integration: GithubIntegration):
    """Get installation given a github integration with an authenticated app."""
    installations = list(integration.get_installations())
    if not installations:
        raise ValueError(
            "Installation not found. Please make sure to install the created github app on the given repository."
        )
    try:
        # Get first installation
        # TODO: Check if we have to handle multiple installations
        installation = installations[0]
        return installation
    except IndexError as e:
        raise ValueError(
            f"Please make sure to give correct github parameters Error message: {e}"
        )


def app_get_client_from_credentials() -> Github:
    """Get an authenticated github client provided corresponding app credentials are provided as environment variables."""
    logger.debug("Getting github client")
    integration = app_get_integration()
    installation = app_get_installation(integration)
    client = installation.get_github_for_installation()
    return client
