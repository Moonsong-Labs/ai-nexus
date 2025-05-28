import json
import os
import sys
from typing import Optional

from common.logging import get_logger
from common.utils import github as github_utils

from .run import ScenarioRun

logger = get_logger(__name__)


def eval(run: ScenarioRun) -> Optional[str]:
    """
    Evaluate a scenario run by cloning the repository.

    Args:
        run: The scenario run to evaluate

    Returns:
        Optional[str]: Path to the cloned repository if successful, None otherwise
    """
    repo_path = f"/tmp/ai-nexus/{run['run_id']}"
    os.makedirs(repo_path, exist_ok=True)

    github_client = github_utils.get_client_from_app_credentials()
    repo = github_client.get_repo(os.getenv("GITHUB_REPOSITORY"))

    try:
        # Get the branch
        branch = repo.get_branch(run["branch"])

        # Clone the repository
        repo.clone_to(repo_path, branch=branch.name)
        return repo_path
    except Exception as e:
        logger.error(f"Failed to clone repository: {str(e)}")
        return None


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <run_id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]
    scenario_runs_dir = os.path.join(os.path.dirname(__file__), "scenario_runs")
    run_file = os.path.join(scenario_runs_dir, f"{run_id}.json")

    try:
        with open(run_file, "r") as f:
            run_data = json.load(f)
            run = ScenarioRun(**run_data)
    except FileNotFoundError:
        logger.error(f"Run file not found: {run_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in run file: {run_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load run data: {str(e)}")
        sys.exit(1)

    result = eval(run)
    if result:
        logger.info(f"Successfully cloned repository to: {result}")
    else:
        logger.error("Failed to clone repository")
        sys.exit(1)


if __name__ == "__main__":
    main()
