"""Tools configuration for the code agent."""

from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.agent_toolkits.github.toolkit import (
    GitHubToolkit,
    BranchName,
    DirectoryPath,
    CreatePR,
    CreateFile,
    UpdateFile,
    ReadFile,
    DeleteFile,
)

from langchain_community.tools.github.prompt import (
    SET_ACTIVE_BRANCH_PROMPT,
    CREATE_BRANCH_PROMPT,
    GET_FILES_FROM_DIRECTORY_PROMPT,
    CREATE_PULL_REQUEST_PROMPT,
    CREATE_FILE_PROMPT,
    UPDATE_FILE_PROMPT,
    READ_FILE_PROMPT,
    DELETE_FILE_PROMPT,
)
from langchain_core.tools import Tool
from langchain_core.runnables import RunnableLambda
from coder.mocks import MockGithubApi

GITHUB_TOOLS = [
    "set_active_branch",
    "create_a_new_branch",
    "get_files_from_a_directory",
    "create_pull_request",
    "create_file",
    "update_file",
    "read_file",
    "delete_file",
    # TODO: evaluate adding these tools as well
    #"overview_of_existing_files_in_main_branch",
    #"overview_of_files_in_current_working_branch",
    #"search_code",
]

def github_tools():
    """Configure and return GitHub tools for the code agent."""
    github_api_wrapper = GitHubAPIWrapper()
    github_toolkit = GitHubToolkit.from_github_api_wrapper(github_api_wrapper)


    def make_gemini_compatible(tool):
        tool.name = tool.name.lower().replace(" ", "_").replace("'", "")
        return tool

    all_github_tools = [make_gemini_compatible(tool) for tool in github_toolkit.get_tools()]
    github_tools = [tool for tool in all_github_tools if tool.name in GITHUB_TOOLS]
    assert len(github_tools) == len(GITHUB_TOOLS), "Github tool mismatch"
    
    return github_tools 

def mock_github_tools(mock_api: MockGithubApi):
    """Create mocked GitHub tools using RunnableLambda.
    
    Args:
        mock_api: An instance of MockGithubApi to use for the tool implementations
    """
    tools = [
        RunnableLambda(mock_api.set_active_branch).as_tool(
            name="set_active_branch",
            description=SET_ACTIVE_BRANCH_PROMPT,
            args_schema=BranchName
        ),
        RunnableLambda(mock_api.create_branch).as_tool(
            name="create_a_new_branch",
            description=CREATE_BRANCH_PROMPT,
            args_schema=BranchName
        ),
        RunnableLambda(mock_api.get_files_from_directory).as_tool(
            name="get_files_from_a_directory",
            description=GET_FILES_FROM_DIRECTORY_PROMPT,
            args_schema=DirectoryPath
        ),
        RunnableLambda(mock_api.create_pull_request).as_tool(
            name="create_pull_request",
            description=CREATE_PULL_REQUEST_PROMPT,
            args_schema=CreatePR
        ),
        RunnableLambda(mock_api.create_file).as_tool(
            name="create_file",
            description=CREATE_FILE_PROMPT,
            args_schema=CreateFile
        ),
        RunnableLambda(mock_api.update_file).as_tool(
            name="update_file",
            description=UPDATE_FILE_PROMPT,
            args_schema=UpdateFile
        ),
        RunnableLambda(mock_api.read_file).as_tool(
            name="read_file",
            description=READ_FILE_PROMPT,
            args_schema=ReadFile
        ),
        RunnableLambda(mock_api.delete_file).as_tool(
            name="delete_file",
            description=DELETE_FILE_PROMPT,
            args_schema=DeleteFile
        )
    ]
    
    # Verify all tools from GITHUB_TOOLS are included
    tool_names = {tool.name for tool in tools}
    assert tool_names == set(GITHUB_TOOLS), f"Tool mismatch. Expected {set(GITHUB_TOOLS)}, got {tool_names}"
    
    return tools

if __name__ == "__main__":
    mock_api = MockGithubApi()
    tools = mock_github_tools(mock_api)
    for tool in tools:
        print(tool.name)
        print(tool.args_schema)
        print(tool.description)