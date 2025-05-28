import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from testing.inputs import decode_base_messages

from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State


@pytest.mark.asyncio
async def test_tool_call_none() -> None:
    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
        State(
            messages=[HumanMessage(content="Hi")],
        ),
        orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}}),
        store=orchestrator.store,
    )

    last_message = result["messages"][-1]
    expected_tool_calls = [
        t["name"]
        for t in last_message.tool_calls
        if hasattr(last_message, "tool_calls")
    ]

    assert [] == expected_tool_calls


@pytest.mark.asyncio
async def test_tool_call_requirements() -> None:
    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
        State(
            messages=[HumanMessage(content="I want to build a website")],
        ),
        orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}}),
        store=orchestrator.store,
    )

    last_message = result["messages"][-1]
    expected_tool_calls = [
        t["name"]
        for t in last_message.tool_calls
        if hasattr(last_message, "tool_calls")
    ]

    assert ["requirements"] == expected_tool_calls


@pytest.mark.asyncio
async def test_tool_call_architect() -> None:
    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
        State(
            messages=decode_base_messages(
                [
                    {
                        "content": "I want to build a website",
                        "role": "human",
                    },
                    {
                        "content": "I'll delegate this task to the Requirements Gatherer.",
                        "role": "ai",
                        "tool_calls": [
                            {
                                "name": "requirements",
                                "args": {"content": "website"},
                                "id": "1",
                            }
                        ],
                    },
                    {
                        "content": "MyWebsite is a personal blog intended for sharing personal experiences with friends and family.",
                        "role": "tool",
                        "name": "requirements",
                        "tool_call_id": "1",
                        "status": "success",
                    },
                ]
            ),
        ),
        orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}}),
        store=orchestrator.store,
    )

    last_message = result["messages"][-1]
    expected_tool_calls = [
        t["name"]
        for t in last_message.tool_calls
        if hasattr(last_message, "tool_calls")
    ]

    assert ["architect"] == expected_tool_calls
