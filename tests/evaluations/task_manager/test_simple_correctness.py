"""
Simple local evaluation tests for task manager that don't require external credentials.
This is a standalone version that doesn't import the LangSmith dependencies.
"""
import pytest
import sys
import os

# Add src directory to path
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from .conftest import TEST_CASES, run_basic_test_case, check_response_quality


@pytest.mark.asyncio
async def test_task_manager_basic_responses(task_manager_graph, test_project):
    """
    Simple local test for task manager responses without external dependencies.
    
    This test verifies that the task manager provides reasonable responses
    to basic questions about requirements and project setup.
    """
    # Run tests for each case
    for i, test_case in enumerate(TEST_CASES):
        found_keywords = await run_basic_test_case(
            task_manager_graph, 
            test_project, 
            test_case, 
            i
        )
        print(f"✓ Test case {i} passed - Found keywords: {found_keywords}")


@pytest.mark.asyncio 
async def test_task_manager_response_quality(task_manager_graph, test_project):
    """
    Test that task manager responses meet basic quality criteria.
    """
    response, found_indicators = await check_response_quality(
        task_manager_graph,
        test_project,
        "What do you need from me to start working?"
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