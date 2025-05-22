"""Define tools for the PR Memory Updater agent"""

import subprocess
import tempfile

import re

from typing import Optional

def invoke_project_memory_from_pr(repo: str, pr: str, *, quiet: Optional[bool] = False) -> str:
    """
    Invoke the `update_project_memory_from_pr` script

    Will take care of checking out the PR in a temporary directory and doing the necessary setup for the script to run

    Args:
      repo: the repository org/name to use the tool with
      pr: the PR number to generate the project memory for
      quiet: if set to True, will silence intermediate commands outputs

    Will return a diff of the applied changes from the agent
    """
    #TODO: ensure GEMINI_API_KEY is set?
    #TODO: ensure git, gh, jq, curl are available?
    #TODO: ensure gh is authenticated?

    if not re.match(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$', repo):
        raise ValueError(f"Invalid repository format: {repo}. Expected <org>/<name>.")
    if not re.match(r'^\d+$', pr):
        raise ValueError(f"Invalid PR number: {pr}. Expected 1 or more digits.")

    # retrieve last commit of the PR to create checkout from
    # choosing this instead of `main` to avoid out-of-sync PRs
    result = subprocess.run(f"gh pr view {pr} -R {repo} --json commits | jq '.commits | last | .oid'", shell=True,  capture_output=True)

    # drop trailing newline
    rev = result.stdout.decode('utf-8').strip()

    memory_changes = None

    # script excepts to be run in a checkout
    # so set it up for given PR at tmpdir to not pollute environment
    with tempfile.TemporaryDirectory() as dir:
        subprocess.run(f"git clone https://github.com/{repo} --depth=1 --revision={rev} .", shell=True, cwd=dir, capture_output=quiet)

        # mark scripts as runnable
        subprocess.run("chmod +x ./scripts/update_project_memory_from_pr.sh ./scripts/fetch_pr_details.sh", shell=True, cwd=dir, capture_output=quiet)

        # invoke scripts/update_project_memory_from_pr.sh
        subprocess.run(f"./scripts/update_project_memory_from_pr.sh -r {repo} -p {pr}", shell=True, cwd=dir, capture_output=quiet)

        # retrieve the updates that were made from the script
        diff = subprocess.run("git diff", shell=True, cwd=dir, capture_output=True)
        memory_changes = diff.stdout.decode('utf-8').strip()

    return memory_changes
