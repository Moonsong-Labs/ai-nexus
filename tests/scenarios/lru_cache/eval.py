import json
import os
import subprocess
import sys

from common.logging import get_logger
from common.utils import github as github_utils
from scenarios.lru_cache.run import ScenarioRun

logger = get_logger(__name__)


def is_git_repo(path: str) -> bool:
    """Check if a directory is a git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def eval(run: ScenarioRun):
    """Evaluate a scenario run by cloning the repository and making some checks."""

    repo_path = f"/tmp/ai-nexus/{run['run_id']}"
    os.makedirs(repo_path, exist_ok=True)

    if not is_git_repo(repo_path):
        env = os.environ.copy()
        env["GIT_ASKPASS"] = "echo"
        env["GIT_TERMINAL_PROMPT"] = "0"

        github_integration = github_utils.app_get_integration()
        github_installation = github_utils.app_get_installation(github_integration)
        github_token = github_integration.get_access_token(github_installation.id).token

        try:
            # Clone using HTTPS with installation token
            subprocess.run(
                [
                    "git",
                    "clone",
                    f"https://x-access-token:{github_token}@github.com/{os.getenv('GITHUB_REPOSITORY')}.git",
                    repo_path,
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            # Checkout the specific branch
            subprocess.run(
                [
                    "git",
                    "checkout",
                    run["branch"],
                ],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            logger.debug(f"Successfully cloned repository to: {repo_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            return None
    else:
        logger.debug(f"Git repository already exists at {repo_path}")

    # Check for Cargo.toml
    cargo_toml_path = os.path.join(repo_path, "Cargo.toml")
    assert os.path.exists(cargo_toml_path), "Cargo.toml not found in repository"

    # Copy test files
    test_dir = os.path.join(repo_path, "tests")
    os.makedirs(test_dir, exist_ok=True)

    # Run cargo check
    try:
        cmd = ["cargo", "check"]

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.debug("Cargo check output:")
        logger.debug(result.stdout)
        if result.stderr:
            logger.debug("Cargo check warnings/errors:")
            logger.debug(result.stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Cargo check failed: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Failed to run cargo check: {str(e)}")
        return None

    logger.debug(f"Copying test files from {os.path.dirname(__file__)} to {test_dir}")
    source_test_dir = os.path.join(os.path.dirname(__file__), "tests")
    for file in os.listdir(source_test_dir):
        source_file = os.path.join(source_test_dir, file)
        dest_file = os.path.join(test_dir, file)
        with open(source_file, "r") as src, open(dest_file, "w") as dst:
            dst.write(src.read())

    # Run cargo test
    try:
        result = subprocess.run(
            ["cargo", "test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.debug("Cargo test output:")
        logger.debug(result.stdout)
        if result.stderr:
            logger.debug("Cargo test warnings/errors:")
            logger.debug(result.stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Cargo test failed: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Failed to run cargo test: {str(e)}")
        return None

    logger.info("SUCCESS")


if __name__ == "__main__":
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

    eval(run)
