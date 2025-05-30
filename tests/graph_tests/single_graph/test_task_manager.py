import json
import os
import shutil
import uuid

import pytest
from fixtures import FIXTURES_PATH
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from common.state import Project
from task_manager.configuration import Configuration
from task_manager.graph import TaskManagerGraph


@pytest.mark.asyncio
async def test_task_manager_hobby_mode():
    """
    Tests the task manager agent in HOBBY mode.
    Verifies that it creates exactly one task file and tasks.json when HOBBY is specified.
    """
    # Define test paths - build absolute path from test file location
    project_fixture = os.path.join(FIXTURES_PATH, "project_inputs", "api_rust_hobby")
    project_dir = os.path.join("/tmp", "task_manager_test", "api_rust_hobby")

    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    shutil.copytree(project_fixture, project_dir)

    planning_dir = os.path.join(project_dir, "planning")

    # Check that project_dir exists
    if not os.path.exists(project_dir):
        pytest.fail(f"Project directory does not exist: {project_dir}")

    # Remove planning folder from previous tests execution
    if os.path.exists(planning_dir):
        shutil.rmtree(planning_dir)

    # Initialize a task manager graph
    graph = TaskManagerGraph(
        agent_config=Configuration(user_id="test_user"), checkpointer=MemorySaver()
    )

    # Create Project object for this test
    project = Project(id="api_rust", name="api_rust", path=project_dir)

    # Prepare test message with HOBBY keyword
    messages = [
        HumanMessage(
            content=f"HOBBY: Start working with the {project.name} project located at {project.path}"
        )
    ]

    state = {"messages": messages, "project": project}

    config = graph.create_runnable_config(
        RunnableConfig(
            configurable={
                "thread_id": str(uuid.uuid4()),
            },
            recursion_limit=100,
        )
    )

    # Invoke the graph
    await graph.compiled_graph.ainvoke(state, config=config)

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
    project_fixture = os.path.join(FIXTURES_PATH, "project_inputs", "api_rust_full")
    project_dir = os.path.join("/tmp", "task_manager_test", "api_rust_full")

    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    shutil.copytree(project_fixture, project_dir)

    planning_dir = os.path.join(project_dir, "planning")

    # Check that project_dir exists
    if not os.path.exists(project_dir):
        pytest.fail(f"Project directory does not exist: {project_dir}")

    # Remove planning folder from previous tests execution
    if os.path.exists(planning_dir):
        shutil.rmtree(planning_dir)

    # Initialize a task manager graph
    graph = TaskManagerGraph(
        agent_config=Configuration(user_id="test_user"), checkpointer=MemorySaver()
    )

    # Create Project object for this test
    project = Project(id="api_rust", name="api_rust", path=project_dir)

    # Prepare test message WITHOUT HOBBY keyword (normal mode)
    messages = [
        HumanMessage(
            content=f"Start working with the {project.name} project located at {project.path}"
        )
    ]

    state = {"messages": messages, "project": project}

    config = graph.create_runnable_config(
        RunnableConfig(
            configurable={
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
            },
            recursion_limit=100,
        )
    )

    # Invoke the graph
    await graph.compiled_graph.ainvoke(state, config=config)

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
        assert task["status"] == "pending", (
            f"Expected status 'pending', got '{task['status']}'"
        )

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
