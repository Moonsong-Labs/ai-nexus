"""Tools for the code agent."""

from typing import Annotated, Optional
from github import Github
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.tools import InjectedToolArg
from langgraph.store.base import BaseStore

from code_agent.configuration import Configuration

@tool
def upsert_memory(
    key: Annotated[str, "Key to store the memory under"],
    value: Annotated[str, "Value to store"],
    config: InjectedToolArg[Configuration],
    store: InjectedToolArg[BaseStore],
) -> str:
    """Store a memory in the memory store."""
    mem_id = f"{config.user_id}:{key}"
    store.upsert(
        ("memories", config.user_id),
        mem_id,
        value,
    )
    return f"Stored memory {mem_id}"

@tool
def get_repo_contents(
    repo_name: Annotated[str, "Full repository name (owner/repo)"],
    path: Annotated[Optional[str], "Path to file or directory, empty for root"] = "",
) -> str:
    """Get contents of a file or directory in a GitHub repository."""
    g = Github()
    repo = g.get_repo(repo_name)
    try:
        contents = repo.get_contents(path)
        if isinstance(contents, list):
            return "\n".join(f"{item.path}: {item.type}" for item in contents)
        return contents.decoded_content.decode()
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def create_pull_request(
    repo_name: Annotated[str, "Full repository name (owner/repo)"],
    title: Annotated[str, "Title of the pull request"],
    body: Annotated[str, "Description of the pull request"],
    head: Annotated[str, "Branch containing changes"],
    base: Annotated[str, "Branch to merge into"] = "main",
) -> str:
    """Create a pull request in a GitHub repository."""
    g = Github()
    repo = g.get_repo(repo_name)
    try:
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return f"Created PR #{pr.number}: {pr.html_url}"
    except Exception as e:
        return f"Error: {str(e)}" 