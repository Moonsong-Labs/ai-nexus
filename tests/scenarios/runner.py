"""Contains abstractions to run scenarios."""

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers.langchain import wait_for_all_tracers
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from termcolor import colored

from common.logging import get_logger
from orchestrator.configuration import Configuration as OrchestratorConfiguration
from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State

logger = get_logger(__name__)


class CoderPR(TypedDict):
    pr_number: int
    branch: str


class ScenarioRun(TypedDict):
    run_name: str
    run_id: str
    pr_number: int
    branch: str


@dataclass
class ScenarioConfig:
    """Configuration for a scenario run"""

    name: str
    initial_prompt: str
    orchestrator_config: OrchestratorConfiguration
    recursion_limit: int = 250
    save_run: bool = True


class ScenarioRunner:
    """Standardized scenario runner"""

    def __init__(self, config: ScenarioConfig):
        self.config = config
        self.run_id = str(uuid.uuid4())

    async def run(self) -> ScenarioRun:
        """Execute the scenario"""
        logger.info(f"Run name: {self.config.name}")
        logger.info(f"Run id: {self.run_id}")

        # Create orchestrator with provided configuration
        orchestrator = self._create_orchestrator()

        try:
            result = await self._execute_scenario(orchestrator)

            run_info = self._extract_run_info(result)

            if self.config.save_run:
                self._save_scenario(run_info)

            return run_info

        finally:
            wait_for_all_tracers()

    def _create_orchestrator(self) -> OrchestratorGraph:
        """Create orchestrator with standard components"""
        return OrchestratorGraph(
            agent_config=self.config.orchestrator_config,
            checkpointer=InMemorySaver(),
            store=InMemoryStore(),
        )

    async def _handle_interrupts(self, orchestrator_graph, config):
        result = None
        while True:
            graph_state = await orchestrator_graph.aget_state(config)
            if graph_state.interrupts:
                interrupt = graph_state.interrupts[0]
                response = input(
                    f"\n{'-' * 50}\n{colored('requirements', 'green')}: {colored(interrupt.value['query'], 'light_grey')}\n\n{colored('Answer', 'yellow')}: "
                )
                result = await orchestrator_graph.ainvoke(
                    Command(resume=response), config=config
                )
            else:
                break
        return result

    async def _execute_scenario(self, orchestrator: OrchestratorGraph) -> dict:
        """Execute the scenario with standard flow"""
        logger.debug("Starting execution")

        config = orchestrator.create_runnable_config(
            RunnableConfig(
                recursion_limit=self.config.recursion_limit,
                run_name=self.config.name,
                run_id=self.run_id,
                configurable={"thread_id": str(uuid.uuid4())},
            )
        )

        result = await orchestrator.compiled_graph.ainvoke(
            State(messages=HumanMessage(content=self.config.initial_prompt)),
            config=config,
        )

        # Handle interrupts
        interrupt_result = await self._handle_interrupts(
            orchestrator.compiled_graph, config
        )
        if interrupt_result is not None:
            result = interrupt_result

        logger.debug("Execution complete")
        return result

    def _save_scenario(self, result):
        logger.info(result)
        scenario_runs_dir = (
            Path(os.path.dirname(__file__))
            / Path("scenario_runs")
            / Path(self.config.name)
        )
        os.makedirs(scenario_runs_dir, exist_ok=True)

        run_file = scenario_runs_dir / Path(f"{result['run_id']}.json")
        with open(run_file, "w") as f:
            json.dump(result, f, indent=1)
        logger.info(f"Stored run results in {run_file}")

    def _extract_run_info(self, result: dict) -> ScenarioRun:
        """Extract PR information from results"""
        logger.debug("Extracting PR number and branch name")

        coder_output = self._get_coder_output(result)
        pr_info = self._parse_pr_info(coder_output)

        return ScenarioRun(
            run_name=self.config.name,
            run_id=self.run_id,
            pr_number=pr_info["pr_number"],
            branch=pr_info["branch"],
        )

    def _get_coder_output(self, result: dict) -> str:
        """Extract coder output from results"""
        coder_output = ""
        for message in result["messages"]:
            if message.name == "coder_new_pr":
                coder_output += message.content

        if not coder_output:
            raise ValueError("No 'coder_new_pr' message found; cannot extract PR info")

        logger.debug(f"Coder output: {coder_output}")
        return coder_output

    def _parse_pr_info(self, coder_output: str) -> dict:
        """Parse PR information from coder output"""
        llm = init_chat_model(
            "google_genai:gemini-2.0-flash", temperature=0
        ).with_structured_output(CoderPR)

        try:
            pr_info = llm.invoke(
                f"From the following output, extract the PR number and branch name: {coder_output}"
            )
            logger.debug(f"PR: {pr_info}")
            return pr_info
        except ValueError as e:
            raise RuntimeError(
                "Failed to parse PR number and branch from coder output"
            ) from e
