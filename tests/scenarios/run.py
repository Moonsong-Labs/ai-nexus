"""Run all scenarios."""

import sys
from typing import List

import binary_search.run as binary_search
import fibonacci.run as fibonacci
import stack.run as stack
from github import GithubException, Repository

from common.logging import get_logger
from scenarios import BASE_BRANCHES
from scenarios.runner import init_github

logger = get_logger(__name__)


def create_branches(repo: Repository, branches: List[str]):
    """Create base branches if they don't exist."""
    logger.info(f"Repository: {repo.full_name}")
    logger.info(f"Default branch: {repo.default_branch}")

    for branch in branches:
        try:
            repo.get_branch(branch)
            logger.info(f"Branch '{branch}' already exists")
        except Exception:
            try:
                default_branch = repo.default_branch
                source = repo.get_branch(default_branch)
                ref = f"refs/heads/{branch}"
                repo.create_git_ref(ref, source.commit.sha)
                logger.info(f"Created branch '{branch}' from '{default_branch}'")
            except Exception as e:
                raise Exception(f"Failed to create branch '{branch}': {str(e)}")


def cleanup_branches(repo: Repository, base_branches: List[str]) -> None:
    """Delete branches that are not in base_branches."""
    logger.info(f"Repository: {repo.full_name}")
    logger.info(f"Default branch: {repo.default_branch}")

    # Get all branches
    all_branches = [branch.name for branch in repo.get_branches()]
    print(f"Current branches: {all_branches}")

    # Delete branches not in base_branches
    for branch in all_branches:
        if branch not in base_branches and branch != repo.default_branch:
            try:
                ref = f"heads/{branch}"
                git_ref = repo.get_git_ref(ref)
                git_ref.delete()
                logger.info(f"Deleted branch: {branch}")
            except GithubException as e:
                logger.error(f"Failed to delete branch '{branch}': {str(e)}")


def setup():
    """Setup function to create branches."""
    repo = init_github()
    create_branches(repo, BASE_BRANCHES)


def teardown():
    """Teardown function to cleanup branches."""
    repo = init_github()
    cleanup_branches(repo, BASE_BRANCHES)


scenarios = {
    "stack": stack.run,
    "fibonacci": fibonacci.run,
    "binary_search": binary_search.run,
}


def run_scenario(name):
    """Run all scenarios."""

    if name not in scenarios:
        logger.error(f"Unknown scenario: {name}")
        logger.error(f"Available scenarios: {', '.join(scenarios.keys())}")
        sys.exit(1)

    scenarios[name](True)


def main(scenarios=scenarios.keys()):
    """Main function to run setup, scenarios, and teardown."""
    logger.info(f"Preparing to run scenarios: {scenarios}")
    setup()
    for name in scenarios:
        run_scenario(name)
    teardown()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "setup":
            setup()
        elif command == "cleanup":
            teardown()
        elif command == "run":
            targets = None
            if len(sys.argv) == 2:
                main()
            else:
                # Run specific scenarios
                main(sys.argv[2:])
        else:
            print(f"Unknown command: {command}")
            print(
                "Usage: uv run -- python tests/scenarios/run.py [setup|cleanup|run [scenario_names...]]"
            )
            sys.exit(1)
    else:
        main()
