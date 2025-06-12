import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from common import tools
from common.chain import prechain, skip_on_summary_and_tool_errors
from common.configuration import AgentConfiguration
from common.state import AgentState


@pytest.mark.asyncio
async def test_tool_errors_are_propagated() -> None:
    error_threshold = 2
    error_msg = "DIVIDE_BY_ZERO"

    @tool("failure", parse_docstring=True)
    def failure():
        """Called when a failure occurs"""
        raise Exception(error_msg)

    @prechain(
        skip_on_summary_and_tool_errors(
            error_threshold=error_threshold,
            error_message="[Abort] {error}",
        )
    )
    async def call_model(state: AgentState, config: RunnableConfig) -> dict:
        """Extract the user's state from the conversation and update the memory."""

        if config["configurable"]["invoke_count"] < error_threshold:
            config["configurable"]["invoke_count"] += 1
            msg = AIMessage(
                content="Using tool",
                tool_calls=[
                    {
                        "id": "1",
                        "name": "failure",
                        "args": {},
                    }
                ],
            )
            return {"messages": [msg]}

        return {"messages": "LLM was called"}

    async def call_model_condition(state: AgentState):
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

    builder = StateGraph(AgentState, config_schema=AgentConfiguration)
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
                "recursion_limit": 10,  # test will fail due to recursion limit if behavior incorrect
                "run_name": "test",
                "configurable": {"invoke_count": 0},
            },
        )

        expected_messages = [
            ("human", "test"),
            ("ai", "Using tool"),
            ("tool", error_msg),
            ("ai", "Using tool"),
            ("tool", error_msg),
            ("ai", f"[Abort] {error_msg}"),
        ]
        actual_messages = [(msg.type, msg.content) for msg in state["messages"]]

        assert state["summary"] == ""
        assert state["error"] == error_msg
        assert expected_messages == actual_messages
    except GraphRecursionError:
        pytest.fail("graph was not interrupted on tool error")


@pytest.mark.asyncio
async def test_summary_is_propagated() -> None:
    @prechain(skip_on_summary_and_tool_errors(summary_message="[Summary] {summary}"))
    async def call_model(state: AgentState, config: RunnableConfig) -> dict:
        """Extract the user's state from the conversation and update the memory."""

        if config["configurable"]["first_run"]:
            config["configurable"]["first_run"] = False
            msg = AIMessage(
                content="Using tool",
                tool_calls=[
                    {
                        "id": "1",
                        "name": "summarize",
                        "args": {"summary": "Answer is 42"},
                    }
                ],
            )
            return {"messages": [msg]}

        return {"messages": "LLM was called"}

    async def call_model_condition(state: AgentState):
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
        [tools.create_summarize_tool("test")], name="tools", handle_tool_errors=lambda e: str(e)
    )

    builder = StateGraph(AgentState, config_schema=AgentConfiguration)
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
                "recursion_limit": 10,  # test will fail due to recursion limit if behavior incorrect
                "run_name": "test",
                "configurable": {"first_run": True},
            },
        )

        last_message = state["messages"][-1].content

        assert state["summary"] == "Answer is 42"
        assert state["error"] == ""
        assert last_message == "[Summary] Answer is 42"
    except GraphRecursionError:
        pytest.fail("graph was not interrupted on tool error")
