import json
import os
import shutil
import uuid
from typing import Awaitable, Callable

import pytest
from tests.datasets.task_manager_dataset import (
    TASK_MANAGER_DATASET_NAME as LANGSMITH_DATASET_NAME,
)
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langsmith import Client
from tests.testing import get_logger
from tests.testing.evaluators import LLMJudge
from tests.testing.formatter import Verbosity, print_evaluation

from common.state import Project
from task_manager import prompts
from task_manager.configuration import TASK_MANAGER_MODEL
from task_manager.graph import TaskManagerGraph

# Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()


def create_task_manager_graph_caller(
    graph: TaskManagerGraph,
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

        # Add project information
        project = Project(
            id="test-project", name="Test Project", path="/path/to/test/project"
        )
        state["project"] = project

        config = graph.create_runnable_config({
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "model": TASK_MANAGER_MODEL,
                "task_manager_system_prompt": prompts.SYSTEM_PROMPT,
            }
        })

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
async def test_task_manager_hobby_mode():
    """
    Tests the task manager agent in HOBBY mode.
    Verifies that it creates exactly one task file and tasks.json when HOBBY is specified.
    """
    # Define test paths - build absolute path from test file location
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(test_dir, "inputs", "api_rust_hobby")
    planning_dir = os.path.join(project_dir, "planning")

    # Check that project_dir exists
    if not os.path.exists(project_dir):
        pytest.fail(f"Project directory does not exist: {project_dir}")

    # Remove planning folder from previous tests execution
    if os.path.exists(planning_dir):
        shutil.rmtree(planning_dir)

    # Initialize a task manager graph
    graph = TaskManagerGraph(checkpointer=MemorySaver())

    # Create Project object for this test
    project = Project(id="api_rust", name="api_rust", path=project_dir)

    # Prepare test message with HOBBY keyword
    messages = [
        HumanMessage(
            content=f"HOBBY: Start working with the {project.name} project located at {project.path}"
        )
    ]

    state = {"messages": messages, "project": project}

    config = graph.create_runnable_config({
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "model": TASK_MANAGER_MODEL,
            "task_manager_system_prompt": prompts.SYSTEM_PROMPT,
        },
        "recursion_limit": 100,
    })

    # Invoke the graph
    result = await graph.compiled_graph.ainvoke(state, config=config)

    # Check if planning folder was created
    assert os.path.exists(planning_dir), "Planning folder was not created"

    # Check that roadmap.md was NOT created (HOBBY mode skips it)
    assert not os.path.exists(os.path.join(planning_dir, "roadmap.md")), (
        "roadmap.md should not be created in HOBBY mode"
    )

    # Check that tasks.json was created
    tasks_json_path = os.path.join(planning_dir, "tasks.json")
    assert os.path.exists(tasks_json_path), "tasks.json was not created"

    # Count task files - should be exactly 1 in HOBBY mode
    task_files = [
        f
        for f in os.listdir(planning_dir)
        if f.startswith("task-") and f.endswith(".md")
    ]
    assert len(task_files) == 1, (
        f"Expected exactly 1 task file in HOBBY mode, but found {len(task_files)}: {task_files}"
    )

    # Verify the task file name contains "hobby"
    task_file = task_files[0]
    assert "hobby" in task_file.lower(), (
        f"Expected task file to contain 'hobby' in the name, but got: {task_file}"
    )

    # Read and verify tasks.json content
    import json
    with open(tasks_json_path, "r") as f:
        tasks_data = json.load(f)
    
    # Should contain exactly 1 task
    assert len(tasks_data) == 1, (
        f"Expected exactly 1 task in tasks.json for HOBBY mode, but found {len(tasks_data)}"
    )

    # Clean up after the test
    shutil.rmtree(planning_dir)


@pytest.mark.asyncio
async def test_task_manager_full_mode():
    """
    Tests the task manager agent in full/normal mode (non-HOBBY).
    Verifies that it creates multiple task files, tasks.json, and roadmap.md.
    """
    # Define test paths - build absolute path from test file location
    test_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(test_dir, "inputs", "api_rust_full")
    planning_dir = os.path.join(project_dir, "planning")

    # Check that project_dir exists
    if not os.path.exists(project_dir):
        pytest.fail(f"Project directory does not exist: {project_dir}")

    # Remove planning folder from previous tests execution
    if os.path.exists(planning_dir):
        shutil.rmtree(planning_dir)

    # Initialize a task manager graph
    graph = TaskManagerGraph(checkpointer=MemorySaver())

    # Create Project object for this test
    project = Project(id="api_rust", name="api_rust", path=project_dir)

    # Prepare test message WITHOUT HOBBY keyword (normal mode)
    messages = [
        HumanMessage(
            content=f"Start working with the {project.name} project located at {project.path}"
        )
    ]

    state = {"messages": messages, "project": project}

    config = graph.create_runnable_config({
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "model": TASK_MANAGER_MODEL,
            "task_manager_system_prompt": prompts.SYSTEM_PROMPT,
        },
        "recursion_limit": 100,
    })

    # Invoke the graph
    result = await graph.compiled_graph.ainvoke(state, config=config)

    # Check if planning folder was created
    assert os.path.exists(planning_dir), "Planning folder was not created"

    # Check that roadmap.md WAS created (normal mode creates it)
    assert os.path.exists(os.path.join(planning_dir, "roadmap.md")), (
        "roadmap.md was not created in normal mode"
    )

    # Check that tasks.json was created
    tasks_json_path = os.path.join(planning_dir, "tasks.json")
    assert os.path.exists(tasks_json_path), "tasks.json was not created"

    # Count task files - should be more than 1 in normal mode
    task_files = [
        f
        for f in os.listdir(planning_dir)
        if f.startswith("task-") and f.endswith(".md")
    ]
    assert len(task_files) > 1, (
        f"Expected multiple task files in normal mode, but found only {len(task_files)}: {task_files}"
    )

    # Read and verify tasks.json content
    import json
    with open(tasks_json_path, "r") as f:
        tasks_data = json.load(f)
    
    # Should contain multiple tasks
    assert len(tasks_data) > 1, (
        f"Expected multiple tasks in tasks.json for normal mode, but found only {len(tasks_data)}"
    )
    
    # Verify task structure
    for task in tasks_data:
        assert "id" in task, f"Task missing 'id' field: {task}"
        assert "title" in task, f"Task missing 'title' field: {task}"
        assert "description" in task, f"Task missing 'description' field: {task}"
        assert "status" in task, f"Task missing 'status' field: {task}"
        assert "dependencies" in task, f"Task missing 'dependencies' field: {task}"
        assert task["status"] == "pending", f"Expected status 'pending', got '{task['status']}'"
    
    # Verify that task files don't contain "hobby" in the name
    for task_file in task_files:
        assert "hobby" not in task_file.lower(), (
            f"Task file should not contain 'hobby' in normal mode, but got: {task_file}"
        )
    
    # Verify roadmap.md exists and has content
    roadmap_path = os.path.join(planning_dir, "roadmap.md")
    assert os.path.exists(roadmap_path), "roadmap.md file should exist"
    
    # Check that roadmap.md is not empty
    assert os.path.getsize(roadmap_path) > 0, "roadmap.md should not be empty"

    # Clean up after the test
    shutil.rmtree(planning_dir)
