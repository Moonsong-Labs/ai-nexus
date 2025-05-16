"""Tools for the code agent."""

from typing import Type, Union
import requests

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
from github.Commit import Commit
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from common.components.github_mocks import MockGithubApi

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
    "comment_on_issue",
    # TODO: evaluate adding these tools as well
    # "overview_of_existing_files_in_main_branch",
    # "overview_of_files_in_current_working_branch",
    # "search_code",

    # custom tools
    "get_pull_request_head_branch",
    "get_pull_request_head_commit",
    "get_pull_request_diff",
    "create_pull_request_review_comment",
]




CREATE_PULL_REQUEST_REVIEW_COMMENT_PROMPT = """
This tool is a wrapper for the GitHub API, useful when you want to leave a pull request review comment. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:

- First you must specify the PR number. **VERY IMPORTANT**: You must specify the PR number as an integer."
- Then you must specify the body of the review comment for the overall PR.
- Then you must specify the commit ID for the review comment. This should be an empty string for now.
- Then you must specify the path of the file in the diff hunk that this refers to.
- Then you must specify the path of the line number in the diff hunk that this refers to.
"""
class CreatePRReviewComment(BaseModel):
    """Schema for creating a Pull Request Review Comment."""

    pr_number: int = Field(0, description="The PR number as an integer, e.g. `12`")
    body: str = Field(1, description="The overall feedback for the review comment.")
    commit: str = Field(2, description="The commit ID for the review comment.")
    path: str = Field(3, description="The file path from the diff hunk this comment relates to.")
    line: int = Field(4, description="The line number from the diff hunk this comment relates to.")
class CreatePullRequestReviewComment(BaseTool):
    """Create a Pull Request Review Comment."""

    name: str = "create_pull_request_review_comment"
    description: str = CREATE_PULL_REQUEST_REVIEW_COMMENT_PROMPT
    args_schema: Type[BaseModel] = CreatePRReviewComment
    github_api_wrapper: GitHubAPIWrapper

    """full create_review_comment function:
        def create_review_comment(
          self,
          body: str,
          commit: github.Commit.Commit,
          path: str,
          # line replaces deprecated position argument, so we put it between path and side
          line: Opt[int] = NotSet,
          side: Opt[str] = NotSet,
          start_line: Opt[int] = NotSet,
          start_side: Opt[str] = NotSet,
          in_reply_to: Opt[int] = NotSet,
          subject_type: Opt[str] = NotSet,
          as_suggestion: bool = False,
      ) -> PullRequestComment:
    """

    def _run(self, pr_number: int, body: str, commit: str, path: str, line: int):
        commit_obj = self.github_api_wrapper.github_repo_instance.get_commit(commit)
        # TODO: this is a pretty heavy request, and this more or less forces it to be duplicated
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        pull_request.create_review_comment(body, commit_obj, path, line)

    async def _arun(self, pr_number: int, body: str, commit: str, path: str, line: int):
        commit_obj = self.github_api_wrapper.github_repo_instance.get_commit(commit)
        # TODO: this is a pretty heavy request, and this more or less forces it to be duplicated
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        pull_request.create_review_comment(body, commit_obj, path, line)

GET_PULL_REQUEST_DIFF_PROMPT = "This tool will return the diff of the code in a PR. **VERY IMPORTANT**: You must specify the PR number as an integer."
class GetPullRequestDiff(BaseTool):
    """Get the diff of a specific Pull Request (by PR number)."""

    name: str = "get_pull_request_diff"
    description: str = GET_PULL_REQUEST_DIFF_PROMPT
    args_schema: Type[BaseModel] = GetPR
    github_api_wrapper: GitHubAPIWrapper

    def _run(self, pr_number: int) -> str:
        # TODO: this is a pretty heavy request, and this more or less forces it to be duplicated
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        diff_url = pull_request.diff_url
        response = requests.get(diff_url, headers={'Accept': 'application/vnd.github.v3.diff'})
        response.raise_for_status()

        diff_content = response.text
        return diff_content

    async def _arun(self, pr_number: int) -> str:
        # TODO: this is a pretty heavy request, and this more or less forces it to be duplicated
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        diff_url = pull_request.diff_url
        response = requests.get(diff_url, headers={'Accept': 'application/vnd.github.v3.diff'})
        response.raise_for_status()

        diff_content = response.text
        return diff_content

# TODO: this is essentially the same as GetPullRequestHeadBranch, but returns the commit itself.
#       the two could be combined
GET_PULL_REQUEST_HEAD_COMMIT_PROMPT = "This tool will fetch the head commit of a specific Pull Request (by PR number). **VERY IMPORTANT**: You must specify the PR number as an integer."
class GetPullRequestHeadCommit(BaseTool):
    """Get the head commit of a specific Pull Request (by PR number)."""

    name: str = "get_pull_request_head_commit"
    description: str = GET_PULL_REQUEST_HEAD_COMMIT_PROMPT
    args_schema: Type[BaseModel] = GetPR
    github_api_wrapper: GitHubAPIWrapper

    def _run(self, pr_number: int) -> str:
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        return pull_request.head.sha

    async def _arun(self, pr_number: int) -> str:
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        return pull_request.head.sha

GET_PULL_REQUEST_HEAD_BRANCH_PROMPT = "This tool will fetch the head branch of a specific Pull Request (by PR number). **VERY IMPORTANT**: You must specify the PR number as an integer."
class GetPullRequestHeadBranch(BaseTool):
    """Get the head branch of a specific Pull Request (by PR number)."""

    name: str = "get_pull_request_head_branch"
    description: str = GET_PULL_REQUEST_HEAD_BRANCH_PROMPT
    args_schema: Type[BaseModel] = GetPR
    github_api_wrapper: GitHubAPIWrapper

    def _run(self, pr_number: int) -> str:
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        return pull_request.head.ref

    async def _arun(self, pr_number: int) -> str:
        pull_request = self.github_api_wrapper.github_repo_instance.get_pull(pr_number)
        return pull_request.head.ref


def github_tools(github_api_wrapper: GitHubAPIWrapper) -> list[BaseTool]:
    """Configure and return GitHub tools for the code agent."""
    github_toolkit = GitHubToolkit.from_github_api_wrapper(github_api_wrapper)

    def make_gemini_compatible(tool):
        tool.name = tool.name.lower().replace(" ", "_").replace("'", "")
        return tool

    all_github_tools = [
        make_gemini_compatible(tool) for tool in github_toolkit.get_tools()
    ] + [
        CreatePullRequestReviewComment(github_api_wrapper=github_api_wrapper),
        GetPullRequestHeadBranch(github_api_wrapper=github_api_wrapper),
        GetPullRequestHeadCommit(github_api_wrapper=github_api_wrapper),
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
