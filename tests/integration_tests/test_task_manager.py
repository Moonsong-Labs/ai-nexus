import pytest
from langgraph.checkpoint.memory import MemorySaver
from langsmith import Client
from testing import create_async_graph_caller, get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

from task_manager.graph import builder as graph_builder

# Setup basic logging for the test
logger = get_logger(__name__)

# Define the LangSmith dataset ID
LANGSMITH_DATASET_NAME = "task-manager-requirements"

# Create a LLMJudge
llm_judge = LLMJudge()

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
    graph_compiled = graph_builder.compile(checkpointer=MemorySaver())

    # Generate a unique thread_id for each evaluation run

    results = await client.aevaluate(
        create_async_graph_caller(graph_compiled),
        data=LANGSMITH_DATASET_NAME,  # The whole dataset is used
        # data=client.list_examples(  # Only the dev split is used
        #     dataset_name=LANGSMITH_DATASET_NAME, splits=["dev"]
        # ),
        # input_mapper=lambda x: x, # Default is identity, maps dataset example to target input
        # evaluators=[correctness_evaluator],
        evaluators=[
            llm_judge.create_correctness_evaluator(
                plaintext=True
            )
        ],
        experiment_prefix="task-manager-gemini-2.5-correctness-eval-plain",
        num_repetitions=4,
        max_concurrency=4,
        # metadata={"revision_id": "my-test-run-001"} # Optional: Add metadata
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
