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
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)
from scenarios.lru_cache import BASE_BRANCH
from scenarios.common import ScenarioConfig, ScenarioRun, ScenarioRunner

dotenv.load_dotenv()
logger = get_logger(__name__)


def config(save_run) -> ScenarioConfig:
    return ScenarioConfig(
        name="scenarios-lru-cache",
        save_run=save_run,
        initial_prompt="I want to build a library that implements an least recently used (LRU) cache in Rust.",
        orchestrator_config=OrchestratorConfiguration(
            github_base_branch=BASE_BRANCH,
            requirements_agent=RequirementsAgentConfig(
                use_stub=False,
                config=RequirementsConfiguration(
                    use_human_ai=True,
                    human_ai_product="""
                    This is a hobby project. A Rust cargo package that exports a generic least recently used (LRU) cache struct.
                    The struct should have three functions: new, that receives the capacity and returns the struct; put, that receives self, key and value and puts the value into the key; and get, that receives self and key and returns the value.
                    If there's an overflow in the capacity, the least used value is to be deleted in favor of the new one.
                    """,
                ),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=False
            ),
            task_manager_agent=TaskManagerAgentConfig(
                use_stub=False,
                config=TaskManagerConfiguration(),
            ),
            coder_new_pr_agent=SubAgentConfig(
                use_stub=False,
            ),
            coder_change_request_agent=SubAgentConfig(
                use_stub=False,
            ),
            reviewer_agent=CodeReviewerAgentConfig(
                use_stub=False,
            ),
            tester_agent=TesterAgentConfig(
                use_stub=False,
            ),
        ),
    )


def run(save_run=False) -> ScenarioRun:
    """Run LRU cache scenario"""
    runner = ScenarioRunner(config=config(save_run))
    return asyncio.run(runner.run())


if __name__ == "__main__":
    run(True)
