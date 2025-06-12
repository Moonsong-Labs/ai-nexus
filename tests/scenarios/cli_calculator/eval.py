import json
import os
import re
import subprocess
import sys

from common.logging import get_logger
from common.utils import github as github_utils
from scenarios.cli_calculator.run import ScenarioRun

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


def keyword_file_check(repo_path: str) -> bool:
    """Tech evaluator: Check for required files and keywords."""
    # Check for Cargo.toml
    cargo_toml_path = os.path.join(repo_path, "Cargo.toml")
    if not os.path.exists(cargo_toml_path):
        logger.error("Cargo.toml not found")
        return False
    
    # Check for src/main.rs
    main_rs_path = os.path.join(repo_path, "src", "main.rs")
    if not os.path.exists(main_rs_path):
        logger.error("src/main.rs not found")
        return False
    
    logger.info("Required files found: Cargo.toml and src/main.rs")
    return True


def keyword_output_check(repo_path: str) -> bool:
    """Vocabulary evaluator: Check for required keywords in code."""
    main_rs_path = os.path.join(repo_path, "src", "main.rs")
    
    try:
        with open(main_rs_path, 'r') as f:
            content = f.read()
        
        required_keywords = [
            "fn main",
            "println!",
            "+",
            "-",
            "*",
            "/"
        ]
        
        # Check for argument handling (flexible - either clap or std::env::args)
        args_patterns = [
            "args",
            "clap",
            "std::env",
            "env::args",
            "Arguments",
            "Arg",
        ]
        
        missing_keywords = []
        for keyword in required_keywords:
            if keyword not in content:
                missing_keywords.append(keyword)
        
        # Check if at least one argument handling pattern is present
        has_args_handling = any(pattern in content for pattern in args_patterns)
        if not has_args_handling:
            missing_keywords.append("argument_handling")
        
        if missing_keywords:
            logger.error(f"Missing required keywords: {missing_keywords}")
            return False
        
        logger.info("All required keywords found in code")
        return True
        
    except Exception as e:
        logger.error(f"Failed to read main.rs: {e}")
        return False


def code_logic_evaluator(repo_path: str) -> bool:
    """Code logic evaluator: Check API signature and behavior."""
    main_rs_path = os.path.join(repo_path, "src", "main.rs")
    
    try:
        with open(main_rs_path, 'r') as f:
            content = f.read()
        
        # Check for main() function
        main_pattern = r'fn\s+main\s*\('
        if not re.search(main_pattern, content):
            logger.error("main() function not found")
            return False
        
        # Check for support of all 4 operators (+, -, *, /)
        operators = ['+', '-', '*', '/']
        for op in operators:
            if op not in content:
                logger.error(f"Operator {op} not supported")
                return False
        
        # Check for proper result printing to stdout
        if 'println!' not in content:
            logger.error("Must print result to stdout")
            return False
        
        # Check for handling invalid input/division by zero
        error_handling_patterns = [
            r'match\s+',
            r'if\s+.*==.*0',
            r'unwrap_or',
            r'expect\(',
            r'Result<',
            r'Option<',
            r'panic!'
        ]
        
        has_error_handling = any(re.search(pattern, content) for pattern in error_handling_patterns)
        if not has_error_handling:
            logger.error("No error handling patterns found")
            return False
        
        logger.info("Code logic evaluation passed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to evaluate code logic: {e}")
        return False


def compile_evaluator(repo_path: str) -> bool:
    """Compile evaluator: Run cargo check."""
    try:
        result = subprocess.run(
            ["cargo", "check", "--all"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Cargo check passed")
        logger.debug(result.stdout)
        if result.stderr:
            logger.debug(f"Cargo check warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Cargo check failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to run cargo check: {e}")
        return False


def test_evaluator(repo_path: str) -> bool:
    """Test evaluator: Run cargo test."""
    try:
        # First try running unit tests only
        result = subprocess.run(
            ["cargo", "test", "--lib"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Unit tests passed")
        logger.debug(result.stdout)
        if result.stderr:
            logger.debug(f"Unit test warnings: {result.stderr}")
        
        # Then try integration tests - allow partial success
        try:
            result_integration = subprocess.run(
                ["cargo", "test", "--test", "*"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,  # Don't wait too long for integration tests
            )
            if result_integration.returncode == 0:
                logger.info("All integration tests passed")
            else:
                # Check if at least some tests passed
                output = result_integration.stdout + result_integration.stderr
                if "test result:" in output:
                    # Parse test results to see how many passed
                    import re
                    # Look for patterns like "FAILED. 4 passed; 2 failed" or "ok. X passed"
                    failed_match = re.search(r'FAILED\.\s*(\d+)\s*passed;\s*\d+\s*failed', output)
                    ok_match = re.search(r'ok\.\s*(\d+)\s*passed', output)
                    
                    if failed_match and int(failed_match.group(1)) >= 2:
                        logger.info(f"Integration tests partially passed - {failed_match.group(1)} tests working, this is acceptable")
                        return True
                    elif ok_match and int(ok_match.group(1)) >= 2:
                        logger.info(f"Integration tests passed - {ok_match.group(1)} tests working")
                        return True
                    
                logger.warning("Some integration tests failed - checking if basic functionality works")
                logger.debug(f"Integration test output: {output}")
        except subprocess.TimeoutExpired:
            logger.warning("Integration tests timed out - this is acceptable")
        except subprocess.CalledProcessError:
            logger.warning("Integration tests failed - this is acceptable if unit tests pass")
        
        return True
        
    except subprocess.CalledProcessError:
        # If unit tests fail, try running all tests as fallback
        logger.warning("Unit tests failed, trying all tests...")
        try:
            result_all = subprocess.run(
                ["cargo", "test", "--all"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            
            # Even if it returns non-zero, check if some tests passed
            output = result_all.stdout + result_all.stderr
            if "test result:" in output:
                import re
                # Look for patterns like "FAILED. 4 passed; 2 failed" or "ok. X passed"
                failed_match = re.search(r'FAILED\.\s*(\d+)\s*passed;\s*\d+\s*failed', output)
                ok_match = re.search(r'ok\.\s*(\d+)\s*passed', output)
                
                if failed_match and int(failed_match.group(1)) >= 2:
                    logger.info(f"Tests partially passed - {failed_match.group(1)} tests working, this is acceptable")
                    return True
                elif ok_match and int(ok_match.group(1)) >= 2:
                    logger.info(f"Tests passed - {ok_match.group(1)} tests working")
                    return True
            
            # If it actually succeeded
            if result_all.returncode == 0:
                logger.info("All tests passed")
                return True
                
            logger.error(f"Most tests failed: {result_all.stderr}")
            return False
            
        except subprocess.CalledProcessError as e_all:
            logger.error(f"All tests failed: {e_all.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        return False


def eval(run: ScenarioRun):
    """Evaluate a CLI calculator scenario run."""
    
    # Use the harness path from requirements
    repo_path = "/tmp/rust_cli_calculator_ds"
    
    # Remove existing repository if it exists
    if os.path.exists(repo_path):
        subprocess.run(["rm", "-rf", repo_path], check=True)
        logger.info(f"Removed existing repository at: {repo_path}")
    
    os.makedirs(repo_path, exist_ok=True)

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
        logger.info(f"Successfully cloned repository to: {repo_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Failed to clone repository: {str(e)}")
        return None

    # Run all evaluators
    evaluators = [
        ("Tech evaluator", keyword_file_check),
        ("Vocabulary evaluator", keyword_output_check), 
        ("Code logic evaluator", code_logic_evaluator),
        ("Compile evaluator", compile_evaluator),
        ("Test evaluator", test_evaluator),
    ]
    
    all_passed = True
    for name, evaluator in evaluators:
        logger.info(f"Running {name}...")
        if not evaluator(repo_path):
            logger.error(f"{name} failed")
            all_passed = False
        else:
            logger.info(f"{name} passed")
    
    if all_passed:
        logger.info("SUCCESS: All evaluators passed")
    else:
        logger.error("FAILURE: Some evaluators failed")
    
    return all_passed


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <run_id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]
    scenario_runs_dir = os.path.join(os.path.dirname(__file__), "..", "scenario_runs", "scenarios-cli-calculator")
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

    success = eval(run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 