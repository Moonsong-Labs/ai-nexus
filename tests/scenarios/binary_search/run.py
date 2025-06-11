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
from scenarios.binary_search import BASE_BRANCH
from scenarios.common import ScenarioConfig, ScenarioRun, ScenarioRunner

dotenv.load_dotenv()
logger = get_logger(__name__)


def config(save_run) -> ScenarioConfig:
    return ScenarioConfig(
        name="scenarios-binary-search",
        save_run=save_run,
        initial_prompt="I want to build a library that implements an efficient binary search in Rust.",
        orchestrator_config=OrchestratorConfiguration(
            github_base_branch=BASE_BRANCH,
            requirements_agent=RequirementsAgentConfig(
                use_stub=False,
                config=RequirementsConfiguration(
                    use_human_ai=True,
                    human_ai_product="""
                    This is a hobby project. A Rust cargo package that exports a generic binary search function. The function should take a list of items and the target item, and return the index where the item is found at, or nothing if the item is not present.
                    The function should be able to be imported by downstream packages and used to search efficiently over a list of items.
                    """,
                ),
                stub_messages=MessageWheel(
                    [
                        "I have gathered the requirements for the project. This should be a simple cargo package that implements an efficient binary search function generic over its items, before exporting it."
                    ]
                ),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=False,
                stub_messages=MessageWheel(
                    [
                        "Architecture should follow cargo structure for a lib. The library should export a generic binary search function, which has 2 arguments, needle and haystack, which returns an index only if the needle was found in the haystack using an efficient binary search algorithm. "
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
                        1) Create a cargo package. The package should have a Cargo.toml and src/lib.rs. The src/lib.rs file should export an efficient binary search function generic over its 2 arguments, needle and haystack. If the needle is found, the index should be returned, otherwise nothing should be returned.
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
                use_stub=False,
                stub_messages=MessageWheel(
                    [
                        "I have tested the code and found no issues.",
                    ]
                ),
            ),
        ),
    )


def run(save_run=False) -> ScenarioRun:
    """Run Binary Search scenario"""
    runner = ScenarioRunner(config=config(save_run))
    return asyncio.run(runner.run())


if __name__ == "__main__":
    run(True)
