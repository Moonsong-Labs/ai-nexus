import asyncio
import uuid

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from termcolor import colored

from orchestrator.configuration import (
    ArchitectAgentConfig,
    RequirementsAgentConfig,
    SubAgentConfig,
)
from orchestrator.configuration import Configuration as OrchestratorConfiguration
from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State

if __name__ == "__main__":
    orchestrator = OrchestratorGraph(
        agent_config=OrchestratorConfiguration(
            requirements_agent=RequirementsAgentConfig(
                use_stub=False,
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=False,
            ),
            coder_new_pr_agent=SubAgentConfig(
                use_stub=False,
            ),
            coder_change_request_agent=SubAgentConfig(
                use_stub=False,
            ),
        ),
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    async def _exec():
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

        return result

    result = asyncio.run(_exec())
    print(result)
