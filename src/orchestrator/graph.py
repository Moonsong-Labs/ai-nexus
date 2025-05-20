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
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.graph import AgentGraph
from orchestrator import stubs, tools
from orchestrator.configuration import (
    Configuration,
    RequirementsAgentConfig,
)
from orchestrator.state import State
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)
from requirement_gatherer.graph import RequirementsGraph
from requirement_gatherer.state import State as RequirementsState

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


# def _create_delegate_to(
#     agent_config: Configuration, orchestrate: Coroutine[Any, Any, dict]
# ):
#     @tool
#     async def delegate_to(
#         state: State, config: RunnableConfig, store: BaseStore
#     ) -> Literal[
#         "__end__",
#         "orchestrate",
#         "requirements",
#         "architect",
#         "coder",
#         "tester",
#         "reviewer",
#         "memorizer",
#     ]:
#         """Determine the next step based on the presence of tool calls."""
#         message = state.messages[-1]
#         if len(message.tool_calls) == 0:
#             return END
#         else:
#             tool_call = message.tool_calls[0]
#             if tool_call["name"] == "store_memory":
#                 return stubs.memorizer.__name__
#             else:
#                 if tool_call["args"]["to"] == "orchestrator":
#                     return orchestrate.__name__
#                 elif tool_call["args"]["to"] == "requirements":
#                     return "requirements"
#                 elif tool_call["args"]["to"] == "architect":
#                     return stubs.architect.__name__
#                 elif tool_call["args"]["to"] == "coder":
#                     return stubs.coder.__name__
#                 elif tool_call["args"]["to"] == "tester":
#                     return stubs.tester.__name__
#                 elif tool_call["args"]["to"] == "reviewer":
#                     return stubs.reviewer.__name__
#                 # elif tool_call["args"]["to"] == "memorizer":
#                 #     return stubs.memorizer.__name__
#                 else:
#                     raise ValueError

#     return delegate_to


# def _create_requirements_node(
#     agent_config: Configuration,
#     requirements_graph: RequirementsGraph,
#     recursion_limit: int = 100,
# ):
#     """Create an asynchronous requirements node for the orchestrator graph.

#     The returned function processes a tool call from the conversation state, invokes the requirements graph with the tool call content as input, and returns a tool message containing the summarized requirements linked to the original tool call ID.

#     Args:
#         requirements_graph: The requirements graph to invoke for requirements gathering.
#         recursion_limit: Maximum recursion depth allowed for the requirements graph (default is 100).

#     Returns:
#         An asynchronous function that processes requirements extraction and returns a dictionary with a tool message containing the summary.
#     """

#     async def requirements(state: State, config: RunnableConfig, store: BaseStore):
#         tool_call = state.messages[-1].tool_calls[0]
#         config_with_recursion = RunnableConfig(**config)
#         config_with_recursion["recursion_limit"] = recursion_limit

#         result = await requirements_graph.compiled_graph.ainvoke(
#             RequirementsState(
#                 messages=[HumanMessage(content=tool_call["args"]["content"])]
#             ),
#             config_with_recursion,
#         )

#         return {
#             "messages": [
#                 ToolMessage(
#                     content=result["summary"],
#                     tool_call_id=tool_call["id"],
#                 )
#             ]
#         }

#     return requirements


def _create_orchestrate(
    agent_config: Configuration,
    call_model: Coroutine[Any, Any, dict],
    tool_node: ToolNode,
):
    """Create an asynchronous function to determine the next step in the requirements gathering graph.

    The returned function inspects the conversation state to decide whether to route to a tool node, end the process, or continue the conversation with the model.
    """

    async def orchestrate(state: State, config: RunnableConfig):
        if state.messages[-1].tool_calls:
            return tool_node.name
        elif state.summary:
            return END
        else:
            return call_model.__name__

    return orchestrate


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
        call_orchestrator = _create_orchestrate(self._agent_config, llm)
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
        # requirements = tools.create_requirements_tool(self._agent_config, requirements_graph)

        all_tools = [
            tools.create_requirements_tool(self._agent_config, requirements_graph),
            stubs.architect,
            stubs.coder,
            stubs.tester,
            stubs.reviewer,
            stubs.memorizer,
        ]
        tool_node = ToolNode(all_tools, name="tools")

        # delegate_to = _create_delegate_to(self._agent_config, orchestrate)

        # Create the graph + all nodes
        builder = StateGraph(State, config_schema=Configuration)

        # Define the flow of the memory extraction process
        builder.add_node(call_orchestrator)
        builder.add_node(tool_node.name, tool_node)
        # builder.add_node(requirements)
        # builder.add_node(stubs.architect)
        # builder.add_node(stubs.coder)
        # builder.add_node(stubs.tester)
        # builder.add_node(stubs.reviewer)
        # builder.add_node(stubs.memorizer)

        builder.add_edge(START, call_orchestrator.__name__)
        builder.add_conditional_edges(
            call_orchestrator.__name__,
            tool_condition,
            [tool_node.name, call_orchestrator.__name__, END],
        )
        # builder.add_conditional_edges(
        #     orchestrate.__name__,
        #     delegate_to,
        # )
        # builder.add_edge(requirements.__name__, orchestrate.__name__)
        # builder.add_edge(stubs.architect.__name__, orchestrate.__name__)
        # builder.add_edge(stubs.coder.__name__, orchestrate.__name__)
        # builder.add_edge(stubs.tester.__name__, orchestrate.__name__)
        # builder.add_edge(stubs.reviewer.__name__, orchestrate.__name__)
        # builder.add_edge(stubs.memorizer.__name__, orchestrate.__name__)

        return builder


# For langsmith
graph = OrchestratorGraph(
    agent_config=Configuration(
        requirements_agent=RequirementsAgentConfig(
            use_stub=False, config=RequirementsConfiguration(use_human_ai=False)
        )
    )
).compiled_graph

__all__ = ["OrchestratorGraph"]
