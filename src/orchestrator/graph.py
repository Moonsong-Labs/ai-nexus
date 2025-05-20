"""Graphs that orchestrates a software project."""

import logging
from datetime import datetime
from typing import Any, Coroutine, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from architect.configuration import (
    Configuration as ArchitectConfiguration,
)
from architect.graph import ArchitectGraph
from coder.graph import CoderChangeRequestGraph, CoderNewPRGraph
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
    TaskManagerAgentConfig,
)
from orchestrator.state import State
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)
from requirement_gatherer.graph import RequirementsGraph
from requirement_gatherer.state import State as RequirementsState
from task_manager.graph import TaskManagerGraph
from task_manager.state import State as TaskManagerState
from task_manager.configuration import (
    Configuration as TaskManagerConfiguration,
)

logger = logging.getLogger(__name__)


def _create_orchestrator(
    agent_config: Configuration,
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    async def orchestrator(
        state: State, config: RunnableConfig, *, store: BaseStore
    ) -> dict:
        """Extract the user's state from the conversation and update the memory."""
        sys_prompt = agent_config.system_prompt.format(time=datetime.now().isoformat())

        msg = await llm.ainvoke(
            [SystemMessage(sys_prompt), *state.messages],
            config,
        )

        return {"messages": [msg]}

    return orchestrator


def _create_orchestrate_condition(
    agent_config: Configuration,
    orchestrator: Coroutine[Any, Any, dict],
    tool_node: ToolNode,
):
    """Create an asynchronous function to determine the next step in the requirements gathering graph.

    The returned function inspects the conversation state to decide whether to route to a tool node, end the process, or continue the conversation with the model.
    """

    async def orchestrate(state: State, config: RunnableConfig):
        if state.messages and state.messages[-1].tool_calls:
            return tool_node.name
        elif state.summary:
            return END
        else:
            return orchestrator.__name__

    return orchestrate


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
        github_tools = get_github_tools(maybe_mock_github())
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
        tester_graph = (
            stubs.TesterStub(
                agent_config=self._agent_config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
            if self._agent_config.tester_agent.use_stub
            else TesterAgentGraph(
                agent_config=self._agent_config.tester_agent.config,
                checkpointer=self._checkpointer,
                store=self._store,
            )
        )
        code_reviewer_graph = stubs.CodeReviewerStub(
            agent_config=self._agent_config,
            checkpointer=self._checkpointer,
            store=self._store,
        )

        all_tools = [
            tools.create_requirements_tool(self._agent_config, requirements_graph),
            tools.create_architect_tool(self._agent_config, architect_graph),
            tools.create_coder_new_pr_tool(self._agent_config, coder_new_pr_graph),
            tools.create_coder_change_request_tool(
                self._agent_config, coder_change_request_graph
            ),
            tools.create_tester_tool(self._agent_config, tester_graph),
            tools.create_code_reviewer_tool(self._agent_config, code_reviewer_graph),
            tools.memorize,
            tools.summarize,
        ]
        tool_node = ToolNode(all_tools, name="tools")
        llm = init_chat_model(self._agent_config.model).bind_tools(all_tools)
        orchestrator = _create_orchestrator(self._agent_config, llm)
        orchestrate_condition = _create_orchestrate_condition(
            self._agent_config, orchestrator, tool_node
        )

        # Create the graph + all nodes
        builder = StateGraph(State, config_schema=Configuration)
        builder.add_node(orchestrator)
        builder.add_node(tool_node.name, tool_node)
        builder.add_edge(START, orchestrator.__name__)
        builder.add_edge(tool_node.name, orchestrator.__name__)
        builder.add_conditional_edges(
            orchestrator.__name__,
            orchestrate_condition,
            [tool_node.name, orchestrator.__name__, END],
        )

        return builder


# For langsmith
graph = OrchestratorGraph(
    agent_config=Configuration(
        requirements_agent=RequirementsAgentConfig(
            use_stub=False, config=RequirementsConfiguration(use_human_ai=False)
        ),
        architect_agent=ArchitectAgentConfig(
            use_stub=False, config=ArchitectConfiguration()
        ),
        task_manager_agent=TaskManagerAgentConfig(
            use_stub=False, config=TaskManagerConfiguration(use_human_ai=False)
        ),
        coder_new_pr_agent=SubAgentConfig(use_stub=False, config=AgentConfiguration()),
        coder_change_request_agent=SubAgentConfig(
            use_stub=False, config=AgentConfiguration()
        ),
    )
).compiled_graph

__all__ = ["OrchestratorGraph"]
