import pytest
from langgraph.checkpoint.memory import MemorySaver
from langsmith import Client
from testing import create_async_graph_caller, get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

from grumpy.graph import builder_no_memory as graph_builder

# Setup basic logging for the test
logger = get_logger(__name__)

# Define the LangSmith dataset ID
LANGSMITH_DATASET_NAME = "grumpy-failed-questions"

# Create a LLMJudge
llm_judge = LLMJudge()

GRUMPY_CORRECTNESS_PROMPT = """You are an expert data labeler evaluating model outputs for correctness.
Your task is to assign a score from 0.0 to 1.0 based on the following rubric:

<Rubric>
  A correct answer:
  - Provides review of the user input
  - Expresses agreement or disagreement with the user input
  - Contains a clear and concise explanation of the reasoning behind the score. No more than 2 sentences.
  - Contains no factual errors
  - Is logically consistent
  - Uses precise and accurate terminology

  When scoring, you should penalize:
  - Factual errors or inaccuracies
  - Missing or unclear score
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
                plaintext=True, prompt=GRUMPY_CORRECTNESS_PROMPT
            )
        ],
        experiment_prefix="grumpy-gemini-2.5-correctness-eval-plain",
        num_repetitions=4,
        max_concurrency=4,
        # metadata={"revision_id": "my-test-run-001"} # Optional: Add metadata
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
