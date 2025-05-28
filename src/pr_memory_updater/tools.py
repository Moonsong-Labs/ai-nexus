"""Define tools for the PR Memory Updater agent."""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated, Awaitable, Callable, Optional

from langchain_core.tools import tool

from common.tools import create_file, read_file


def _invoke(
    cmd: str, *, cwd: Optional[str] = None, err_ctx: Optional[str] = None
) -> str:
    """
    Executes a shell command and returns its standard output as a string.
    
    If the command exits with a non-zero status, raises a RuntimeError with the provided error context and the command's standard error output.
    
    Args:
        cmd: The shell command to execute.
        cwd: Optional working directory in which to run the command.
        err_ctx: Optional context message to include in the error if the command fails.
    
    Returns:
        The standard output of the command, stripped of leading and trailing whitespace.
    
    Raises:
        RuntimeError: If the command exits with a non-zero status.
    """
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True)

    if not err_ctx:
        err_ctx = f"Failed to run '{cmd}':"

    if result.returncode != 0:
        error_msg = result.stderr.decode("utf-8").strip()
        raise RuntimeError(f"{err_ctx}: {error_msg}")

    return result.stdout.decode("utf-8").strip()


async def checkout_and_edit(repo: str, pr: str, *, thunk: Callable[str, Awaitable]) -> str:
    """
    Checks out a GitHub pull request into a temporary directory, runs an async callback, and returns the resulting git diff.
    
    The function validates the repository and PR number, clones the repository at the latest commit of the specified PR into a temporary directory, and executes the provided asynchronous `thunk` callback with the directory path. After the callback completes, it returns the diff of changes made within the checkout.
    
    Args:
        repo: The GitHub repository in the format "<org>/<name>".
        pr: The pull request number as a string.
        thunk: An asynchronous callback that receives the temporary directory path.
    
    Returns:
        The git diff as a string representing changes made by the callback.
    
    Raises:
        ValueError: If the repository or PR number format is invalid, or if the PR commit cannot be found.
    """
    if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", repo):
        raise ValueError(f"Invalid repository format: {repo}. Expected <org>/<name>.")
    if not re.match(r"^\d+$", pr):
        raise ValueError(f"Invalid PR number: {pr}. Expected 1 or more digits.")

    # retrieve last commit of the PR to create checkout from
    # choosing this instead of `main` to avoid out-of-sync PRs
    rev = _invoke(
        f"gh pr view {pr} -R {repo} --json commits | jq '.commits | last | .oid'",
        err_ctx="Failed to retrieve PR commit",
    )

    if not rev or rev == "null":
        raise ValueError(
            f"Could not find valid commit for PR {pr} in repository {repo}"
        )

    changes = None

    with tempfile.TemporaryDirectory() as dir:
        _invoke(
            f"git clone https://github.com/{repo} --depth=1 --revision={rev} .",
            cwd=dir,
            err_ctx="Failed to clone repository",
        )

        await thunk(dir)

        # retrieve the updates that were made from the script
        changes = _invoke(
            "git diff", cwd=dir, err_ctx="Failed to retrieve memory updates"
        )

    return changes


async def invoke_project_memory_from_pr(repo: str, pr: str) -> str:
    """
    Checks out a pull request and runs the project memory update script, returning the resulting diff.
    
    This function clones the specified GitHub repository at the given pull request, executes the `update_project_memory_from_pr.sh` script in a temporary directory, and returns the diff of changes made by the script.
    
    Args:
        repo: The GitHub repository in the format "org/name".
        pr: The pull request number as a string.
    
    Returns:
        The git diff output representing changes applied by the memory update script.
    """
    # TODO: ensure GEMINI_API_KEY is set?
    # TODO: ensure git, gh, jq, curl are available?
    # TODO: ensure gh is authenticated?

    async def _thunk(dir):
        # mark scripts as runnable
        """
        Sets execute permissions on required scripts and runs the project memory updater script in the specified directory.
        
        Args:
            dir: Path to the directory containing the scripts.
        """
        _invoke(
            "chmod +x ./scripts/update_project_memory_from_pr.sh ./scripts/fetch_pr_details.sh",
            cwd=dir,
            err_ctx="Failed to set execute permission on scripts",
        )

        # invoke scripts/update_project_memory_from_pr.sh
        _invoke(
            f"./scripts/update_project_memory_from_pr.sh -r {repo} -p {pr}",
            cwd=dir,
            err_ctx="Failed to run memory updater script",
        )

    return await checkout_and_edit(repo, pr, thunk=_thunk)

@tool(
    "fetch_pr_details",
    description="""Fetch the relevant details for a given repo, pr combination.

The data returned by the tool will be in loosely-formatted text, and should be processed into a more meaningful output.
""",
)
def invoke_pr_details(
    repo: Annotated[str, "the repository '<org>/<name>' which the PR belongs to"],
    pr: Annotated[str, "the PR number to retrieve the details for"],
) -> str:
    """
    Fetches pull request details for a given repository and PR number using a shell script.
    
    Validates the repository and PR number formats, then runs the `fetch_pr_details.sh` script to retrieve loosely formatted PR details as text.
    
    Args:
        repo: The repository in the format '<org>/<name>'.
        pr: The pull request number.
    
    Returns:
        The output of the `fetch_pr_details.sh` script containing PR details.
    
    Raises:
        ValueError: If the repository or PR number format is invalid.
        RuntimeError: If the script execution fails.
    """
    if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", repo):
        raise ValueError(f"Invalid repository format: {repo}. Expected <org>/<name>.")

    pr = pr.lstrip('#')
    if not re.match(r"^\d+$", pr):
        raise ValueError(f"Invalid PR number: {pr}. Expected 1 or more digits only.")

    return _invoke(
        f"./scripts/fetch_pr_details.sh -r {repo} -p {pr}",
        cwd=os.curdir,
        err_ctx="Failed to run fetch pr details script",
    )


@tool
def fetch_project_global_memory(
    *,
    project_dir: Annotated[Optional[str], "the project directory"] = os.curdir,
    global_memory_file: Annotated[
        Optional[Path], "the project global memory file path"
    ] = Path("project_memories/global.md"),
) -> str:
    """
    Reads and returns the contents of a project's global memory markdown file.
    
    Args:
        project_dir: The directory containing the project. Defaults to the current directory if not specified.
        global_memory_file: The path to the project's global memory file. Defaults to 'project_memories/global.md'.
    
    Returns:
        The contents of the global memory file as a string.
    """
    full_path = (project_dir / global_memory_file).resolve()
    return read_file.invoke({"file_path": str(full_path)})


@tool
def store_project_global_memory(
    *,
    project_dir: Annotated[Optional[str], "the project directory"] = os.curdir,
    global_memory_file: Annotated[
        Optional[Path], "the project global memory file path"
    ] = Path("project_memories/global.md"),
    content: Annotated[str, "the memory file contents to write"],
) -> str:
    """
    Writes the provided content to the project's global memory file.
    
    Args:
        project_dir: The directory of the project. Defaults to the current directory.
        global_memory_file: The path to the global memory file. Defaults to 'project_memories/global.md'.
        content: The content to write to the global memory file.
    
    Returns:
        A message indicating whether the content was successfully stored or an error message if the operation failed.
    """
    full_path = (project_dir / global_memory_file).resolve()
    result = create_file.invoke({"file_path": str(full_path), "content": content})
    if "Successfully" in result:
        return "Successfully stored project global memory"
    else:
        return result
