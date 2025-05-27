import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from common import tools
from common.chain import prechain, skip_on_summary_and_tool_errors
from orchestrator.configuration import (
    Configuration,
)
from orchestrator.state import State


@pytest.mark.asyncio
async def test_tool_errors_are_propagated() -> None:
    @tool("failure", parse_docstring=True)
    def failure():
        """Called when a failure occurs"""
        raise Exception("DIVIDE_BY_ZERO")

    @prechain(skip_on_summary_and_tool_errors(error_message="[Error] {error}"))
    async def call_model(state: State, config: RunnableConfig) -> dict:
        """Extract the user's state from the conversation and update the memory."""

        if config["configurable"]["first_run"]:
            config["configurable"]["first_run"] = False
            msg = AIMessage(content="Using tool")
            msg.tool_calls.append(
                {
                    "id": "1",
                    "name": "failure",
                    "args": {},
                }
            )
            return {"messages": [msg]}

        return {"messages": "LLM was called"}

    async def call_model_condition(state: State):
        if (
            state.messages
            and isinstance(state.messages[-1], AIMessage)
            and state.messages[-1].tool_calls
        ):
            return tool_node.name
        elif state.summary or state.error:
            return END
        else:
            return call_model.__name__

    tool_node = ToolNode([failure], name="tools", handle_tool_errors=lambda e: str(e))

    builder = StateGraph(State, config_schema=Configuration)
    builder.add_node(call_model)
    builder.add_node(tool_node.name, tool_node)
    builder.add_edge(START, call_model.__name__)
    builder.add_edge(tool_node.name, call_model.__name__)
    builder.add_conditional_edges(
        call_model.__name__,
        call_model_condition,
        [tool_node.name, call_model.__name__, END],
    )

    graph = builder.compile()

    try:
        state = await graph.ainvoke(
            {
                "messages": "test",
                "summary": "",
                "error": "",
            },
            {
                "recursion_limit": 5,  # test will fail due to recursion limit if behavior incorrect
                "run_name": "test",
                "configurable": {"first_run": True},
            },
        )

        last_message = state["messages"][-1].content

        assert state["summary"] == ""
        assert state["error"] == "DIVIDE_BY_ZERO"
        assert last_message == "[Error] DIVIDE_BY_ZERO"
    except GraphRecursionError:
        pytest.fail("graph was not interrupted on tool error")


@pytest.mark.asyncio
async def test_summary_is_propagated() -> None:
    @prechain(skip_on_summary_and_tool_errors(summary_message="[Summary] {summary}"))
    async def call_model(state: State, config: RunnableConfig) -> dict:
        """Extract the user's state from the conversation and update the memory."""

        if config["configurable"]["first_run"]:
            config["configurable"]["first_run"] = False
            msg = AIMessage(content="Using tool")
            msg.tool_calls.append(
                {
                    "id": "1",
                    "name": "summarize",
                    "args": {"summary": "Answer is 42"},
                }
            )
            return {"messages": [msg]}

        return {"messages": "LLM was called"}

    async def call_model_condition(state: State):
        if (
            state.messages
            and isinstance(state.messages[-1], AIMessage)
            and state.messages[-1].tool_calls
        ):
            return tool_node.name
        elif state.summary or state.error:
            return END
        else:
            return call_model.__name__

    tool_node = ToolNode(
        [tools.summarize], name="tools", handle_tool_errors=lambda e: str(e)
    )

    builder = StateGraph(State, config_schema=Configuration)
    builder.add_node(call_model)
    builder.add_node(tool_node.name, tool_node)
    builder.add_edge(START, call_model.__name__)
    builder.add_edge(tool_node.name, call_model.__name__)
    builder.add_conditional_edges(
        call_model.__name__,
        call_model_condition,
        [tool_node.name, call_model.__name__, END],
    )

    graph = builder.compile()

    try:
        state = await graph.ainvoke(
            {
                "messages": "test",
                "summary": "",
                "error": "",
            },
            {
                "recursion_limit": 5,  # test will fail due to recursion limit if behavior incorrect
                "run_name": "test",
                "configurable": {"first_run": True},
            },
        )

        print(state)

        last_message = state["messages"][-1].content

        assert state["summary"] == "Answer is 42"
        assert state["error"] == ""
        assert last_message == "[Summary] Answer is 42"
    except GraphRecursionError:
        pytest.fail("graph was not interrupted on tool error")
