import logging
import os
from pathlib import Path
from typing import List

import pytest

from agent_template.configuration import Configuration
from agent_template.graph import AgentTemplateGraph
from common.logging import get_logger

# Get the logger
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "conversation,expected_category",
    [
        (
            [
                "Python is strongly typed but dynamically typed, which means type checking happens at runtime rather than compile time. Remember this technical information as knowledge."
            ],
            "knowledge",
        ),
        (
            [
                "When reviewing pull requests, always check for comprehensive test coverage before approving. This is an important development rule to follow."
            ],
            "rule",
        ),
        (
            [
                "To deploy a microservice to production, first run the test suite, then build the Docker image, push it to the registry, update the deployment manifest, and finally apply the Kubernetes changes. Remember this deployment procedure."
            ],
            "procedure",
        ),
    ],
    ids=["knowledge", "rule", "procedure"],
)
async def test_memory_storage(conversation: List[str], expected_category: str):
    """
    Tests that the agent correctly categorizes and stores memory entries based on conversation input.

    Args:
        conversation: A list of user messages to send to the agent.
        expected_category: The memory category expected to be assigned ("knowledge", "rule", or "procedure").

    Asserts that at least one memory entry with the expected category is found in the agent's response.
    """
    from common.components.memory import MemoryConfiguration

    config = Configuration(memory=MemoryConfiguration(use_memory=True))
    graph = AgentTemplateGraph(agent_config=config).compiled_graph

    # Track if we found the expected category
    category_found = False

    for content in conversation:
        logger.info(f"Processing message, expecting category: {expected_category}")

        response = await graph.ainvoke(
            {"messages": [("user", content)]},
            {
                "thread_id": f"thread_{expected_category}"
            },  # Use different thread IDs for each test
        )

        # Extract AI messages from the response
        if "messages" in response:
            for message in response["messages"]:
                # Check if it's an AIMessage with tool calls
                if hasattr(message, "tool_calls") and message.tool_calls:
                    logger.info("AI message with tool calls:")
                    logger.info("Tool calls:")

                    for tool_call in message.tool_calls:
                        logger.info(f"  - Name: {tool_call['name']}")

                        # Check memory management tool calls
                        if tool_call["name"] == "manage_memory":
                            args = tool_call.get("args", {})
                            logger.info(f"  - Args: {args}")

                            # Extract and validate the category
                            content_data = args.get("content", {})
                            category = content_data.get("category")
                            logger.info(f"  - Category: {category}")

                            # Validate category is one of the expected types
                            assert category in ["knowledge", "rule", "procedure"], (
                                f"Category must be 'knowledge', 'rule', or 'procedure', but got '{category}'"
                            )

                            # Check if this matches our expected category
                            if category == expected_category:
                                category_found = True
                                logger.info(f"✅ Found matching category: {category}")

                    logger.info("-" * 50)
        else:
            logger.warning("No 'messages' key found in response")
            logger.info(f"Response keys: {list(response.keys())}")

    # Assert that we found the expected category
    assert category_found, (
        f"No memory entries with category '{expected_category}' were found"
    )

    logger.info(f"✅ Successfully found memory category: {expected_category}")


@pytest.mark.asyncio
async def test_memory_dump():
    """
    Verifies that the agent's memory dump tool exports stored memories to a non-empty file.

    Stores a memory entry, instructs the agent to dump its memories, and asserts that a memory dump file is created and contains data.
    """
    from common.components.memory import MemoryConfiguration

    config = Configuration(memory=MemoryConfiguration(use_memory=True))
    graph = AgentTemplateGraph(agent_config=config).compiled_graph

    # Step 1: Store a memory
    store_memory_msg = "The Python programming language was created by Guido van Rossum and released in 1991."
    await graph.ainvoke(
        {"messages": [("user", store_memory_msg)]},
        {"thread_id": "memory_dump_test"},
    )

    # Step 2: Request a memory dump
    dump_request = "Please call the memory_dump tool to export your memories to a file."
    await graph.ainvoke(
        {"messages": [("user", dump_request)]},
        {"thread_id": "memory_dump_test"},
    )

    # Step 3: Verify a dump file was created and is not empty
    # Check for memory dump files in current working directory and subdirectories
    current_dir = Path.cwd()
    dump_files = list(current_dir.rglob("memory_dump_*.json"))
    assert len(dump_files) > 0, "No memory dump files were created"

    # Check that file is not empty
    dump_file = dump_files[0]
    assert os.path.getsize(dump_file) > 0, "Memory dump file is empty"
