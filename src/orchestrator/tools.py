"""Define he agent's tools."""

from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from orchestrator.configuration import Configuration
from orchestrator.state import State
from requirement_gatherer.graph import RequirementsGraph
from requirement_gatherer.state import State as RequirementsState


@dataclass
class Delegate:
    """Decision on where to delegate a task.

    - If requirements, then "requirements".
    - If architecture and design, then "architect".
    - If coding and implementation, then "coder_new_pr".
    - If coding and implementation, then "coder_change_request".
    - If code needs testing, then "tester".
    - If code needs review, then "reviewer".
    """

    to: Literal[
        "orchestrator",
        "requirements",
        "architect",
        "coder_new_pr",
        "coder_change_request",
        "tester",
        "reviewer",
    ]
    content: str


# def _create_delegate_to(
#     agent_config: Configuration, orchestrate: Coroutine[Any, Any, dict]
# ):
#     @tool("delegate_to", parse_docstring=True)
#     async def delegate_to(
#         delegate: Delegate,
#         tool_call_id: Annotated[str, InjectedToolCallId],
#         state: Annotated[State, InjectedState],
#         config: RunnableConfig,
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
#         if delegate.to == "orchestrator":
#             return orchestrate.__name__
#         elif delegate.to == "requirements":
#             return "requirements"
#         elif delegate.to == "architect":
#             return stubs.architect.__name__
#         elif delegate.to == "coder":
#             return stubs.coder.__name__
#         elif delegate.to == "tester":
#             return stubs.tester.__name__
#         elif delegate.to == "reviewer":
#             return stubs.reviewer.__name__
#         # elif tool_call["args"]["to"] == "memorizer":
#         #     return stubs.memorizer.__name__
#         else:
#             raise ValueError

#     return delegate_to


def create_requirements_tool(
    agent_config: Configuration,
    requirements_graph: RequirementsGraph,
    recursion_limit: int = 100,
):
    """Create an asynchronous requirements gatherer tool for the orchestrator graph.

    The returned function processes a tool call from the conversation state, invokes the requirements graph with the tool call content as input, and returns a tool message containing the summarized requirements linked to the original tool call ID.

    Args:
        requirements_graph: The requirements graph to invoke for requirements gathering.
        recursion_limit: Maximum recursion depth allowed for the requirements graph (default is 100).

    Returns:
        An asynchronous function that processes requirements extraction and returns a dictionary with a tool message containing the summary.
    """

    @tool("requirements", parse_docstring=True)
    async def requirements(
        content: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> Command:
        """If requirements need to be gathered or a project defined in the earliest stage.

        Args:
            content: The input to the requirements gatherer agent.

        Returns:
            A Command that updates the agent's state with requirements gatherer's response.
        """
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await requirements_graph.compiled_graph.ainvoke(
            RequirementsState(messages=[HumanMessage(content=content)]),
            config_with_recursion,
        )

        return {
            "messages": [
                ToolMessage(
                    content=result["summary"],
                    tool_call_id=tool_call_id,
                )
            ]
        }

    return requirements


def _create_architect_tool(
    agent_config: Configuration,
    architect_graph: RequirementsGraph,
    recursion_limit: int = 100,
):
    @tool("architect", parse_docstring=True)
    async def architect(
        content: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> Command:
        """Given the requirements if a project architectrure or design needs to be created.

        Args:
            content: The input to the architect agent.

        Returns:
            A Command that updates the agent's state with requirements gatherer's response.
        """
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await architect_graph.compiled_graph.ainvoke(
            RequirementsState(messages=[HumanMessage(content=content)]),
            config_with_recursion,
        )

        return {
            "messages": [
                ToolMessage(
                    content=result["summary"],
                    tool_call_id=tool_call_id,
                )
            ]
        }

    return architect


@tool("store_memory", parse_docstring=True)
def store_memory(
    content: str,
    origin: Literal[
        "user",
        "requirements",
        "architect",
        "coder_new_pr",
        "coder_change_request",
        "tester",
        "reviewer",
    ],
):
    """Use this to memorize, store or remember instructions."""
    # print(f"[MEMORIZE] for {origin}: {content}")  # noqa: T201
    return f"Memorized '{content}' for '{origin}'"


@dataclass
class Memory:
    """Tool to update memory."""

    origin: Literal[
        "user",
        "requirements",
        "architect",
        "coder_new_pr",
        "coder_change_request",
        "tester",
        "reviewer",
    ]
    content: str
