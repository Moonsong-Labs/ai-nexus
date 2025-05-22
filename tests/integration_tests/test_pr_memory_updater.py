
import pytest
from datasets.pr_memory_updater_dataset import PR_MEMORY_UPDATER_DATASET_NAME as DATASET_NAME
from langsmith import Client
from testing import get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

from pr_memory_updater.tools import invoke_project_memory_from_pr

# from requirement_gatherer.graph import RequirementsGraph

## Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()

@pytest.mark.asyncio
async def test_pr_memory_updater(pytestconfig):
    """
    Asynchronously tests the PR Memory Updater agent using LangSmith's evaluation framework.

    This test verifies that the specified LangSmith dataset exists, evaluates the PR Memory Updater agent over the dataset using an LLM-based correctness evaluator, and asserts that evaluation results are produced.
    """
    client = Client()

    if not client.has_dataset(dataset_name=DATASET_NAME):
        logger.error(
            "Dataset %s not found in LangSmith!", DATASET_NAME
        )
        # Print existing datasets for debugging
        datasets = client.list_datasets()
        logger.error("Existing datasets: %s", datasets)
        for dataset in datasets:
            logger.error("Dataset ID: %s, Name: %s", dataset.id, dataset.name)
        pytest.fail(
            f"Dataset {DATASET_NAME} not found in LangSmith!"
        )

    logger.info(f"evaluating dataset: {DATASET_NAME}")
    # memory_saver = MemorySaver()  # Checkpointer for the graph
    # memory_store = InMemoryStore()

    # # Compile the graph - needs checkpointer for stateful execution during evaluation
    # graph = RequirementsGraph(
    #     checkpointer=memory_saver, store=memory_store
    # ).compiled_graph

    # target = create_async_graph_caller(graph)

    async def target(inputs: dict) -> dict:
        #TODO: use PR details JSON as part of dataset input?
        result = invoke_project_memory_from_pr(inputs["repository"], inputs["pr_num"])
        return { "output": result }

    # Define the function to be evaluated for each dataset example
    results = await client.aevaluate(
        target,
        data=DATASET_NAME,  # The whole dataset is used
        evaluators=[
            llm_judge.create_correctness_evaluator()
        ],
        # Using `script` until we migrate to graph-based agent
        experiment_prefix="pr-memory-updater-script-gemini-2.5-correctness-eval",
        num_repetitions=4,
        max_concurrency=4,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
