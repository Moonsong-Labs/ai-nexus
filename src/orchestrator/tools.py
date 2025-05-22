"""Define he agent's tools."""

from typing import Annotated, Literal

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from architect.state import State as ArchitectState
from code_reviewer.state import State as CodeReviewerState
from coder.state import State as CoderState
from orchestrator.configuration import Configuration
from orchestrator.state import State
from requirement_gatherer.graph import RequirementsGraph
from requirement_gatherer.state import State as RequirementsState
from task_manager.graph import TaskManagerGraph
from task_manager.state import State as TaskManagerState
from tester.state import State as TesterState


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
    ) -> str:
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

        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=result["summary"],
                        tool_call_id=tool_call_id,
                    )
                ],
                "project": result["project"],
            }
        )

    return requirements


# ruff: noqa: D103
def create_architect_tool(
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
    ) -> str:
        """Given the requirements if a project architecture or design needs to be created.

        Args:
            content: The input to the architect agent.

        Returns:
            A Command that updates the agent's state with architect's response.
        """
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await architect_graph.compiled_graph.ainvoke(
            ArchitectState(
                messages=[HumanMessage(content=content)], project=state.project
            ),
            config_with_recursion,
        )

        return result["summary"]

    return architect


# ruff: noqa: D103
def create_task_manager_tool(
    agent_config: Configuration,
    task_manager_graph: TaskManagerGraph,
    recursion_limit: int = 100,
):
    @tool("task_manager", parse_docstring=True)
    async def task_manager(
        content: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> str:
        """If tasks need to be created or updated.

        Args:
            content: The input to the task manager agent.

        Returns:
            A Command that updates the agent's state with task manager's response.
        """
        config_with_recursion = RunnableConfig(**config)
        config_with_recursion["recursion_limit"] = recursion_limit

        result = await task_manager_graph.compiled_graph.ainvoke(
            TaskManagerState(
                messages=[HumanMessage(content=content)], project=state.project
            ),
            config_with_recursion,
        )

        return result["summary"]

    return task_manager


# ruff: noqa: D103
def create_coder_new_pr_tool(
    agent_config: Configuration,
    coder_new_pr_graph: RequirementsGraph,
):
    @tool("coder_new_pr", parse_docstring=True)
    async def coder_new_pr(
        content: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> str:
        """Given the requirements and design if code needs to be written and a PR created.

        Args:
            content: The input to the coder_new_pr agent.

        Returns:
            A Command that updates the agent's state with coder's response.
        """
        result = await coder_new_pr_graph.compiled_graph.ainvoke(
            CoderState(messages=[HumanMessage(content=content)]),
            config,
        )

        return result["messages"][-1].content

    return coder_new_pr


# ruff: noqa: D103
def create_coder_change_request_tool(
    agent_config: Configuration,
    coder_change_request_graph: RequirementsGraph,
):
    @tool("coder_change_request", parse_docstring=True)
    async def coder_change_request(
        content: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> str:
        """Given the an existing PR if any changes need to be made.

        Args:
            content: The input to the coder_change_request agent.

        Returns:
            A Command that updates the agent's state with coder's response.
        """
        result = await coder_change_request_graph.compiled_graph.ainvoke(
            CoderState(messages=[HumanMessage(content=content)]),
            config,
        )

        return result["messages"][-1].content

    return coder_change_request


# ruff: noqa: D103
def create_tester_tool(
    agent_config: Configuration,
    tester_graph: RequirementsGraph,
):
    @tool("tester", parse_docstring=True)
    async def tester(
        content: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> str:
        """Given a PR if it needs to be tested.

        Args:
            content: The input to the tester agent.

        Returns:
            A Command that updates the agent's state with tester's response.
        """
        result = await tester_graph.compiled_graph.ainvoke(
            TesterState(
                messages=[HumanMessage(content=content)],
                project=state.project,
            ),
            config,
        )

        return result["summary"]

    return tester


# ruff: noqa: D103
def create_code_reviewer_tool(
    agent_config: Configuration,
    code_reviewer_graph: RequirementsGraph,
):
    @tool("code_reviewer", parse_docstring=True)
    async def code_reviewer(
        content: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> str:
        """Given a PR if a code review is to be made.

        Args:
            content: The input to the code_reviewer agent.

        Returns:
            A Command that updates the agent's state with code reviewer's response.
        """
        result = await code_reviewer_graph.compiled_graph.ainvoke(
            CodeReviewerState(messages=[HumanMessage(content=content)]),
            config,
        )

        return result["summary"]

    return code_reviewer


@tool("memorize", parse_docstring=True)
def memorize(
    content: str,
    origin: Literal[
        "user",
        "requirements",
        "architect",
        "coder_new_pr",
        "coder_change_request",
        "tester",
        "code_reviewer",
    ],
) -> str:
    """Store information in the agent's memory for future reference.

    This tool allows the orchestrator to memorize important information, instructions,
    or context from various sources within the AI Nexus system. The stored memories
    can be retrieved later to maintain context across interactions and agent workflows.

    Args:
        content: The actual information to be stored in memory. This should be a
                string containing the knowledge, instruction, or context to remember.
        origin: The source of the memory. Must be one of: "user", "requirements",
               "architect", "coder_new_pr", "coder_change_request", "tester", or
               "reviewer". This identifies which component or agent provided the information.

    Returns:
        str: A confirmation message indicating that the content has been memorized
             for the specified origin.
    """
    # print(f"[MEMORIZE] for {origin}: {content}")  # noqa: T201
    return f"Memorized '{content}' for '{origin}'"
