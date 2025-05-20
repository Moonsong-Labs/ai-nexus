import os
import shutil
import uuid
from typing import Awaitable, Callable

import pytest
from datasets.task_manager_dataset import (
    TASK_MANAGER_DATASET_NAME as LANGSMITH_DATASET_NAME,
)
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langsmith import Client
from testing import get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

from task_manager import prompts
from task_manager.configuration import TASK_MANAGER_MODEL
from task_manager.graph import TaskManagerGraph

# Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()


def create_task_manager_graph_caller(
    graph: CompiledStateGraph,
) -> Callable[[dict], Awaitable[dict]]:
    """
    Create a task-manager specific graph caller that properly handles the dataset format.
    This avoids modifying the original graph caller that might be used by other tests.
    """
    logger = get_logger("task_manager_graph_caller")

    async def call_model(inputs: dict):
        # Handle different input formats
        messages = []

        # Case 1: Direct message content
        if "message" in inputs and isinstance(inputs["message"], str):
            content = inputs["message"]
            if content and content.strip():
                messages.append(HumanMessage(content=content))
            else:
                messages.append(HumanMessage(content="Task manager test query"))

        # Case 2: Message object with content
        elif (
            "message" in inputs
            and isinstance(inputs["message"], dict)
            and "content" in inputs["message"]
        ):
            content = inputs["message"]["content"]
            if content and content.strip():
                messages.append(HumanMessage(content=content))
            else:
                messages.append(HumanMessage(content="Task manager test query"))

        # Case 3: Messages array (used by LangSmith dataset)
        elif "messages" in inputs and isinstance(inputs["messages"], list):
            for msg in inputs["messages"]:
                if (
                    isinstance(msg, dict)
                    and "role" in msg
                    and msg["role"] == "human"
                    and "content" in msg
                ):
                    content = msg["content"]
                    if content and content.strip():
                        messages.append(HumanMessage(content=content))

        # Default case if no valid messages were found
        if not messages:
            messages.append(HumanMessage(content="Task manager test query"))

        logger.info(f"Processed messages for task manager: {messages}")

        state = {"messages": messages}

        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "model": TASK_MANAGER_MODEL,
                "task_manager_system_prompt": prompts.SYSTEM_PROMPT,
            }
        }

        try:
            result = await graph.compiled_graph.ainvoke(state, config=config)

            if isinstance(result, dict) and "messages" in result and result["messages"]:
                return result["messages"][-1].content

            return str(result)
        except Exception as e:
            logger.error(f"Error invoking graph: {e}")
            return f"Error: {str(e)}"

    return call_model


@pytest.mark.asyncio
async def test_task_manager_langsmith(pytestconfig):
    """
    Tests the task-manager agent graph using langsmith.aevaluate against a LangSmith dataset.
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

    # Compile the graph - needs checkpointer for stateful execution during evaluation
    # graph_compiled = graph_builder.compile(checkpointer=MemorySaver())
    graph = TaskManagerGraph(checkpointer=MemorySaver())

    results = await client.aevaluate(
        create_task_manager_graph_caller(graph),
        data=LANGSMITH_DATASET_NAME,  # The whole dataset is used
        evaluators=[llm_judge.create_correctness_evaluator(plaintext=True)],
        experiment_prefix="task-manager-gemini-2.5-correctness-eval-plain",
        num_repetitions=1,
        max_concurrency=1,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"


@pytest.mark.asyncio
async def test_task_manager_with_project_path():
    """
    Tests the task manager agent with a specific project path.
    Verifies that it creates a planning folder in the specified project directory.
    """
    # Define test paths
    project_dir = "tests/integration_tests/inputs/api_rust"
    planning_dir = os.path.join(project_dir, "planning")

    # Remove planning folder from previous tests execution
    if os.path.exists(planning_dir):
        shutil.rmtree(planning_dir)

    # Initialize a task manager graph
    graph = TaskManagerGraph(checkpointer=MemorySaver())

    # Prepare test message with project path
    messages = [
        HumanMessage(
            content="Start working with the api_rust project located at tests/integration_tests/inputs/api_rust"
        )
    ]

    state = {"messages": messages}

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "model": TASK_MANAGER_MODEL,
            "task_manager_system_prompt": prompts.SYSTEM_PROMPT,
        },
        "recursion_limit": 100,
    }

    # Invoke the graph
    await graph.compiled_graph.ainvoke(state, config=config)

    # Check if planning folder was created
    assert os.path.exists(planning_dir), "Planning folder was not created"

    # Check if roadmap.md file was created
    assert os.path.exists(os.path.join(planning_dir, "roadmap.md")), (
        "roadmap.md was not created"
    )

    # Count and verify that multiple task files were created
    task_files = [
        f
        for f in os.listdir(planning_dir)
        if f.startswith("task-") and f.endswith(".md")
    ]
    assert len(task_files) > 1, (
        f"Expected multiple task files, but found only {len(task_files)}: {task_files}"
    )

    # Clean up after the test
    # shutil.rmtree(planning_dir)
