import uuid

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langsmith import Client
from testing import create_async_graph_caller, get_logger
from testing.evaluators import LLMJudge

from grumpy.graph import builder_no_memory as graph_builder

# Setup basic logging for the test
logger = get_logger(__name__)

# Define the LangSmith dataset ID
LANGSMITH_DATASET_NAME = "grumpy-failed-questions"

# Create a LLMJudge
llm_judge = LLMJudge()


@pytest.mark.asyncio
async def test_grumpy_easy_review_langsmith(pytestconfig):
    """
    Tests the grumpy agent graph using langsmith.aevaluate against a LangSmith dataset.
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
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    results = await client.aevaluate(
        create_async_graph_caller(graph_compiled, config),
        data=LANGSMITH_DATASET_NAME,  # The whole dataset is used
        # data=client.list_examples(  # Only the dev split is used
        #     dataset_name=LANGSMITH_DATASET_NAME, splits=["dev"]
        # ),
        # input_mapper=lambda x: x, # Default is identity, maps dataset example to target input
        # evaluators=[correctness_evaluator],
        evaluators=[
            llm_judge.create_correctness_evaluator(plaintext=True, continuous=False)
        ],
        experiment_prefix="grumpy-gemini-2.5-correctness-eval-plain",
        num_repetitions=10,
        max_concurrency=4,
        # metadata={"revision_id": "my-test-run-001"} # Optional: Add metadata
    )

    # View results
    # import pprint
    # async for result in results:
    #     pprint.pp(result)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
