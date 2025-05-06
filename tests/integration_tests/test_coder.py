import pytest
from coder.mocks import MockGithubApi
from coder.tools import get_github_tools
from coder.graph import graph_builder

@pytest.mark.asyncio
async def test_coder_creates_hello_world():
    mock_api = MockGithubApi()
    github_tools = get_github_tools(mock_api)
    
    # Create and build graph
    graph = graph_builder(github_tools).compile()
    
    # Run agent with request to create main.py
    config = {"configurable": {"thread_id": "test"}}
    await graph.ainvoke(
        {"messages": [{"role": "user", "content": "Create a main.py entry point that prints 'Hello World'"}]},
        config
    )
    
    # Verify main.py was created with correct content
    create_file_ops = [op for op in mock_api.operations if op["type"] == "create"]
    assert len(create_file_ops) > 0, "No file creation operation found"
    main_py_op = next(op for op in create_file_ops if op["args"]["path"] == "main.py")
    assert "Hello World" in main_py_op["args"]["content"]
