import asyncio
import json
import os
import uuid
from typing import TypedDict

import dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers.langchain import wait_for_all_tracers
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from termcolor import colored

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
from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State
from orchestrator.stubs import MessageWheel
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)
from scenarios.fibonacci import BASE_BRANCH

dotenv.load_dotenv()
logger = get_logger(__name__)


class CoderPR(TypedDict):
    pr_number: int
    branch: str


class ScenarioRun(TypedDict):
    run_name: str
    run_id: str
    pr_number: int
    branch: str


def run():
    """Run scenario"""
    run_name = "scenarios-fibonacci"
    run_id = str(uuid.uuid4())

    logger.info(f"Run name: {run_name}")
    logger.info(f"Run id: {run_id}")

    orchestrator = OrchestratorGraph(
        agent_config=OrchestratorConfiguration(
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
                stub_messages=MessageWheel(
                    [
                        "I have gathered the requirements for the project. This should be a simple cargo package the implements a Fibonacci iterator and exports it.",
                    ]
                ),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=False,
                stub_messages=MessageWheel(
                    [
                        "Architecture should follow cargo structure for a lib. with a Cargo.toml file, and src/lib.rs exporting a `Fibonacci` structs that implements the Iterator."
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
                     1) Create a cargo package it should have a Cargo.toml and a src/lib.rs that exports a Fibonacci struct that implements a Fibonacci Iterator in Rust.
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
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    async def _exec():
        logger.debug("Starting execution")

        config = orchestrator.create_runnable_config(
            RunnableConfig(
                recursion_limit=250,
                run_name=run_name,
                run_id=run_id,
                configurable={
                    "thread_id": str(uuid.uuid4()),
                },
            )
        )

        result = await orchestrator.compiled_graph.ainvoke(
            State(
                messages=HumanMessage(
                    content="I want to build a library that implements a Fibonacci iterator in Rust. It should have a Cargo.toml and a src/lib.rs file that exports a Fibonacci struct that implements a Fibonacci Iterator."
                )
            ),
            config=config,
        )

        # Handle interrupts
        while True:
            graph_state = await orchestrator.compiled_graph.aget_state(config)
            if graph_state.interrupts:
                interrupt = graph_state.interrupts[0]
                response = input(
                    f"\n{'-' * 50}\n{colored('requirements', 'green')}: {colored(interrupt.value['query'], 'light_grey')}\n\n{colored('Answer', 'yellow')}: "
                )
                result = await orchestrator.compiled_graph.ainvoke(
                    Command(resume=response), config=config
                )
            else:
                break

        logger.debug("Execution complete")
        return result

    try:
        result = asyncio.run(_exec())
        logger.debug(result)
    finally:
        wait_for_all_tracers()

    logger.debug("Extracting PR number and branch name")
    coder_output = ""
    for m in result["messages"]:
        if m.name == "coder_new_pr":
            coder_output += m.content
    logger.debug(f"Coder output: {coder_output}")

    if not coder_output:
        raise ValueError("No 'coder_new_pr' message found; cannot extract PR info")

    llm = init_chat_model(
        "google_genai:gemini-2.0-flash", temperature=0
    ).with_structured_output(CoderPR)

    try:
        pr = llm.invoke(
            f"From the following output, extract the PR number and branch name: {coder_output}"
        )
    except ValueError as e:
        raise RuntimeError(
            "Failed to parse PR number and branch from coder output"
        ) from e

    logger.debug(f"PR: {pr}")

    run = ScenarioRun(
        run_name=run_name,
        run_id=run_id,
        pr_number=pr["pr_number"],
        branch=pr["branch"],
    )

    return run


if __name__ == "__main__":
    ret = run()
    logger.info(ret)
    # Store run results
    scenario_runs_dir = os.path.join(os.path.dirname(__file__), "scenario_runs")
    os.makedirs(scenario_runs_dir, exist_ok=True)

    run_file = os.path.join(scenario_runs_dir, f"{ret['run_id']}.json")
    with open(run_file, "w") as f:
        json.dump(ret, f, indent=1)
    logger.info(f"Stored run results in {run_file}")
