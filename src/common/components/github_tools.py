"""Tools for the code agent."""

import asyncio
import logging
import tempfile
import zipfile
from os import listdir
from typing import List, Type, Union

import requests
from github.PullRequest import ReviewComment
from langchain_community.agent_toolkits.github.toolkit import (
    BranchName,
    CreateFile,
    CreatePR,
    DeleteFile,
    DirectoryPath,
    GetPR,
    GitHubToolkit,
    ReadFile,
    UpdateFile,
)
from langchain_community.tools.github.prompt import (
    CREATE_BRANCH_PROMPT,
    CREATE_FILE_PROMPT,
    CREATE_PULL_REQUEST_PROMPT,
    DELETE_FILE_PROMPT,
    GET_FILES_FROM_DIRECTORY_PROMPT,
    GET_PR_PROMPT,
    LIST_PULL_REQUEST_FILES,
    READ_FILE_PROMPT,
    SET_ACTIVE_BRANCH_PROMPT,
    UPDATE_FILE_PROMPT,
)
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from common.components.github_mocks import MockGithubApi

logger = logging.getLogger(__name__)

GITHUB_TOOLS = [
    "set_active_branch",
    "create_a_new_branch",
    "get_files_from_a_directory",
    "create_pull_request",
    "create_file",
    "update_file",
    "read_file",
    "delete_file",
    "get_pull_request",
    "list_pull_requests_files",
    # TODO: evaluate adding these tools as well
    # "overview_of_existing_files_in_main_branch",
    # "overview_of_files_in_current_working_branch",
    # "search_code",
    # custom tools
    "get_latest_pr_workflow_run",
    "get_pull_request_head_branch",
    "get_pull_request_diff",
    "create_pull_request_review",
    "create_issue_comment",
]

CREATE_ISSUE_COMMENT_PROMPT = """
This tool is a wrapper for the GitHub API, useful when you want to comment on a pull request or issue. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:

- First you must specify the PR number. **VERY IMPORTANT**: You must specify the PR number as an integer, not a float."
- Then you must specify the body of your comment.
"""


class IssueComment(BaseModel):
    """Schema for creating an issue comment."""

    pr_number: int = Field(0, description="The PR number as an integer, e.g. `12`")
    body: str = Field(
        1, description="The comment to be left on the issue or pull request."
    )


class CreateIssueComment(BaseTool):
    """Create an Issue or Pull Request Comment."""

    name: str = "create_issue_comment"
    description: str = CREATE_ISSUE_COMMENT_PROMPT
    args_schema: Type[BaseModel] = IssueComment
    github_api_wrapper: GitHubAPIWrapper

    def _run(self, pr_number: int, body: str):
        return asyncio.run(self._arun(pr_number, body))

    async def _arun(self, pr_number: int, body: str):
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        pull_request.create_issue_comment(body)


class PRReviewComment(BaseModel):
    """Schema for a Pull Request Review Comment."""

    path: str = Field(
        0, description="The file path from the diff hunk this comment relates to."
    )
    position: int = Field(
        1,
        description="""The position in the diff where you want to add a review comment. Note this value is not the same as the line number in the file. The position value equals the number of lines down from the first "@@" hunk header in the file you want to add a comment. The line just below the "@@" line is position 1, the next line is position 2, and so on. The position in the diff continues to increase through lines of whitespace and additional hunks until the beginning of a new file. **VERY IMPORTANT:** This MUST be an integer, not a float.""",
    )
    body: str = Field(2, description="Text of the review comment.")
    line: int = Field(
        3,
        description="The line number from the diff hunk this comment relates to. **VERY IMPORTANT:** This MUST be an integer, not a float. The feedback is represented BELOW this line number, not above it, so you may need to add one to the number.",
    )

    # converts to a pygithub ReviewComment object
    def to_gh_review(self):
        """Convert self to a pygithub ReviewComment object."""
        comment = ReviewComment()
        comment["path"] = self.path
        # bug fix: this fixes the eventual HTTP POST data to use "line" instead of the deprecated
        # "position", github otherwise rejects the request. this is probably a bug in pygithub
        comment["line"] = self.position
        comment["body"] = self.body
        comment["line"] = self.line
        return comment


CREATE_PULL_REQUEST_REVIEW_PROMPT = """
This tool is a wrapper for the GitHub API, useful when you want to leave a pull request review comment. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:

- First you must specify the PR number. **VERY IMPORTANT**: You must specify the PR number as an integer, not a float."
- Then you must specify the body of your main comment, which is a summary of your overall feedback. It should mention anything that is very important and clearly express whether changes are requested or not.
- Then you must specify the event for the review, which **MUST BE** one of 'REQUEST_CHANGES', 'APPROVE', or 'COMMENT'.
- Then you must specify comments that are specific to any diff hunks. If there are none, this MUST be an empty List and CANNOT be omitted.
"""


class CreatePRReview(BaseModel):
    """Schema for creating a Pull Request Review."""

    pr_number: int = Field(0, description="The PR number as an integer, e.g. `12`")
    body: str = Field(1, description="The overall feedback for the review comment.")
    event: str = Field(
        2,
        description="Must be one of 'REQUEST_CHANGES' if changes are required, 'APPROVE' if approving the PR, or 'COMMENT' otherwise.",
    )
    comments: List[PRReviewComment] = Field(
        3, description="A list of comments to include with this review."
    )


class CreatePullRequestReviewComment(BaseTool):
    """Create a Pull Request Review Comment."""

    name: str = "create_pull_request_review"
    description: str = CREATE_PULL_REQUEST_REVIEW_PROMPT
    args_schema: Type[BaseModel] = CreatePRReview
    github_api_wrapper: GitHubAPIWrapper

    def _run(
        self, pr_number: int, body: str, event: str, comments: List[PRReviewComment]
    ):
        return asyncio.run(self._arun(pr_number, body, event, comments))

    async def _arun(
        self, pr_number: int, body: str, event: str, comments: List[PRReviewComment]
    ):
        comments_mapped = list(map(lambda x: x.to_gh_review(), comments))

        # TODO: this is a pretty heavy request, and this more or less forces it to be duplicated
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        commit = pull_request.head.sha
        commit_obj = self.github_api_wrapper.github_repo_instance.get_commit(commit)

        pull_request.create_review(commit_obj, body, event, comments_mapped)


GET_PULL_REQUEST_DIFF_PROMPT = "This tool will return the diff of the code in a PR. **VERY IMPORTANT**: You must specify the PR number as an integer."


class GetPullRequestDiff(BaseTool):
    """Get the diff of a specific Pull Request (by PR number)."""

    name: str = "get_pull_request_diff"
    description: str = GET_PULL_REQUEST_DIFF_PROMPT
    args_schema: Type[BaseModel] = GetPR
    github_api_wrapper: GitHubAPIWrapper

    def _run(self, pr_number: int) -> str:
        return asyncio.run(self._arun(pr_number))

    async def _arun(self, pr_number: int) -> str:
        # TODO: this is a pretty heavy request, and this more or less forces it to be duplicated
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        diff_url = pull_request.diff_url
        response = requests.get(
            diff_url, headers={"Accept": "application/vnd.github.v3.diff"}
        )
        response.raise_for_status()

        diff_content = response.text
        return diff_content


GET_PULL_REQUEST_HEAD_BRANCH_PROMPT = "This tool will fetch the head branch of a specific Pull Request (by PR number). **VERY IMPORTANT**: You must specify the PR number as an integer."


class GetPullRequestHeadBranch(BaseTool):
    """Get the head branch of a specific Pull Request (by PR number)."""

    name: str = "get_pull_request_head_branch"
    description: str = GET_PULL_REQUEST_HEAD_BRANCH_PROMPT
    args_schema: Type[BaseModel] = GetPR
    github_api_wrapper: GitHubAPIWrapper

    def _run(self, pr_number: int) -> str:
        return asyncio.run(self._arun(pr_number))

    async def _arun(self, pr_number: int) -> str:
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        return pull_request.head.ref


GET_LATEST_PR_WORKFLOW_RUN_PROMPT = "This tool will get the most recent workflow run for a given PR. **VERY IMPORTANT**: You must specify the PR number as an integer."


class GetLatestPRWorkflowRun(BaseTool):
    """Get the most recent workflow run for a PR."""

    name: str = "get_latest_pr_workflow_run"
    description: str = GET_LATEST_PR_WORKFLOW_RUN_PROMPT
    args_schema: Type[BaseModel] = GetPR
    github_api_wrapper: GitHubAPIWrapper

    def _run(self, pr_number: int) -> str:
        return asyncio.run(self._arun(pr_number))

    async def _arun(self, pr_number: int) -> str:
        repo = self.github_api_wrapper.github_repo_instance
        pull_request = repo.get_pull(pr_number)
        pr_commit = pull_request.head.sha
        workflow_runs = repo.get_workflow_runs(head_sha=pr_commit, event="pull_request")
        logger.info(f"num workflow runs: {workflow_runs.totalCount}")
        if workflow_runs.totalCount > 0:
            page = workflow_runs.get_page(0)
            logs_url = page[0].logs_url

            auth_token = repo.requester.auth.token

            response = requests.get(
                logs_url,
                headers={
                    "Accept": "application/vnd.github+text",
                    "Authorization": "Bearer " + auth_token,
                },
            )
            response.raise_for_status()

            # generate a random temp dir for extracting the logs (which is a zip file)
            dir = tempfile.TemporaryDirectory()
            dirname = f"{dir.name}/workflow_run_logs.zip"

            file = open(f"{dir.name}/workflow_run_logs.zip", "wb")
            file.write(response.content)
            file.close()

            zip = zipfile.ZipFile(f"{dir.name}/workflow_run_logs.zip", "r")
            zip.extractall(dir.name)

            content = ""
            log_files = [f for f in listdir(dir.name) if f.endswith(".txt")]
            for file in log_files:
                with open(f"{dir.name}/{file}") as f:
                    content += f.read()
                    content += "\n\n"

            dir.cleanup()
            return content

        return ""


def github_tools(github_api_wrapper: GitHubAPIWrapper) -> list[BaseTool]:
    """Configure and return GitHub tools for the code agent."""
    github_toolkit = GitHubToolkit.from_github_api_wrapper(github_api_wrapper)

    def make_gemini_compatible(tool):
        tool.name = tool.name.lower().replace(" ", "_").replace("'", "")
        return tool

    all_github_tools = [
        make_gemini_compatible(tool) for tool in github_toolkit.get_tools()
    ] + [
        GetLatestPRWorkflowRun(github_api_wrapper=github_api_wrapper),
        CreatePullRequestReviewComment(github_api_wrapper=github_api_wrapper),
        CreateIssueComment(github_api_wrapper=github_api_wrapper),
        GetPullRequestHeadBranch(github_api_wrapper=github_api_wrapper),
        GetPullRequestDiff(github_api_wrapper=github_api_wrapper),
    ]
    github_tools = [tool for tool in all_github_tools if tool.name in GITHUB_TOOLS]
    assert len(github_tools) == len(GITHUB_TOOLS), "Github tool mismatch"

    return github_tools


def _convert_args_schema_to_string(func, args_schema: Type[BaseModel]):
    """Wrap a function to convert its BaseModel argument to a string."""

    def wrapper(args: dict):
        # Get the first field from the schema class
        field_names = list(args_schema.model_json_schema()["properties"].keys())
        if len(field_names) > 1:
            raise AssertionError(
                f"Expected one argument in tool schema, got {field_names}."
            )
        field = field_names[0] if field_names else ""
        value = args.get(field, "")
        return func(str(value))

    return wrapper


def mock_github_tools(mock_api: MockGithubApi):
    """Create mocked GitHub tools.

    Args:
        mock_api: An instance of MockGithubApi to use for the tool implementations
    """
    tools = [
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.set_active_branch, BranchName)
        ).as_tool(
            name="set_active_branch",
            description=SET_ACTIVE_BRANCH_PROMPT,
            args_schema=BranchName,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.create_branch, BranchName)
        ).as_tool(
            name="create_a_new_branch",
            description=CREATE_BRANCH_PROMPT,
            args_schema=BranchName,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(
                mock_api.get_files_from_directory, DirectoryPath
            )
        ).as_tool(
            name="get_files_from_a_directory",
            description=GET_FILES_FROM_DIRECTORY_PROMPT,
            args_schema=DirectoryPath,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.create_pull_request, CreatePR)
        ).as_tool(
            name="create_pull_request",
            description=CREATE_PULL_REQUEST_PROMPT,
            args_schema=CreatePR,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.create_file, CreateFile)
        ).as_tool(
            name="create_file", description=CREATE_FILE_PROMPT, args_schema=CreateFile
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.update_file, UpdateFile)
        ).as_tool(
            name="update_file", description=UPDATE_FILE_PROMPT, args_schema=UpdateFile
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.read_file, ReadFile)
        ).as_tool(name="read_file", description=READ_FILE_PROMPT, args_schema=ReadFile),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.delete_file, DeleteFile)
        ).as_tool(
            name="delete_file", description=DELETE_FILE_PROMPT, args_schema=DeleteFile
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.get_pull_request, GetPR)
        ).as_tool(
            name="get_pull_request",
            description=GET_PR_PROMPT,
            args_schema=GetPR,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.list_pull_requests_files, GetPR)
        ).as_tool(
            name="list_pull_requests_files",
            description=LIST_PULL_REQUEST_FILES,
            args_schema=GetPR,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.get_pull_request_head_branch, GetPR)
        ).as_tool(
            name="get_pull_request_head_branch",
            description=GET_PULL_REQUEST_HEAD_BRANCH_PROMPT,
            args_schema=GetPR,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(mock_api.get_pull_request_diff, GetPR)
        ).as_tool(
            name="get_pull_request_diff",
            description=GET_PULL_REQUEST_DIFF_PROMPT,
            args_schema=GetPR,
        ),
        RunnableLambda(
            _convert_args_schema_to_string(
                mock_api.create_pull_request_review, CreatePRReview
            )
        ).as_tool(
            name="create_pull_request_review",
            description=CREATE_PULL_REQUEST_REVIEW_PROMPT,
            args_schema=CreatePRReview,
        ),
    ]

    # Verify all tools from GITHUB_TOOLS are included
    tool_names = {tool.name for tool in tools}
    assert tool_names == set(GITHUB_TOOLS), (
        f"Tool mismatch. Expected {set(GITHUB_TOOLS)}, got {tool_names}"
    )

    return tools


def get_github_tools(source: Union[GitHubAPIWrapper, MockGithubApi]) -> list[BaseTool]:
    """Get the GitHub tools.

    Args:
        source: Either a GitHubAPIWrapper or MockGithubApi instance
    """
    if isinstance(source, GitHubAPIWrapper):
        return github_tools(source)
    return mock_github_tools(source)
