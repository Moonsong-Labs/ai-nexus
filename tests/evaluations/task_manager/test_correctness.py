import pytest
import uuid
import sys
import os

# Add tests and src directories to path for imports
tests_dir = os.path.dirname(os.path.dirname(__file__))
src_dir = os.path.join(os.path.dirname(tests_dir), 'src')
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from datasets.task_manager_dataset import TASK_MANAGER_DATASET_NAME
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langsmith import Client
from testing import get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

from task_manager.configuration import Configuration as TaskManagerConfig
from task_manager.graph import TaskManagerGraph
from .conftest import TEST_CASES, run_basic_test_case, check_response_quality

# Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()

TASK_MANAGER_CORRECTNESS_PROMPT = """You are an expert data labeler evaluating model outputs for correctness. 
Your task is to assign a score from 0.0 to 1.0 based on the following rubric:

<Rubric>
  A correct answer:
  - Provides accurate and complete information
  - Contains no factual errors
  - Addresses all parts of the question
  - Is logically consistent
  - Uses precise and accurate terminology

  When scoring, you should penalize:
  - Factual errors or inaccuracies
  - Incomplete or partial answers
  - Misleading or ambiguous statements
  - Incorrect terminology
  - Logical inconsistencies
  - Missing key information
  - Excessive verbosity or unnecessary details
  - Extra information that is not relevant to a review
</Rubric>

<Instructions>
  - Carefully read the input and output
  - Check for factual accuracy and completeness
  - Focus on correctness of information rather than style or verbosity
</Instructions>

<Reminder>
  The goal is to evaluate factual correctness and completeness of the response.
  1 is if response fully match an example
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


def create_async_graph_caller_for_task_manager(graph):
    """
    Create a task manager graph caller that properly handles the dataset format.
    """
    async def call_model(inputs: dict):
        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "model": "google_genai:gemini-2.0-flash-lite",
            }
        }

        result = await graph.ainvoke(inputs, config=config)
        return result["messages"][-1].content

    return call_model

# TEST_CASES now imported from conftest.py


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


@pytest.mark.asyncio
async def test_task_manager_langsmith(pytestconfig):
    """
    Asynchronously tests the TaskManagerGraph agent using LangSmith's evaluation framework.

    This test verifies that the specified LangSmith dataset exists, evaluates the TaskManagerGraph agent over the dataset using an LLM-based correctness evaluator, and asserts that evaluation results are produced.
    """
    client = Client()

    if not client.has_dataset(dataset_name=TASK_MANAGER_DATASET_NAME):
        logger.error(
            "Dataset %s not found in LangSmith!", TASK_MANAGER_DATASET_NAME
        )
        # Print existing datasets for debugging
        datasets = client.list_datasets()
        logger.error("Existing datasets: %s", datasets)
        for dataset in datasets:
            logger.error("Dataset ID: %s, Name: %s", dataset.id, dataset.name)
        pytest.fail(
            f"Dataset {TASK_MANAGER_DATASET_NAME} not found in LangSmith!"
        )

    logger.info(f"evaluating dataset: {TASK_MANAGER_DATASET_NAME}")
    memory_saver = MemorySaver()  # Checkpointer for the graph
    memory_store = InMemoryStore()
    agent_config = TaskManagerConfig()

    # Compile the graph - needs checkpointer for stateful execution during evaluation
    graph = TaskManagerGraph(
        checkpointer=memory_saver, store=memory_store, agent_config=agent_config
    ).compiled_graph

    # Define the function to be evaluated for each dataset example
    results = await client.aevaluate(
        create_async_graph_caller_for_task_manager(graph),
        data=TASK_MANAGER_DATASET_NAME,  # The whole dataset is used
        evaluators=[
            llm_judge.create_correctness_evaluator(
                plaintext=True, prompt=TASK_MANAGER_CORRECTNESS_PROMPT
            )
        ],
        experiment_prefix="task-manager-gemini-2.5-correctness-eval-plain",
        num_repetitions=1,
        max_concurrency=4,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"