import asyncio

import dotenv

from common.logging import get_logger
from orchestrator.configuration import (
    ArchitectAgentConfig,
    CodeReviewerAgentConfig,
    RequirementsAgentConfig,
    SubAgentConfig,
    TaskManagerAgentConfig,
    TaskManagerConfiguration,
    TesterAgentConfig,
)
from orchestrator.configuration import Configuration as OrchestratorConfiguration
from orchestrator.stubs import MessageWheel
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)
from scenarios.cli_calculator import BASE_BRANCH
from scenarios.common import ScenarioConfig, ScenarioRun, ScenarioRunner

dotenv.load_dotenv()
logger = get_logger(__name__)


def config(save_run) -> ScenarioConfig:
    return ScenarioConfig(
        name="scenarios-cli-calculator",
        save_run=save_run,
        initial_prompt="I want to build a Rust CLI calculator that accepts two numbers and an operator as command-line arguments.",
        orchestrator_config=OrchestratorConfiguration(
            github_base_branch=BASE_BRANCH,
            requirements_agent=RequirementsAgentConfig(
                use_stub=False,
                config=RequirementsConfiguration(
                    use_human_ai=True,
                    human_ai_product="""
                    This is a HOBBY project. Create a Rust CLI calculator that accepts two numbers and an operator (+, -, *, /) as positional command-line arguments, computes the result and prints it.

                    Requirements:
                    - Project structure: Cargo.toml in root, src/main.rs for main logic, optionally src/lib.rs for shared functions
                    - Functionality: Accept exactly 3 positional arguments in order: number1, operator, number2
                    - Usage: cargo run <number1> <operator> <number2> (e.g., cargo run 10 + 20, cargo run 15.5 * 3)
                    - No named parameters or flags - use simple positional arguments only with std::env::args
                    - Error handling: Gracefully handle invalid input, division by zero, and malformed arguments with appropriate error messages and exit codes
                    - Testing: Include comprehensive tests covering all four operators with various numbers and invalid cases (division by zero, invalid operators, malformed input, missing arguments)
                    - Tests runnable with 'cargo test' and verify correct behavior for valid inputs and appropriate failures for invalid inputs
                    - Code must compile with 'cargo check --all' and pass all tests with 'cargo test --all'
                    - Follow Rust best practices and conventions
                    """,
                ),
                stub_messages=MessageWheel(
                    [
                        "I have gathered the requirements for the project. This should be a Rust CLI calculator that accepts two numbers and an operator (+, -, *, /) as command-line arguments, computes the result and prints it. The calculator should gracefully handle invalid input or division by zero. The signature should parse 3 arguments and use Cargo.toml with src/main.rs structure.",
                    ]
                ),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=False,
                stub_messages=MessageWheel(
                    [
                        "Architecture should follow cargo binary structure with Cargo.toml and src/main.rs. The binary should use clap for command line argument parsing with positional args: first number, operator (+, -, *, /), second number. Include proper error handling for invalid input and division by zero. The main function should parse args, compute result, and print output.",
                    ]
                ),
            ),
            task_manager_agent=TaskManagerAgentConfig(
                use_stub=False,
                config=TaskManagerConfiguration(),
                stub_messages=MessageWheel(
                    [
                        """
                    There's only one task for the coder:
                     1) Create a Rust CLI calculator that accepts two numbers and an operator (+, -, *, /) as command-line arguments, computes the result and prints it. Use clap for argument parsing. Include proper error handling for invalid input and division by zero. Include tests for each operator path.
                    """
                    ]
                ),
            ),
            coder_new_pr_agent=SubAgentConfig(
                use_stub=False,
            ),
            coder_change_request_agent=SubAgentConfig(
                use_stub=True,
            ),
            reviewer_agent=CodeReviewerAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "The CLI calculator implementation looks correct and follows best practices.",
                    ]
                ),
            ),
            tester_agent=TesterAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "I have tested the CLI calculator with various operators and edge cases and found no issues.",
                    ]
                ),
            ),
        ),
    )


def run(save_run=False) -> ScenarioRun:
    """Run CLI Calculator scenario"""
    runner = ScenarioRunner(config=config(save_run))
    return asyncio.run(runner.run())


if __name__ == "__main__":
    run(True)
