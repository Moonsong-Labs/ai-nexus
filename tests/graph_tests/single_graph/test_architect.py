import os
import shutil
import uuid
from collections import Counter

import pytest
from langchain_core.messages import (  # Import message types
    HumanMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from testing import get_logger
from testing.utils import get_tool_args_with_names

from architect.configuration import Configuration as ArchitectConfiguration
from architect.graph import ArchitectGraph
from architect.state import State
from common.state import Project

# Setup basic logging for the test
logger = get_logger(__name__)

# Test directory for file operations
TEST_DIR = "./projects/test-site"


@pytest.mark.asyncio
async def test_architect_create_files():
    """
    Tests the architect agent graph using langsmith.aevaluate against a LangSmith dataset.
    """

    memory_saver = MemorySaver()  # Checkpointer for the graph
    memory_store = InMemoryStore()
    agent_config = ArchitectConfiguration(
        user_id="test_user", model="google_genai:gemini-2.0-flash"
    )

    graph = ArchitectGraph(
        agent_config=agent_config,
        checkpointer=memory_saver,
        store=memory_store,
    )

    config = graph.create_runnable_config(
        RunnableConfig(
            recursion_limit=250,
            configurable={
                "thread_id": str(uuid.uuid4()),
            },
        )
    )

    project = Project.from_name("Test Site")
    result = await graph.compiled_graph.ainvoke(
        State(
            project=project,
            messages=HumanMessage(
                content="Create the architecture for a simple hobby website for sharing photos."
            ),
        ),
        config=config,
    )

    # Test all the architect heuristics
    try:
        # Assert that results were produced.
        assert result is not None
        assert "messages" in result

        messages = result["messages"]
        # At least two messages need to be generated
        assert len(messages) >= 2

        tool_count_dict = Counter(
            message.name for message in messages if isinstance(message, ToolMessage)
        )
        # Each tool involved in the architect needs to be called at least once
        # Create directory needs to be called only once
        # Create file and memorize need to be called for each required file in the prompt
        assert tool_count_dict["recall"] > 1
        assert tool_count_dict["create_directory"] == 1
        assert tool_count_dict["memorize"] >= 1
        assert tool_count_dict["create_file"] >= 6
        assert tool_count_dict["list_files"] > 1

        # Architect needs to finish with the summarize (also checks its called once)
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
        memories_args = get_tool_args_with_names(
            messages=messages, tool_name="memorize"
        )

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

        # Check if the files were created and are where they're supposed to be
        assert os.path.exists(TEST_DIR)
        assert os.path.isdir(TEST_DIR)

        assert os.path.exists(TEST_DIR + "/projectbrief.md")
        assert os.path.exists(TEST_DIR + "/projectRequirements.md")
        assert os.path.exists(TEST_DIR + "/systemPatterns.md")
        assert os.path.exists(TEST_DIR + "/techPatterns.md")
        assert os.path.exists(TEST_DIR + "/progress.md")
        assert os.path.exists(TEST_DIR + "/codingContext.md")
        assert os.path.exists(TEST_DIR + "/testingContext.md")

    finally:
        # Clean up after tests
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
