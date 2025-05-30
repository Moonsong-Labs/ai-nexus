"""
Simple local evaluation tests for task manager that don't require external credentials.
This is a standalone version that doesn't import the LangSmith dependencies.
"""
import pytest
import uuid
import sys
import os

# Add src directory to path
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from common.state import Project
from task_manager.configuration import Configuration as TaskManagerConfig
from task_manager.graph import TaskManagerGraph


# Test cases for local evaluation
TEST_CASES = [
    {
        "inputs": {
            "messages": [HumanMessage(content="What requirements do you need to make your work done?")]
        },
        "expected_keywords": ["project", "name", "files", "requirements"]
    },
    {
        "inputs": {
            "messages": [HumanMessage(content="What files must I provide to you?")]
        },
        "expected_keywords": ["md", "requirements", "context", "files"]
    },
    {
        "inputs": {
            "messages": [HumanMessage(content="How do I start working with a project?")]
        },
        "expected_keywords": ["project", "name", "directory", "files"]
    }
]


@pytest.mark.asyncio
async def test_task_manager_basic_responses():
    """
    Simple local test for task manager responses without external dependencies.
    
    This test verifies that the task manager provides reasonable responses
    to basic questions about requirements and project setup.
    """
    # Setup the task manager graph
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    agent_config = TaskManagerConfig()
    
    graph = TaskManagerGraph(
        checkpointer=memory_saver,
        store=memory_store,
        agent_config=agent_config
    )
    
    # Test project
    project = Project(
        id="test-project",
        name="Test Project", 
        path="/path/to/test/project"
    )
    
    # Run tests for each case
    for i, test_case in enumerate(TEST_CASES):
        # Create unique config for each test
        config = graph.create_runnable_config({
            "configurable": {
                "thread_id": f"test_thread_{i}_{uuid.uuid4()}",
                "user_id": "test_user"
            }
        })
        
        # Prepare state
        state = {
            "messages": test_case["inputs"]["messages"],
            "project": project
        }
        
        # Run the task manager
        result = await graph.compiled_graph.ainvoke(state, config=config)
        
        # Extract response
        assert "messages" in result, f"Test case {i}: No messages in result"
        assert len(result["messages"]) > 0, f"Test case {i}: No messages returned"
        
        response = result["messages"][-1].content
        assert response, f"Test case {i}: Empty response"
        
        # Check that response contains expected keywords (simple heuristic evaluation)
        response_lower = response.lower()
        found_keywords = [
            keyword for keyword in test_case["expected_keywords"] 
            if keyword.lower() in response_lower
        ]
        
        # We expect at least half the keywords to be present
        min_expected = len(test_case["expected_keywords"]) // 2
        assert len(found_keywords) >= min_expected, (
            f"Test case {i}: Expected at least {min_expected} keywords from "
            f"{test_case['expected_keywords']}, but only found {found_keywords} "
            f"in response: {response[:200]}..."
        )
        
        print(f"✓ Test case {i} passed - Found keywords: {found_keywords}")


@pytest.mark.asyncio 
async def test_task_manager_response_quality():
    """
    Test that task manager responses meet basic quality criteria.
    """
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    agent_config = TaskManagerConfig()
    
    graph = TaskManagerGraph(
        checkpointer=memory_saver,
        store=memory_store,
        agent_config=agent_config
    )
    
    project = Project(
        id="test-project",
        name="Test Project",
        path="/path/to/test/project"
    )
    
    config = graph.create_runnable_config({
        "configurable": {
            "thread_id": f"quality_test_{uuid.uuid4()}",
            "user_id": "test_user"
        }
    })
    
    # Test with a basic requirements question
    state = {
        "messages": [HumanMessage(content="What do you need from me to start working?")],
        "project": project
    }
    
    result = await graph.compiled_graph.ainvoke(state, config=config)
    response = result["messages"][-1].content
    
    # Quality checks
    assert len(response) > 50, f"Response too short: {response}"
    assert len(response) < 1000, f"Response too long: {len(response)} chars"
    assert "project" in response.lower() or "file" in response.lower(), (
        f"Response should mention project or files: {response}"
    )
    
    # Check for basic helpfulness indicators
    helpful_indicators = ["need", "require", "provide", "must", "should"]
    found_indicators = [ind for ind in helpful_indicators if ind in response.lower()]
    assert len(found_indicators) > 0, (
        f"Response should contain helpful language: {response}"
    )
    
    print(f"✓ Quality test passed - Response length: {len(response)}, "
          f"Helpful indicators: {found_indicators}")


if __name__ == "__main__":
    # Allow running this file directly for testing
    import asyncio
    
    async def main():
        print("Running task manager evaluation tests...")
        try:
            await test_task_manager_basic_responses()
            print("✓ Basic responses test passed")
            
            await test_task_manager_response_quality()
            print("✓ Quality test passed")
            
            print("✅ All tests passed!")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
    
    asyncio.run(main())