"""Common fixtures and test data for task manager evaluations."""
import pytest
import uuid
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from common.state import Project
from task_manager.configuration import Configuration as TaskManagerConfig
from task_manager.graph import TaskManagerGraph


# Shared test cases
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


@pytest.fixture
def task_manager_graph():
    """Fixture that provides a configured TaskManagerGraph."""
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    agent_config = TaskManagerConfig()
    
    graph = TaskManagerGraph(
        checkpointer=memory_saver,
        store=memory_store,
        agent_config=agent_config
    )
    
    return graph


@pytest.fixture
def test_project():
    """Fixture that provides a test project."""
    return Project(
        id="test-project",
        name="Test Project",
        path="/path/to/test/project"
    )


@pytest.fixture
def graph_config():
    """Fixture that provides a unique graph configuration."""
    return {
        "configurable": {
            "thread_id": f"test_thread_{uuid.uuid4()}",
            "user_id": "test_user"
        }
    }


async def run_basic_test_case(graph, project, test_case, test_id):
    """Helper function to run a single test case."""
    # Create unique config for each test
    config = graph.create_runnable_config({
        "configurable": {
            "thread_id": f"test_thread_{test_id}_{uuid.uuid4()}",
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
    assert "messages" in result, f"Test case {test_id}: No messages in result"
    assert len(result["messages"]) > 0, f"Test case {test_id}: No messages returned"
    
    response = result["messages"][-1].content
    assert response, f"Test case {test_id}: Empty response"
    
    # Check that response contains expected keywords (simple heuristic evaluation)
    response_lower = response.lower()
    found_keywords = [
        keyword for keyword in test_case["expected_keywords"] 
        if keyword.lower() in response_lower
    ]
    
    # We expect at least half the keywords to be present
    min_expected = len(test_case["expected_keywords"]) // 2
    assert len(found_keywords) >= min_expected, (
        f"Test case {test_id}: Expected at least {min_expected} keywords from "
        f"{test_case['expected_keywords']}, but only found {found_keywords} "
        f"in response: {response[:200]}..."
    )
    
    return found_keywords


async def check_response_quality(graph, project, message_content):
    """Helper function to check response quality."""
    config = graph.create_runnable_config({
        "configurable": {
            "thread_id": f"quality_test_{uuid.uuid4()}",
            "user_id": "test_user"
        }
    })
    
    # Test with a basic requirements question
    state = {
        "messages": [HumanMessage(content=message_content)],
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
    
    return response, found_indicators