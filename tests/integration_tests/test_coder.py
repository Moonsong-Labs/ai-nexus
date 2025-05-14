import uuid

import pytest

from coder.graph import coder_change_request_config, coder_new_pr_config
from common.components.github_mocks import MockGithubApi
from common.components.github_tools import get_github_tools


@pytest.mark.asyncio(loop_scope="session")
async def test_coder_creates_hello_world():
    mock_api = MockGithubApi()
    github_tools = get_github_tools(mock_api)

    # Create and build graph
    graph = coder_new_pr_config().graph_builder(github_tools).compile()

    # Run agent with request to create main.py
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Create a main.py entry point that prints 'Hello World'",
                }
            ]
        },
        config,
    )

    # Verify main.py was created with correct content
    create_file_ops = [op for op in mock_api.operations if op["type"] == "create"]
    assert len(create_file_ops) > 0, "No file creation operation found"
    main_py_op = next(op for op in create_file_ops if op["args"]["path"] == "main.py")
    assert "Hello World" in main_py_op["args"]["content"]


@pytest.mark.asyncio(loop_scope="session")
async def test_coder_renames_function():
    # Setup mock GitHub API
    mock_api = MockGithubApi()
    mock_api.files = {
        "type": "dir",
        "content": {
            "math.py": {
                "type": "file",
                "content": "def sum_two_numbers(a, b):\n    return a + b",
            }
        },
    }
    github_tools = get_github_tools(mock_api)

    # Create and build graph
    graph = coder_new_pr_config().graph_builder(github_tools).compile()

    # Run agent with request to rename function
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Rename the sum_two_numbers function in math.py to add",
                }
            ]
        },
        config,
    )

    # Verify math.py was updated correctly
    update_ops = [op for op in mock_api.operations if op["type"] == "update"]
    assert len(update_ops) > 0, "No update operation found"

    math_update = next(op for op in update_ops if op["args"]["path"] == "math.py")
    assert "add" in math_update["args"]["new_content"]
    assert "sum_two_numbers" not in math_update["args"]["new_content"]


@pytest.mark.asyncio(loop_scope="session")
async def test_coder_changes_server_port_on_existing_pr():
    # Setup mock GitHub API
    mock_api = MockGithubApi()
    mock_api.branches = ["main", "feature/add-server"]
    # Add mock PR with correct structure
    mock_api.pull_request = {
        "title": "Add a server",
        "body": "Add a server",
        "head": "feature/add-server",
        "base": "main",
    }
    github_tools = get_github_tools(mock_api)

    # Simulate initial file creation with port 8000
    # NOTE: Needs to be in files (branch state) and in operations (pr changes) for the mock to work
    mock_api.files = {
        "type": "dir",
        "content": {
            "server.py": {
                "type": "file",
                "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
            }
        },
    }
    mock_api.operations.append(
        {
            "type": "create",
            "args": {
                "path": "server.py",
                "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
                "branch": "feature/add-server",
            },
        }
    )

    # Create and build graph
    graph = coder_change_request_config().graph_builder(github_tools).compile()

    # Run agent with request to change port
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "On PR #8, the port should be 8080",
                }
            ]
        },
        config,
    )

    assert mock_api.active_branch == "feature/add-server"

    # Verify server.py was updated correctly
    update_ops = [op for op in mock_api.operations if op["type"] == "update"]
    assert len(update_ops) > 0, "No update operation found"

    print(update_ops)
    server_update = next(op for op in update_ops if op["args"]["path"] == "server.py")
    assert "port=8080" in server_update["args"]["new_content"]
    assert "port=8000" not in server_update["args"]["new_content"]
    assert "port=8000" in server_update["args"]["old_content"]
