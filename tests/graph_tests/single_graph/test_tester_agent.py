import os
import uuid

import pytest
from fixtures import FIXTURES_PATH
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from common.components.github_mocks import MockGithubApi
from common.components.github_tools import get_github_tools
from common.state import Project
from tester.configuration import Configuration
from tester.graph import TesterAgentGraph as Graph


@pytest.mark.skip("currently failing")
@pytest.mark.asyncio
async def test_tester_agent_calls_needed_tools():
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    agent_config = Configuration(
        user_id="test_user", model="google_genai:gemini-2.0-flash-lite"
    )

    project_path = os.path.join(FIXTURES_PATH, "project_inputs", "api_rust_full")
    test_project = Project(id="api_rust", name="API Rust", path=project_path)

    mock_github_tools = get_github_tools(MockGithubApi())

    graph = Graph(
        github_tools=mock_github_tools,
        agent_config=agent_config,
        checkpointer=memory_saver,
        store=memory_store,
    )

    test_input = {
        "messages": [
            {
                "role": "user",
                "content": "Please test the application based on the requirements.",
            }
        ],
        "project": test_project,
    }
    config = graph.create_runnable_config(
        RunnableConfig(
            configurable={
                "thread_id": str(uuid.uuid4()),
            }
        )
    )

    try:
        result = await graph.compiled_graph.ainvoke(test_input, config=config)
    except Exception as e:
        pytest.fail(f"Graph invocation failed: {e}")

    assert result is not None, "Graph did not return a result."
    assert "messages" in result, "Result dictionary does not contain 'messages'."
    messages = result["messages"]

    print(messages)

    # Check that list_files tool was called
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    list_files_messages = [msg for msg in tool_messages if msg.name == "list_files"]

    assert len(list_files_messages) > 0, (
        f"Expected list_files tool to be called. Available tool names in messages: {[msg.name for msg in tool_messages]}"
    )

    list_files_result = list_files_messages[0].content

    assert isinstance(list_files_result, str), "list_files result should be a string"
    assert len(list_files_result.strip()) > 0, "list_files result should not be empty"

    expected_files = [
        "progress.md",
        "projectRequirements.md",
        "projectbrief.md",
        "systemPatterns.md",
        "techPatterns.md",
        "testingContext.md",
    ]

    for expected_file in expected_files:
        assert expected_file in list_files_result, (
            f"Expected {expected_file} to be in list_files result"
        )

    # Check that read_file tool was called
    read_file_messages = [msg for msg in tool_messages if msg.name == "read_file"]

    assert len(read_file_messages) > 0, (
        f"Expected at least one read_file call, got {len(read_file_messages)}"
    )

    # Check that GitHub tools were called
    github_tools_expected = [
        "create_a_new_branch",
        "create_file",
        "create_pull_request",
    ]

    for tool_name in github_tools_expected:
        tool_messages_for_tool = [msg for msg in tool_messages if msg.name == tool_name]
        assert len(tool_messages_for_tool) > 0, (
            f"Expected {tool_name} tool to be called. Available tool names: {[msg.name for msg in tool_messages]}"
        )
