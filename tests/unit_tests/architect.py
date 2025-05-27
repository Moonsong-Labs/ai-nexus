import os
import shutil
import uuid

import pytest
from langchain_core.messages import (  # Import message types
    HumanMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from testing import get_logger

from architect.configuration import Configuration as ArchitectConfiguration
from architect.graph import ArchitectGraph
from architect.state import State
from common.state import Project

# Setup basic logging for the test
logger = get_logger(__name__)

# Test directory for file operations
TEST_DIR = "./projects/test-site"


@pytest.mark.asyncio
async def test_architect_create_files(pytestconfig):
    """
    Tests the architect agent graph using langsmith.aevaluate against a LangSmith dataset.
    """

    memory_saver = MemorySaver()  # Checkpointer for the graph
    memory_store = InMemoryStore()
    agent_config = ArchitectConfiguration()

    graph = ArchitectGraph(
        agent_config=agent_config,
        checkpointer=memory_saver,
        store=memory_store,
    )

    config = RunnableConfig(
        recursion_limit=250,
        configurable={
            "thread_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "model": "google_genai:gemini-2.0-flash-lite",
        },
    )

    # Compile the graph - needs checkpointer for stateful execution during evaluation
    compiled_graph = graph.builder.compile(
        checkpointer=memory_saver, store=memory_store
    )

    project = Project.from_name("Test Site")

    result = await compiled_graph.ainvoke(
        State(
            project=project,
            messages=HumanMessage(
                content="Create the architecture for a simple hobby website for sharing photos."
            ),
        ),
        config=config,
    )

    # Assert that results were produced.
    assert result is not None

    assert os.path.exists(TEST_DIR)
    assert os.path.isdir(TEST_DIR)

    assert os.path.exists(TEST_DIR + "/projectbrief.md")
    assert os.path.exists(TEST_DIR + "/projectRequirements.md")
    assert os.path.exists(TEST_DIR + "/systemPatterns.md")
    assert os.path.exists(TEST_DIR + "/techPatterns.md")
    assert os.path.exists(TEST_DIR + "/progress.md")
    assert os.path.exists(TEST_DIR + "/codingContext.md")
    assert os.path.exists(TEST_DIR + "/testingContext.md")

    # Clean up after tests
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
