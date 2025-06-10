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
from scenarios.common import ScenarioConfig, ScenarioRun, ScenarioRunner
from scenarios.fibonacci import BASE_BRANCH

dotenv.load_dotenv()
logger = get_logger(__name__)

def config(save_run) -> ScenarioConfig:
    """Create configuration for Fibonacci scenario"""
    return ScenarioConfig(
        name="scenarios-fibonacci",
        save_run=save_run,
        initial_prompt="I want to build a library that implements a Fibonacci iterator in Rust. It should have a Cargo.toml and a src/lib.rs file that exports a Fibonacci struct that implements a Fibonacci Iterator.",
        orchestrator_config=OrchestratorConfiguration(
            github_base_branch=BASE_BRANCH,
            requirements_agent=RequirementsAgentConfig(
                use_stub=False,
                config=RequirementsConfiguration(
                    use_human_ai=True,
                    human_ai_product="""
                    This is a hobby project. A Rust cargo package that exports a Fibonacci struct that implements the Iterator trait.
                    This struct can be imported by its package users and used to create an iterator with the elements of the Fibonacci sequence.
                    """,
                ),
                stub_messages=MessageWheel([
                    "I have gathered the requirements for the project. This should be a simple cargo package the implements a Fibonacci iterator and exports it.",
                ]),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=False,
                stub_messages=MessageWheel([
                    "Architecture should follow cargo structure for a lib. with a Cargo.toml file, and src/lib.rs exporting a `Fibonacci` structs that implements the Iterator."
                ]),
            ),
            task_manager_agent=TaskManagerAgentConfig(
                use_stub=False,
                config=TaskManagerConfiguration(),
                stub_messages=MessageWheel([
                    "There's only one task for the coder: 1) Create a cargo package it should have a Cargo.toml and a src/lib.rs that exports a Fibonacci struct that implements a Fibonacci Iterator in Rust."
                ]),
            ),
            coder_new_pr_agent=SubAgentConfig(use_stub=False),
            coder_change_request_agent=SubAgentConfig(use_stub=False),
            reviewer_agent=CodeReviewerAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(["Everything looks correct."]),
            ),
            tester_agent=TesterAgentConfig(
                use_stub=False,
                stub_messages=MessageWheel(["I have tested the code and found no issues."]),
            ),
        ),
    )

def run(save_run = False) -> ScenarioRun:
    """Run Fibonacci scenario"""
    runner = ScenarioRunner(config=config(save_run))
    return asyncio.run(runner.run())

if __name__ == "__main__":
    run(True)
