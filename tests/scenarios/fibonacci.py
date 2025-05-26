import asyncio
import uuid

import dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from termcolor import colored

from common.logging import get_logger
from orchestrator.configuration import (
    ArchitectAgentConfig,
    RequirementsAgentConfig,
    SubAgentConfig,
    TaskManagerAgentConfig,
    TaskManagerConfiguration,
)
from orchestrator.configuration import Configuration as OrchestratorConfiguration
from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State
from orchestrator.stubs import MessageWheel

dotenv.load_dotenv()
logger = get_logger(__name__)

BASE_BRANCH = "fibonacci-base"

if __name__ == "__main__":
    orchestrator = OrchestratorGraph(
        agent_config=OrchestratorConfiguration(
            github_base_branch=BASE_BRANCH,
            requirements_agent=RequirementsAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "I have gathered the requirements for the project. This should be a simple cargo package the implements a Fibonacci iterator and exports it.",
                    ]
                ),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "Architecture should follow cargo structure for a lib. lib should export a Fibonacci iterator.",
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
                     1) Create skeleton for a cargo package that exports a Fibonacci Iterator in Rust.
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
            reviewer_agent=SubAgentConfig(
                use_stub=True,
                stub_messages=MessageWheel(
                    [
                        "Everything looks correct.",
                    ]
                ),
            ),
            tester_agent=SubAgentConfig(
                use_stub=True,
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
        logger.info("Starting execution")
        config = orchestrator.create_runnable_config(
            RunnableConfig(
                recursion_limit=250,
                configurable={
                    "thread_id": str(uuid.uuid4()),
                },
            )
        )
        result = await orchestrator.compiled_graph.ainvoke(
            State(
                messages=HumanMessage(
                    content="I want to build a library that implements a Fibonacci iterator in Rust"
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

        logger.info("Execution complete")
        return result

    result = asyncio.run(_exec())
    print(result)
