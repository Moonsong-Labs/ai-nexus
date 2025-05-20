"""Graphs that orchestrates a software project."""

import logging
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

from architect.configuration import (
    Configuration as ArchitectConfiguration,
)
from architect.graph import ArchitectGraph
from architect.state import State as ArchitectState
from coder.graph import CoderChangeRequestGraph, CoderNewPRGraph
from coder.state import State as CoderState
from common.components.github_mocks import maybe_mock_github
from common.components.github_tools import get_github_tools
from common.configuration import AgentConfiguration
from common.graph import AgentGraph
from orchestrator import stubs, tools
from orchestrator.configuration import (
    ArchitectAgentConfig,
    Configuration,
    RequirementsAgentConfig,
    SubAgentConfig,
)
from orchestrator.state import State
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)
from requirement_gatherer.graph import RequirementsGraph
from requirement_gatherer.state import State as RequirementsState
from task_manager.graph import TaskManagerGraph
from task_manager.state import State as TaskManagerState

logger = logging.getLogger(__name__)


def _create_orchestrate(
    agent_config: Configuration,
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    async def orchestrate(
        state: State, config: RunnableConfig, *, store: BaseStore
    ) -> dict:
        """Extract the user's state from the conversation and update the memory."""
        sys_prompt = agent_config.system_prompt.format(time=datetime.now().isoformat())

        msg = await llm.ainvoke(
            [SystemMessage(sys_prompt), *state.messages],
            config,
        )

        return {"messages": [msg]}

    return orchestrate


def _create_delegate_to(
    agent_config: Configuration, orchestrate: Coroutine[Any, Any, dict]
):
    async def delegate_to(
        state: State, config: RunnableConfig, store: BaseStore
    ) -> Literal[
        "__end__",
        "orchestrate",
        "requirements",
        "architect",
        "task_manager",
        "coder_new_pr",
        "coder_change_request",
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
                    return "architect"
                elif tool_call["args"]["to"] == "task_manager":
                    return "task_manager"
                elif tool_call["args"]["to"] == "coder_new_pr":
                    return "coder_new_pr"
                elif tool_call["args"]["to"] == "coder_change_request":
                    return "coder_change_request"
                elif tool_call["args"]["to"] == "tester":
                    return stubs.tester.__name__
                elif tool_call["args"]["to"] == "reviewer":
                    return stubs.reviewer.__name__
                # elif tool_call["args"]["to"] == "memorizer":
                #     return stubs.memorizer.__name__
                else:
                    raise ValueError

    return delegate_to


def _create_architect_node(
    agent_config: Configuration,
    architect_graph: ArchitectGraph,
    recursion_limit: int = 100,
):
    """Create an asynchronous architect node for the orchestrator graph.

    The returned function processes a tool call from the conversation state, invokes the architect graph with the tool call content as input, and returns a tool message containing the summarized architect linked to the original tool call ID.

    Args:
        architect_graph: The architect graph to invoke for architecting.
        recursion_limit: Maximum recursion depth allowed for the requirements graph (default is 100).

    Returns:
        An asynchronous function that architects the project and returns a dictionary with a tool message containing the summary.
    """

    async def architect(state: State, config: RunnableConfig, store: BaseStore):
        tool_call = state.messages[-1].tool_calls[0]
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await architect_graph.compiled_graph.ainvoke(
            ArchitectState(
                messages=[HumanMessage(content=tool_call["args"]["content"])]
            ),
            config_with_recursion,
        )

        return {
            "messages": [
                ToolMessage(
                    content=result["messages"][-1].content,
                    tool_call_id=tool_call["id"],
                )
            ]
        }

    return architect


def _create_requirements_node(
    agent_config: Configuration,
    requirements_graph: RequirementsGraph,
    recursion_limit: int = 100,
):
    """Create an asynchronous requirements node for the orchestrator graph.

    The returned function processes a tool call from the conversation state, invokes the requirements graph with the tool call content as input, and returns a tool message containing the summarized requirements linked to the original tool call ID.

    Args:
        requirements_graph: The requirements graph to invoke for requirements gathering.
        recursion_limit: Maximum recursion depth allowed for the requirements graph (default is 100).

    Returns:
        An asynchronous function that processes requirements extraction and returns a dictionary with a tool message containing the summary.
    """

    async def requirements(state: State, config: RunnableConfig, store: BaseStore):
        tool_call = state.messages[-1].tool_calls[0]
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await requirements_graph.compiled_graph.ainvoke(
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


def _create_coder_new_pr_node(
    coder_new_pr_graph: CoderNewPRGraph, recursion_limit: int = 100
):
    """Create an asynchronous coder_new_pr node for the orchestrator graph.

    The returned function processes a tool call from the conversation state, invokes the coder_new_pr graph with the tool call content as input, and returns a tool message containing the summarized requirements linked to the original tool call ID.

    Args:
        coder_new_pr_graph: The coder_new_pr graph to invoke for coder_new_pr gathering.
        recursion_limit: Maximum recursion depth allowed for the coder_new_pr graph (default is 100).

    Returns:
        An asynchronous function that processes the coding of new functionality and returns a dictionary with a tool message containing the changes.
    """

    async def coder_new_pr(state: State, config: RunnableConfig, store: BaseStore):
        tool_call = state.messages[-1].tool_calls[0]
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await coder_new_pr_graph.compiled_graph.ainvoke(
            CoderState(messages=[HumanMessage(content=tool_call["args"]["content"])]),
            config_with_recursion,
        )

        return {
            "messages": [
                ToolMessage(
                    content=result["messages"][-1].content,
                    tool_call_id=tool_call["id"],
                )
            ]
        }

    return coder_new_pr


def _create_coder_change_request_node(
    coder_change_request_graph: CoderChangeRequestGraph, recursion_limit: int = 100
):
    """Create an asynchronous coder_change_request node for the orchestrator graph.

    The returned function processes a tool call from the conversation state, invokes the coder_change_request graph with the tool call content as input, and returns a tool message containing the summarized requirements linked to the original tool call ID.

    Args:
        coder_change_request_graph: The coder_change_request graph to invoke for coder_change_request gathering.
        recursion_limit: Maximum recursion depth allowed for the coder_change_request graph (default is 100).

    Returns:
        An asynchronous function that processes the coding of changes and returns a dictionary with a tool message containing the changes.
    """

    async def coder_change_request(
        state: State, config: RunnableConfig, store: BaseStore
    ):
        tool_call = state.messages[-1].tool_calls[0]
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await coder_change_request_graph.compiled_graph.ainvoke(
            CoderState(messages=[HumanMessage(content=tool_call["args"]["content"])]),
            config_with_recursion,
        )

        return {
            "messages": [
                ToolMessage(
                    content=result["messages"][-1].content,
                    tool_call_id=tool_call["id"],
                )
            ]
        }

    return coder_change_request


def _create_task_manager_node(
    task_manager_graph: TaskManagerGraph, recursion_limit: int = 100
):
    """Create an asynchronous task_manager node for the orchestrator graph.

    The returned function processes a tool call from the conversation state, invokes the task_manager graph with the tool call content as input, and returns a tool message containing the summarized requirements linked to the original tool call ID.

    Args:
        task_manager_graph: The task_manager graph to invoke for task_manager gathering.
        recursion_limit: Maximum recursion depth allowed for the task_manager graph (default is 100).

    Returns:
        An asynchronous function that processes the task_manager and returns a dictionary with a tool message containing the changes.
    """

    async def task_manager(state: State, config: RunnableConfig, store: BaseStore):
        tool_call = state.messages[-1].tool_calls[0]
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await task_manager_graph.compiled_graph.ainvoke(
            TaskManagerState(
                messages=[HumanMessage(content=tool_call["args"]["content"])]
            ),
            config_with_recursion,
        )

        return {
            "messages": [
                ToolMessage(
                    content=result["messages"][-1].content,
                    tool_call_id=tool_call["id"],
                )
            ]
        }

    return task_manager


class OrchestratorGraph(AgentGraph):
    """Orchestrator graph."""

    _agent_config: Configuration

    def __init__(
        self,
        *,
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize the OrchestratorGraph with agent configuration, optional checkpointer, and store.

        Args:
            agent_config: Optional configuration for the orchestrator agent. If not provided, a default configuration is used.
            checkpointer: Optional checkpointer for managing workflow state persistence.
            store: Optional storage backend for conversation or workflow data.
        """
        super().__init__(
            name="Orchestrator",
            agent_config=agent_config or Configuration(),
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """Construct and returns the orchestrator state graph for project workflow management.

        Initializes all nodes and edges representing the orchestrator, requirements gathering, and role-specific stubs, wiring them into a StateGraph that defines the control flow for the orchestration process.
        """
        # Initialize the language model to be used for memory extraction
        llm = init_chat_model(self._agent_config.model).bind_tools(
            [tools.Delegate, tools.store_memory]
        )
        orchestrate = _create_orchestrate(self._agent_config, llm)
        requirements_graph = (
            stubs.RequirementsGathererStub(
                agent_config=self._agent_config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
            if self._agent_config.requirements_agent.use_stub
            else RequirementsGraph(
                agent_config=self._agent_config.requirements_agent.config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
        )
        github_source = maybe_mock_github()
        github_tools = get_github_tools(github_source)
        coder_new_pr_graph = (
            stubs.CoderNewPRStub(
                agent_config=self._agent_config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
            if self._agent_config.coder_new_pr_agent.use_stub
            else CoderNewPRGraph(
                agent_config=self._agent_config.coder_new_pr_agent.config,
                checkpointer=self._checkpointer,
                store=self._store,
                github_tools=github_tools,
            )
        )
        coder_change_request_graph = (
            stubs.CoderChangeRequestStub(
                agent_config=self._agent_config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
            if self._agent_config.coder_change_request_agent.use_stub
            else CoderChangeRequestGraph(
                agent_config=self._agent_config.coder_change_request_agent.config,
                checkpointer=self._checkpointer,
                store=self._store,
                github_tools=github_tools,
            )
        )
        architect_graph = (
            stubs.ArchitectStub(
                agent_config=self._agent_config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
            if self._agent_config.architect_agent.use_stub
            else ArchitectGraph(
                agent_config=self._agent_config.architect_agent.config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
        )
        task_manager_graph = (
            stubs.TaskManagerStub(
                agent_config=self._agent_config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
            if self._agent_config.task_manager_agent.use_stub
            else TaskManagerGraph(
                agent_config=self._agent_config.task_manager_agent.config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
        )
        requirements = _create_requirements_node(self._agent_config, requirements_graph)
        architect = _create_architect_node(self._agent_config, architect_graph)
        task_manager = _create_task_manager_node(task_manager_graph)
        coder_new_pr = _create_coder_new_pr_node(coder_new_pr_graph)
        coder_change_request = _create_coder_change_request_node(
            coder_change_request_graph
        )
        delegate_to = _create_delegate_to(self._agent_config, orchestrate)

        # Create the graph + all nodes
        builder = StateGraph(State, config_schema=Configuration)

        # Define the flow of the memory extraction process
        builder.add_node(orchestrate)
        builder.add_node(requirements)
        builder.add_node(architect)
        builder.add_node(task_manager)
        builder.add_node(coder_new_pr)
        builder.add_node(coder_change_request)
        builder.add_node(stubs.tester)
        builder.add_node(stubs.reviewer)
        builder.add_node(stubs.memorizer)

        builder.add_edge(START, orchestrate.__name__)
        builder.add_conditional_edges(
            orchestrate.__name__,
            delegate_to,
        )
        builder.add_edge(requirements.__name__, orchestrate.__name__)
        builder.add_edge(architect.__name__, orchestrate.__name__)
        builder.add_edge(task_manager.__name__, orchestrate.__name__)
        builder.add_edge(coder_new_pr.__name__, orchestrate.__name__)
        builder.add_edge(coder_change_request.__name__, orchestrate.__name__)
        builder.add_edge(stubs.tester.__name__, orchestrate.__name__)
        builder.add_edge(stubs.reviewer.__name__, orchestrate.__name__)
        builder.add_edge(stubs.memorizer.__name__, orchestrate.__name__)

        return builder


# For langsmith
graph = OrchestratorGraph(
    agent_config=Configuration(
        requirements_agent=RequirementsAgentConfig(
            use_stub=False, config=RequirementsConfiguration(use_human_ai=False)
        ),
        architect_agent=ArchitectAgentConfig(
            use_stub=False, config=ArchitectConfiguration(use_human_ai=False)
        ),
        coder_new_pr_agent=SubAgentConfig(use_stub=False, config=AgentConfiguration()),
        coder_change_request_agent=SubAgentConfig(
            use_stub=False, config=AgentConfiguration()
        ),
    )
).compiled_graph

__all__ = ["OrchestratorGraph"]
