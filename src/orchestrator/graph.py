"""Graphs that orchestrates a software project."""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.types import Checkpointer, Command, interrupt

from common import config, utils
from orchestrator import configuration, prompts, stubs, tools
from orchestrator.state import State
from requirement_gatherer.graph_v2 import RequirementsGathererGraph
from requirement_gatherer.graph_v2 import builder as requirements_gatherer_builder
from requirement_gatherer.state import State as RequirementsState

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
model_orchestrator = init_chat_model()


async def orchestrate(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    sys_msg = configurable.system_prompt.format(time=datetime.now().isoformat())

    msg = await model_orchestrator.bind_tools(
        [tools.Delegate, tools.store_memory]
    ).ainvoke(
        [SystemMessage(sys_msg), *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )

    return {"messages": [msg]}


async def store_memory(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    sys = configurable.system_prompt.format(time=datetime.now().isoformat())

    msg = await model_orchestrator.bind_tools([tools.Delegate, tools.Memory]).ainvoke(
        [SystemMessage(sys), *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )

    return {"messages": [msg]}


checkpointer = InMemorySaver()
store = InMemoryStore()
requirements_gatherer = requirements_gatherer_builder.compile(
    name="Requirements Gatherer", checkpointer=checkpointer, store=store
)
requirements_gatherer = requirements_gatherer_builder.compile(
    name="Requirements Gatherer", checkpointer=checkpointer, store=store
)


async def delegate_to(
    state: State, config: RunnableConfig, store: BaseStore
) -> Literal[
    "__end__",
    "orchestrate",
    "requirements",
    "architect",
    "coder",
    "tester",
    "reviewer",
    "memorizer",
]:
    """Determine the next step based on the presence of tool calls."""
    message = state.messages[-1]
    if len(message.tool_calls) == 0:
        return END
    else:
        tool_call = message.tool_calls[0]
        if tool_call["name"] == "store_memory":
            return stubs.memorizer.__name__
        else:
            if tool_call["args"]["to"] == "orchestrator":
                return orchestrate.__name__
            elif tool_call["args"]["to"] == "requirements":
                return stubs.requirements.__name__
            elif tool_call["args"]["to"] == "architect":
                return stubs.architect.__name__
            elif tool_call["args"]["to"] == "coder":
                return stubs.coder.__name__
            elif tool_call["args"]["to"] == "tester":
                return stubs.tester.__name__
            elif tool_call["args"]["to"] == "reviewer":
                return stubs.reviewer.__name__
            # elif tool_call["args"]["to"] == "memorizer":
            #     return stubs.memorizer.__name__
            else:
                raise ValueError


async def requirements(state: State, config: RunnableConfig, store: BaseStore):
    tool_call = state.messages[-1].tool_calls[0]
    message = tool_call["args"]["content"]
    config["recursion_limit"] = 560
    result = await requirements_gatherer.ainvoke(
        RequirementsState(
            messages=[HumanMessage(content=tool_call["args"]["content"])]
        ),
        config,
    )

    return {
        "messages": [
            ToolMessage(
                content=result["summary"],
                tool_call_id=tool_call["id"],
            )
        ]
    }


def create_requirements(requirements_graph: RequirementsGathererGraph, recursion_limit: int = 100):
    async def requirements(state: State, config: RunnableConfig, store: BaseStore):
        tool_call = state.messages[-1].tool_calls[0]
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit
        
        result = await requirements_graph.ainvoke(
            RequirementsState(
                messages=[HumanMessage(content=tool_call["args"]["content"])]
            ),
            config_with_recursion,
        )

        return {
            "messages": [
                ToolMessage(
                    content=result["summary"],
                    tool_call_id=tool_call["id"],
                )
            ]
        }

    return requirements


# Create the graph + all nodes
builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(orchestrate)
# builder.add_node(store_memory)
# builder.add_node(stubs.requirements)
builder.add_node(requirements)
builder.add_node(stubs.architect)
builder.add_node(stubs.coder)
builder.add_node(stubs.tester)
builder.add_node(stubs.reviewer)
builder.add_node(stubs.memorizer)

builder.add_edge(START, orchestrate.__name__)
builder.add_conditional_edges(
    orchestrate.__name__,
    delegate_to,
)
builder.add_edge(stubs.requirements.__name__, orchestrate.__name__)
builder.add_edge(stubs.architect.__name__, orchestrate.__name__)
builder.add_edge(stubs.coder.__name__, orchestrate.__name__)
builder.add_edge(stubs.tester.__name__, orchestrate.__name__)
builder.add_edge(stubs.reviewer.__name__, orchestrate.__name__)
builder.add_edge(stubs.memorizer.__name__, orchestrate.__name__)

# graph = builder.compile(name="Orchestrator")
graph = builder.compile(name="Orchestrator", checkpointer=checkpointer, store=store)


__all__ = ["graph"]


@dataclass(kw_only=True)
class Configuration(config.Configuration):
    """Main configuration class for the memory graph system."""

    system_prompt: str = prompts.get_prompt()


class OrchestratorGraph:
    def __init__(
        self,
        base_config: config.Configuration,
        checkpointer: Checkpointer = None,
        store: Optional[BaseStore] = None,
    ):
        self._config = Configuration(**asdict(base_config))
        self._checkpointer = checkpointer
        self._store = store
        self._compiled_graph = None
        self._requirements_graph = RequirementsGathererGraph(
            base_config, checkpointer, store
        ).compile()

        # Create the graph + all nodes
        builder = StateGraph(State, config_schema=configuration.Configuration)

        # Define the flow of the memory extraction process
        builder.add_node(orchestrate)
        # builder.add_node(store_memory)
        # builder.add_node(stubs.requirements)
        builder.add_node(create_requirements(self._requirements_graph))
        # builder.add_node(requirements)
        builder.add_node(stubs.architect)
        builder.add_node(stubs.coder)
        builder.add_node(stubs.tester)
        builder.add_node(stubs.reviewer)
        builder.add_node(stubs.memorizer)

        builder.add_edge(START, orchestrate.__name__)
        builder.add_conditional_edges(
            orchestrate.__name__,
            delegate_to,
        )
        builder.add_edge(stubs.requirements.__name__, orchestrate.__name__)
        builder.add_edge(stubs.architect.__name__, orchestrate.__name__)
        builder.add_edge(stubs.coder.__name__, orchestrate.__name__)
        builder.add_edge(stubs.tester.__name__, orchestrate.__name__)
        builder.add_edge(stubs.reviewer.__name__, orchestrate.__name__)
        builder.add_edge(stubs.memorizer.__name__, orchestrate.__name__)

        self._builder = builder
        self._compiled_graph = None
        self._config = Configuration(**asdict(base_config))

    @property
    def builder(self):
        return self._builder

    def compile(
        self,
        *,
        with_store=True,
    ) -> CompiledStateGraph:
        if with_store:
            self._compiled_graph = self._builder.compile(
                name="Orchestrator", checkpointer=self._checkpointer, store=self._store
            )
        else:
            self._compiled_graph = self._builder.compile(name="Orchestrator")

        return self

    async def ainvoke(self, state: State, config: RunnableConfig | None = None):
        new_config = None
        if config is not None:
            new_config = RunnableConfig(**config)
            for k, v in asdict(self._config).items():
                if k not in new_config["configurable"]:
                    new_config["configurable"][k] = v
        return await self._compiled_graph.ainvoke(state, new_config)
