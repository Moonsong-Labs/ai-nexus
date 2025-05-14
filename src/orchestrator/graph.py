"""Graphs that orchestrates a software project."""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Coroutine, Literal, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.config import BaseConfiguration
from common.graph import AgentGraph
from orchestrator import stubs, tools
from orchestrator.configuration import Configuration
from orchestrator.state import State
from requirement_gatherer.graph import RequirementsGathererGraph
from requirement_gatherer.state import State as RequirementsState

logger = logging.getLogger(__name__)


def _create_orchestrate(
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    async def orchestrate(
        state: State, config: RunnableConfig, *, store: BaseStore
    ) -> dict:
        """Extract the user's state from the conversation and update the memory."""
        sys_prompt = config["configurable"]["system_prompt"].format(
            time=datetime.now().isoformat()
        )

        msg = await llm.ainvoke(
            [SystemMessage(sys_prompt), *state.messages],
            config,
        )

        return {"messages": [msg]}

    return orchestrate


def _create_delegate_to(orchestrate: Coroutine[Any, Any, dict]):
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
                    return "requirements"
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

    return delegate_to


def _create_requirements_node(
    requirements_graph: RequirementsGathererGraph, recursion_limit: int = 100
):
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


@dataclass(kw_only=True)
class AgentConfig:
    use_stub: bool = True


class RequirementsAgentConfig(AgentConfig):
    use_human_ai: bool = False


@dataclass(kw_only=True)
class AgentsConfig:
    requirements: RequirementsAgentConfig = field(
        default_factory=RequirementsAgentConfig
    )
    architect: AgentConfig = field(default_factory=AgentConfig)
    coder: AgentConfig = field(default_factory=AgentConfig)
    tester: AgentConfig = field(default_factory=AgentConfig)
    reviewer: AgentConfig = field(default_factory=AgentConfig)


class OrchestratorGraph(AgentGraph):
    """Orchestrator graph."""

    def __init__(
        self,
        *,
        agents_config: Optional[AgentsConfig] = None,
        base_config: Optional[BaseConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize."""
        super().__init__(base_config, checkpointer, store)
        self._name = "Orchestrator"
        self._config = Configuration(**asdict(self._base_config))
        self._agents_config = agents_config or AgentsConfig()

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        # Initialize the language model to be used for memory extraction
        llm = init_chat_model().bind_tools([tools.Delegate, tools.store_memory])
        orchestrate = _create_orchestrate(llm)
        requirements_graph = (
            stubs.RequirementsGathererStub(
                config=self._config, checkpointer=self._checkpointer, store=self._store
            )
            if self._agents_config.requirements.use_stub
            else RequirementsGathererGraph(
                use_human_ai=self._agents_config.requirements.use_human_ai,
                base_config=self._base_config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
        )
        requirements = _create_requirements_node(requirements_graph)
        delegate_to = _create_delegate_to(orchestrate)

        # Create the graph + all nodes
        builder = StateGraph(State, config_schema=Configuration)

        # Define the flow of the memory extraction process
        builder.add_node(orchestrate)
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
        builder.add_edge(requirements.__name__, orchestrate.__name__)
        builder.add_edge(stubs.architect.__name__, orchestrate.__name__)
        builder.add_edge(stubs.coder.__name__, orchestrate.__name__)
        builder.add_edge(stubs.tester.__name__, orchestrate.__name__)
        builder.add_edge(stubs.reviewer.__name__, orchestrate.__name__)
        builder.add_edge(stubs.memorizer.__name__, orchestrate.__name__)

        return builder


# For langsmith
_agents_config = AgentsConfig()
_agents_config.requirements.use_stub = False
_agents_config.requirements.use_human_ai = False
graph = OrchestratorGraph(agents_config=_agents_config).compiled_graph

__all__ = ["OrchestratorGraph"]
