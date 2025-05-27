"""Define tools for the PR Memory Updater agent."""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated, Optional

from langchain_core.tools import tool


def _invoke(
    cmd: str, *, cwd: Optional[str] = None, err_ctx: Optional[str] = None
) -> str:
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True)

    if not err_ctx:
        err_ctx = f"Failed to run '{cmd}':"

    if result.returncode != 0:
        error_msg = result.stderr.decode("utf-8").strip()
        raise RuntimeError(f"{err_ctx}: {error_msg}")

    return result.stdout.decode("utf-8").strip()


def invoke_project_memory_from_pr(repo: str, pr: str) -> str:
    """Invoke the `update_project_memory_from_pr` script.

    Will take care of checking out the PR in a temporary directory and doing the necessary setup for the script to run

    Args:
      repo: the repository org/name to use the tool with
      pr: the PR number to generate the project memory for

    Will return a diff of the applied changes from the agent.
    """
    # TODO: ensure GEMINI_API_KEY is set?
    # TODO: ensure git, gh, jq, curl are available?
    # TODO: ensure gh is authenticated?

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

    memory_changes = None

    # script excepts to be run in a checkout
    # so set it up for given PR at tmpdir to not pollute environment
    with tempfile.TemporaryDirectory() as dir:
        _invoke(
            f"git clone https://github.com/{repo} --depth=1 --revision={rev} .",
            cwd=dir,
            err_ctx="Failed to clone repository",
        )

        # mark scripts as runnable
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

        # retrieve the updates that were made from the script
        memory_changes = _invoke(
            "git diff", cwd=dir, err_ctx="Failed to retrieve memory updates"
        )

    return memory_changes


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
    """Invoke the `fetch_pr_details` script."""
    if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", repo):
        raise ValueError(f"Invalid repository format: {repo}. Expected <org>/<name>.")
    if not re.match(r"^\d+$", pr):
        raise ValueError(f"Invalid PR number: {pr}. Expected 1 or more digits.")

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
    """Fetch the contents of the given project's global memory file."""
    full_path = (project_dir / global_memory_file).resolve()
    with open(full_path, "r+t") as f:
        return f.read()


@tool
def store_project_global_memory(
    *,
    project_dir: Annotated[Optional[str], "the project directory"] = os.curdir,
    global_memory_file: Annotated[
        Optional[Path], "the project global memory file path"
    ] = Path("project_memories/global.md"),
    content: Annotated[str, "the memory file contents to write"],
) -> str:
    """Store the given content to the project's global memory file."""
    full_path = (project_dir / global_memory_file).resolve()
    with open(full_path, "w+t") as f:
        return f.write(content)
