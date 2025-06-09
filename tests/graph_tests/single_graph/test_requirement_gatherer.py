import uuid
from collections import Counter

import pytest
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from testing.utils import get_tool_args_with_names

from requirement_gatherer.configuration import Configuration as GathererConfig
from requirement_gatherer.graph import RequirementsGraph


@pytest.mark.asyncio
async def test_requirement_gatherer_ends_with_summarize_tool_call():
    """
    Tests that the RequirementsGraph produces a ToolMessage with name 'summarize'
    as the second to last message.
    """

    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    agent_config = GathererConfig(
        use_human_ai=True,
        user_id="test_user",
        model="google_genai:gemini-2.0-flash",
    )

    graph = RequirementsGraph(
        checkpointer=memory_saver, store=memory_store, agent_config=agent_config
    )

    test_input = {"messages": [{"role": "human", "content": "Start!"}]}
    config = graph.create_runnable_config(
        RunnableConfig(
            configurable={
                "thread_id": str(uuid.uuid4()),
            },
            recursion_limit=100,
        )
    )
    print(config)

    result = await graph.compiled_graph.ainvoke(test_input, config=config)

    assert result is not None
    assert "messages" in result

    messages = result["messages"]
    # At least two messages need to be generated
    assert len(messages) >= 2

    tool_count_dict = Counter(
        message.name for message in messages if isinstance(message, ToolMessage)
    )
    # Each tool involved in gatherer need to be called at least once
    # 'memorize' need to be called the same number or more times than 'human_feedback'
    # 'human_feedback' can't be called more that 5 times for a hobby project
    assert 1 <= tool_count_dict["human_feedback"] <= 5
    assert tool_count_dict["human_feedback"] <= tool_count_dict["memorize"]
    assert tool_count_dict["set_project"] == 1

    # Requirement gatherer needs to finish with the summarize (also checks its called once)
    second_last_message = messages[-2]
    assert isinstance(second_last_message, ToolMessage), (
        f"Expected second to last message to be a ToolMessage, got {type(second_last_message).__name__}. Full message: {second_last_message}"
    )
    assert second_last_message.name == "summarize", (
        f"Expected ToolMessage name to be 'summarize', got '{second_last_message.name}'. Available tool names in messages: {[msg.name for msg in messages if isinstance(msg, ToolMessage)]}"
    )

    # Retrieve stored memories
    stored_memories = memory_store.search(
        ("memories", "test_user"),
        query=str([m.content for m in messages]),
        limit=10,
    )
    # Get arguments with which AI called tool
    memories_args = get_tool_args_with_names(messages=messages, tool_name="memorize")

    assert len(memories_args) == len(stored_memories)

    # Check that content and context match between tool args and stored memories
    for memory_arg, stored_memory in zip(memories_args, stored_memories):
        arg_content = memory_arg["content"]
        arg_context = memory_arg["context"]

        stored_value = stored_memory.value
        stored_content = stored_value["content"]
        stored_context = stored_value["context"]

        assert arg_content == stored_content
        assert arg_context == stored_context
