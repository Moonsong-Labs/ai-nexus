import logging
from typing import List

import pytest

from agent_template.configuration import Configuration
from agent_template.graph import graph_builder

# Get the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "conversation",
    [
        ["My name is Alice and I love pizza. Remember this."],
        [
            "Hi, I'm Bob and I enjoy playing tennis. Remember this.",
            "Yes, I also have a pet dog named Max.",
            "Max is a golden retriever and he's 5 years old. Please remember this too.",
        ],
        [
            "Hello, I'm Charlie. I work as a software engineer and I'm passionate about AI. Remember this.",
            "I specialize in machine learning algorithms and I'm currently working on a project involving natural language processing.",
            "My main goal is to improve sentiment analysis accuracy in multi-lingual texts. It's challenging but exciting.",
            "We've made some progress using transformer models, but we're still working on handling context and idioms across languages.",
            "Chinese and English have been the most challenging pair so far due to their vast differences in structure and cultural contexts.",
        ],
    ],
    ids=["short", "medium", "long"],
)
async def test_memory_storage(conversation: List[str]):
    config = Configuration()
    graph = graph_builder(config).compile()

    manage_memory_calls_found = False

    for content in conversation:
        response = await graph.ainvoke(
            {"messages": [("user", content)]},
            {"thread_id": "thread"},
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
                        logger.info(f"    Args: {tool_call['args']}")
                        # Check if manage_memory is being called
                        if tool_call["name"] == "manage_memory":
                            manage_memory_calls_found = True

                    logger.info("-" * 50)
        else:
            logger.warning("No 'messages' key found in response")
            logger.info(f"Response keys: {list(response.keys())}")

    # Assert that we found at least one manage_memory call
    assert manage_memory_calls_found, (
        "No 'manage_memory' tool calls found in any of the responses"
    )
