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
from scenarios.runner import ScenarioConfig, ScenarioRun, ScenarioRunner
from scenarios.stack import BASE_BRANCH

dotenv.load_dotenv()
logger = get_logger(__name__)


def config(save_run) -> ScenarioConfig:
    """Create configuration for Stack scenario"""
    return ScenarioConfig(
        name="scenarios-stack",
        save_run=save_run,
        initial_prompt="I want to build a library that implements a generic stack (LIFO data structure) in Rust",
        orchestrator_config=OrchestratorConfiguration(
            github_base_branch=BASE_BRANCH,
            requirements_agent=RequirementsAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "I have gathered the requirements for the project. This should be a simple cargo package that implements a generic stack (LIFO data structure) in Rust with basic operations like push, pop, peek, and is_empty.",
                    ]
                ),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "Architecture should follow cargo structure for a lib. The library should export a generic Stack struct with methods for push, pop, peek, is_empty, and new. Include proper error handling for pop and peek operations on empty stacks.",
                    ]
                ),
            ),
            task_manager_agent=TaskManagerAgentConfig(
                use_stub=True,
                config=TaskManagerConfiguration(),
                stub_messages=MessageWheel(
                    [
                        """
                    There's only one task for the coder:
                     1) Create a cargo package that implements a generic Stack data structure in Rust with push, pop, peek, is_empty, and new methods.
                    """
                    ]
                ),
            ),
            coder_new_pr_agent=SubAgentConfig(
                use_stub=False,
            ),
            coder_change_request_agent=SubAgentConfig(
                use_stub=False,
            ),
            reviewer_agent=CodeReviewerAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "Everything looks correct.",
                    ]
                ),
            ),
            tester_agent=TesterAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "I have tested the code and found no issues.",
                    ]
                ),
            ),
        ),
    )


def run(save_run=False) -> ScenarioRun:
    """Run Stack scenario"""
    runner = ScenarioRunner(config=config(save_run))
    return asyncio.run(runner.run())


if __name__ == "__main__":
    run(True)
