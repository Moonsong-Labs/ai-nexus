"""Mock Github API for testing."""

import os
from typing import Union

from langchain_community.utilities.github import GitHubAPIWrapper

from common.logging import get_logger

logger = get_logger(__name__)


class MockGithubApi:
    """Mock Github API that keeps changes in memory."""

    branches = ["main"]
    active_branch = "main"
    # Mock file system structure: {type: "dir"|"file", content: str|dict}
    files = {"type": "dir", "content": {}}
    # Store the current pull request: {title: str, body: str, head: str, base: str}
    pull_request = None
    # Track file operations: [{type: str, args: dict}]
    operations = []

    def set_active_branch(self, branch_name: str):
        """Set the active branch."""
        if branch_name in self.branches:
            self.active_branch = branch_name
            return f"Switched to branch `{branch_name}`"
        else:
            return (
                f"Error {branch_name} does not exist,"
                f"in repo with current branches: {str(self.branches)}"
            )

    def create_branch(self, proposed_branch_name: str) -> str:
        """Create a new branch, and set it as the active bot branch.

        If the proposed branch already exists, append _v1 then _v2...
        until a unique name is found.
        """
        i = 0
        new_branch_name = proposed_branch_name

        for i in range(1000):
            if new_branch_name not in self.branches:
                self.branches.append(new_branch_name)
                self.active_branch = new_branch_name
                return (
                    f"Branch '{new_branch_name}' "
                    "created successfully, and set as current active branch."
                )
            i += 1
            new_branch_name = f"{proposed_branch_name}_v{i}"

        return (
            "Unable to create branch. "
            "At least 1000 branches exist with named derived from "
            f"proposed_branch_name: `{proposed_branch_name}`"
        )

    def _get_files_recursive(self, current_path: str, node: dict) -> list:
        files = []
        if node["type"] == "file":
            files.append(current_path)
        else:
            for name, child in node["content"].items():
                child_path = f"{current_path}/{name}" if current_path else name
                files.extend(self._get_files_recursive(child_path, child))
        return files

    def get_files_from_directory(self, directory_path: str) -> str:
        """Recursively fetches files from a directory in the repo."""
        path_parts = [p for p in directory_path.split("/") if p]

        # Navigate to the target directory
        current = self.files
        for part in path_parts:
            if current["type"] != "dir" or part not in current["content"]:
                return f"No files found in directory: {directory_path}"
            current = current["content"][part]

        if current["type"] != "dir":
            return f"Error: {directory_path} is not a directory"

        # Get all files under this directory
        files = self._get_files_recursive(directory_path, current)

        if not files:
            return f"No files found in directory: {directory_path}"

        return str(files)

    def create_pull_request(self, pr_query: str) -> str:
        """Create a pull request from the bot's branch to the base branch."""
        if self.active_branch == "main":
            return "Cannot make a pull request because commits are already in the main branch."

        title = pr_query.split("\n")[0]
        body = pr_query[len(title) + 2 :]

        self.pull_request = {
            "title": title,
            "body": body,
            "head": self.active_branch,
            "base": "main",
        }

        return "Successfully created PR number 1"

    def create_file(self, file_query: str) -> str:
        """Create a new file on the Github repo."""
        if self.active_branch == "main":
            return (
                "You're attempting to commit to the directly to the"
                f"{self.active_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        file_path = file_query.split("\n")[0]
        file_contents = file_query[len(file_path) + 2 :]

        self.operations.append(
            {
                "type": "create",
                "args": {
                    "path": file_path,
                    "content": file_contents,
                    "branch": self.active_branch,
                },
            }
        )

        return f"Created file {file_path}"

    def update_file(self, file_query: str) -> str:
        """Update a file with new content."""
        if self.active_branch == "main":
            return (
                "You're attempting to commit to the directly"
                f"to the {self.active_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        file_path = file_query.split("\n")[0]
        old_content = file_query.split("OLD <<<<")[1].split(">>>> OLD")[0].strip()
        new_content = file_query.split("NEW <<<<")[1].split(">>>> NEW")[0].strip()

        self.operations.append(
            {
                "type": "update",
                "args": {
                    "path": file_path,
                    "old_content": old_content,
                    "new_content": new_content,
                    "branch": self.active_branch,
                },
            }
        )

        return f"Updated file {file_path}"

    def delete_file(self, file_path: str) -> str:
        """Delete a file from the repo."""
        if self.active_branch == "main":
            return (
                "You're attempting to commit to the directly"
                f"to the {self.active_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        self.operations.append(
            {
                "type": "delete",
                "args": {"path": file_path, "branch": self.active_branch},
            }
        )

        return f"Deleted file {file_path}"

    def read_file(self, file_path: str) -> str:
        """Read a file from the repo."""
        # Split path into components
        path_parts = [p for p in file_path.split("/") if p]

        # Navigate to the target file
        current = self.files
        for part in path_parts:
            if current["type"] != "dir" or part not in current["content"]:
                return f"File not found `{file_path}`"
            current = current["content"][part]

        if current["type"] != "file":
            return f"Error: {file_path} is not a file"

        return current["content"]

    def get_pull_request(self, pr_number: str) -> str:
        """Get information about a pull request."""
        if not self.pull_request:
            return "No pull request found"

        response_dict = {
            "title": self.pull_request["title"],
            "number": "1",
            "body": self.pull_request["body"],
            "comments": "[]",
            "commits": "[]",
        }

        return str(response_dict)

    def list_pull_requests_files(self, pr_number: str) -> str:
        """List files changed in a pull request."""
        if not self.pull_request:
            return "No pull request found"

        # Get all file operations related to this PR
        pr_files = [
            op["args"]["path"]
            for op in self.operations
            if op["args"].get("branch") == self.pull_request["head"]
        ]

        return str(pr_files) if pr_files else "No files changed in this pull request"

    def get_pull_request_head_branch(self, pr_number: str) -> str:
        """Get the head branch of a pull request."""
        if not self.pull_request:
            return "No pull request found"
        return self.pull_request["head"]

    def get_pull_request_diff(self, pr_number: str) -> str:
        """Get the diff of a pull request."""
        # TODO: how to mock this...?
        raise NotImplementedError("get_pull_request_diff mock is not implemented")

    def create_issue_comment(self, pr_number: str, body: str) -> str:
        """Comment on an issue."""
        logger.warning("create_isuse_comment mock is not implemented")
        return ""

    def create_pull_request_review(self, pr_number: str, review: str) -> str:
        """Leave a PR review."""
        # TODO: store list of reviews?
        # TODO: fn signature
        logger.warning("create_pull_request_review mock is not implemented")
        return ""

    def get_issue_body(self, issue_number: int) -> str:
        """Get the body of an issue."""
        logger.warning("get_issue_body mock is not implemented")
        return ""

    def get_latest_pr_workflow_run(self, pr_number: str) -> str:
        """Get the most recent workflow run for a PR."""
        logger.warning("get_latest_pr_workflow_run mock is not implemented")
        return ""


def get_github(base_branch) -> GitHubAPIWrapper:
    """Initialize a GitHub API wrapper instance based on environment variables.

    Required environment variables for GitHub API:
    - GITHUB_APP_ID
    - GITHUB_APP_PRIVATE_KEY
    - GITHUB_REPOSITORY
    """
    required_vars = ["GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", "GITHUB_REPOSITORY"]
    if not all(os.getenv(var) for var in required_vars):
        raise RuntimeError("Not all required environment variables set for GitHub API")

    return GitHubAPIWrapper(
        github_app_id=os.getenv("GITHUB_APP_ID"),
        github_app_private_key=os.getenv("GITHUB_APP_PRIVATE_KEY"),
        github_repository=os.getenv("GITHUB_REPOSITORY"),
        github_base_branch=base_branch,
    )


def get_mock_github() -> MockGithubApi:
    """Get a mock GitHub API wrapper."""
    return MockGithubApi()


def maybe_mock_github(
    base_branch: str = "main",
    allow_mocks_fallback: bool = True,
) -> Union[GitHubAPIWrapper, MockGithubApi]:
    """Get either a real GitHub API wrapper or a mock based configuration."""
    try:
        return get_github(base_branch)
    except RuntimeError as e:
        if allow_mocks_fallback:
            return get_mock_github()
        raise RuntimeError("Unable to initialize GitHub API wrapper") from e
