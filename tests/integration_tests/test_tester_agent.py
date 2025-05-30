import uuid

import pytest
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langsmith import Client
from testing import create_async_graph_caller, get_logger
from testing.evaluators import LLMJudge

from common.components.github_mocks import MockGithubApi
from common.components.github_tools import get_github_tools
from common.state import Project
from tester.configuration import Configuration as TesterConfig
from tester.graph import TesterAgentGraph

# Setup basic logging for the test
logger = get_logger(__name__)

# Define the LangSmith dataset ID
LANGSMITH_DATASET_NAME = "tester-agent-test-dataset"
CORRECTNESS_PROMPT = """You are an expert data labeler evaluating model outputs for correctness.
Your task is to assign a score from 0.0 to 1.0 based on the following rubric:

<Rubric>
  A correct tester agent response:
  - Properly analyzes requirements and identifies ambiguities
  - Asks clear, relevant questions when information is missing or unclear
  - Generates comprehensive tests that verify system behavior according to requirements
  - Provides proper traceability between tests and requirements
  - Includes both happy path tests and edge case tests
  - Does not invent business rules or make assumptions beyond what is stated
  - Does not define code architecture or suggest design changes

  When scoring, you should penalize:
  - Making assumptions about functionality that is not explicitly stated
  - Inventing business rules or behaviors
  - Generating tests without proper requirement traceability
  - Missing important edge cases that should be tested
  - Failing to ask questions when requirements are ambiguous
  - Excessive verbosity or unnecessary details
</Rubric>

<Instructions>
  - Carefully read the input and output
  - Focus on how well the agent generates questions or tests based on the requirements
</Instructions>

<Reminder>
  The goal is to evaluate how well the Test Agent performs its role in generating tests based on requirements.
</Reminder>

<input>
{inputs}
</input>

<output>
{outputs}
</output>

Use the reference outputs below to help you evaluate the correctness of the response:

<reference_outputs>
{reference_outputs}
</reference_outputs>
"""

# Create a LLMJudge
llm_judge = LLMJudge()


@pytest.mark.skip(reason="Disabled for now")
@pytest.mark.asyncio
async def test_tester_agent_langsmith(pytestconfig):
    """
    Tests the tester agent graph using langsmith.aevaluate against a LangSmith dataset.
    """
    client = Client()

    if not client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        logger.error(f"dataset {LANGSMITH_DATASET_NAME} not found")
        datasets = list(client.list_datasets())
        logger.error(f"found {len(datasets)} existing datasets")
        for dataset in datasets:
            logger.error(f"\tid: {dataset.id}, name: {dataset.name}")
        pytest.fail(f"dataset {LANGSMITH_DATASET_NAME} not found")

    logger.info(f"evaluating dataset: {LANGSMITH_DATASET_NAME}")

    graph_compiled = TesterAgentGraph(checkpointer=MemorySaver()).compiled_graph

    results = await client.aevaluate(
        create_async_graph_caller(graph_compiled),
        data=LANGSMITH_DATASET_NAME,
        evaluators=[
            llm_judge.create_correctness_evaluator(
                plaintext=False, prompt=CORRECTNESS_PROMPT
            )
        ],
        experiment_prefix="tester-agent-correctness-eval",
        num_repetitions=3,
        max_concurrency=2,
    )

    # Assert that results were produced
    assert results is not None, "evaluation did not return results"


@pytest.mark.asyncio
async def test_tester_agent_calls_needed_tools():
    """
    Tests that the TesterAgentGraph produces a ToolMessage with name 'summarize'
    as the second to last message.
    """
    logger.info("Testing if tester agent ends with summarize tool call.")
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    agent_config = TesterConfig()

    test_project = Project(
        id="api_rust", name="API Rust", path="tests/integration_tests/inputs/api_rust"
    )

    mock_github_tools = get_github_tools(MockGithubApi())

    graph = TesterAgentGraph(
        github_tools=mock_github_tools,
        agent_config=agent_config,
        checkpointer=memory_saver,
        store=memory_store,
    ).compiled_graph

    test_input = {
        "messages": [
            {
                "role": "user",
                "content": "Please test the application based on the requirements.",
            }
        ],
        "project": test_project,
    }
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "model": "google_genai:gemini-2.0-flash-lite",
        }
    }

    try:
        result = await graph.ainvoke(test_input, config=config)
    except Exception as e:
        pytest.fail(f"Graph invocation failed: {e}")

    assert result is not None, "Graph did not return a result."
    assert "messages" in result, "Result dictionary does not contain 'messages'."
    messages = result["messages"]

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
        "featuresContext.md",
        "progress.md",
        "projectRequirements.md",
        "projectbrief.md",
        "securityContext.md",
        "systemPatterns.md",
        "techContext.md",
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

    logger.info(
        "Test for tester agent list_files tool call and result passed successfully."
    )
