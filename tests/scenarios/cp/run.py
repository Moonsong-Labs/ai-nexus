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
from scenarios.cp import BASE_BRANCH
from scenarios.runner import ScenarioConfig, ScenarioRun, ScenarioRunner

dotenv.load_dotenv()
logger = get_logger(__name__)

def config(save_run) -> ScenarioConfig:
    return ScenarioConfig(
        name="scenarios-cp",
        save_run=save_run,
        initial_prompt="I want to build a Rust CLI using clap that copies a file from <source> to <destination>.",
        orchestrator_config=OrchestratorConfiguration(
            github_base_branch=BASE_BRANCH,
            requirements_agent=RequirementsAgentConfig(
                use_stub=False,
                config=RequirementsConfiguration(
                    use_human_ai=True,
                    human_ai_product="""
                    This is a hobby project. Create a Rust CLI using clap that copies a file from <source> to <destination>.
                    """,
                ),
            ),
            architect_agent=ArchitectAgentConfig(use_stub=False),
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
        )
    )

def run(save_run=False) -> ScenarioRun:
    runner = ScenarioRunner(config=config(save_run))
    return asyncio.run(runner.run())

if __name__ == "__main__":
    run(True)
