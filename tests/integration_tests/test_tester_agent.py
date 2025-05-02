import logging
import uuid

import pytest

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Stop chaging this for graph, we need the builder
from tester.graph import builder as tester_graph

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_tester_hello_response():
    """
    Tests the tester agent responds to a hello message without asking questions.
    """
    # Create both a memory saver for checkpointing and an in-memory store
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    
    # Compile the graph with both the checkpointer and store
    graph_compiled = tester_graph.compile(
        checkpointer=memory_saver,
        store=memory_store
    )
    
    # Create a simple hello message
    input_message = "hello"
    graph_input = {"messages": [HumanMessage(content=input_message)]}
    
    # Generate a unique thread_id for this test run
    config = {"configurable": {"thread_id": str(uuid.uuid4()), "user_id": "test_user"}}
    
    try:
        # Invoke the graph
        result = await graph_compiled.ainvoke(graph_input, config=config)
        
        # Get the last message from the agent
        assert "messages" in result, "Expected 'messages' in result"
        last_message = result["messages"][-1]
        
        # Verify the response content
        response_content = last_message.content if hasattr(last_message, "content") else str(last_message)
        
        # Check that the response doesn't contain questions or testing language
        assert "questions=[]" in response_content, "Response should not contain questions"
        assert "tests=[]" in response_content, "Response should not contain tests"
        
        logger.info(f"Test passed. Agent response: {response_content}")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        pytest.fail(f"Test failed with error: {e}") 