import tempfile
import uuid

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from code_reviewer.graph import CodeReviewerGraph, local_code_reviewer_config
from code_reviewer.state import State

@pytest.mark.asyncio
@pytest.mark.asyncio(loop_scope="session")
async def test_tool_call_none() -> None:
    code_reviewer = CodeReviewerGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
        github_tools=[],
        config=local_code_reviewer_config()
    )

    result = await code_reviewer.compiled_graph.ainvoke(
        State(
            messages=[HumanMessage(content="Hi")],
        ),
        code_reviewer.create_runnable_config({"configurable": {"thread_id": str(uuid.uuid4())}}),
    )

    last_message = result["messages"][-1]
    actual_tool_calls = [t["name"] for t in getattr(last_message, "tool_calls", [])]

    assert [] == actual_tool_calls
    
@pytest.mark.asyncio
@pytest.mark.asyncio(loop_scope="session")
async def test_reads_dir() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        code_reviewer = CodeReviewerGraph(
            checkpointer=InMemorySaver(),
            store=InMemoryStore(),
            github_tools=[],
            config=local_code_reviewer_config()
        )

        prompt = f"Please review the code in the project found in project dir {temp_dir}"

        result = await code_reviewer.compiled_graph.ainvoke(
            State(
                messages=[HumanMessage(content=prompt)],
            ),
            code_reviewer.create_runnable_config({"configurable": {"thread_id": str(uuid.uuid4())}}),
        )

        # should at least call model and execute tool
        assert len(result["messages"]) > 1

        last_message = result["messages"][1]
        actual_tool_calls = [t["name"] for t in getattr(last_message, "tool_calls", [])]

        assert ["list_files"] == actual_tool_calls