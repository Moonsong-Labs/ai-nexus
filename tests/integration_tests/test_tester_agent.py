import pytest
from langgraph.checkpoint.memory import MemorySaver
from langsmith import Client
from testing import create_async_graph_caller, get_logger
from testing.evaluators import LLMJudge

from deprecated_tester.graph import builder as tester_graph_builder

# Setup basic logging for the test
logger = get_logger(__name__)

# Define the LangSmith dataset ID
LANGSMITH_DATASET_NAME = "tester-agent-test-dataset"
CORRECTNESS_PROMPT = """You are an expert data labeler evaluating model outputs for correctness.
Your task is to assign a score from 0.0 to 1.0 based on the following rubric:

<Rubric>
  A correct tester agent response:
  - Properly analyzes requirements and identifies ambiguities
  - Asks clear, relevant questions when information is missing or unclear
  - Generates comprehensive tests that verify system behavior according to requirements
  - Provides proper traceability between tests and requirements
  - Includes both happy path tests and edge case tests
  - Does not invent business rules or make assumptions beyond what is stated
  - Does not define code architecture or suggest design changes

  When scoring, you should penalize:
  - Making assumptions about functionality that is not explicitly stated
  - Inventing business rules or behaviors
  - Generating tests without proper requirement traceability
  - Missing important edge cases that should be tested
  - Failing to ask questions when requirements are ambiguous
  - Excessive verbosity or unnecessary details
</Rubric>

<Instructions>
  - Carefully read the input and output
  - Focus on how well the agent generates questions or tests based on the requirements
</Instructions>

<Reminder>
  The goal is to evaluate how well the Test Agent performs its role in generating tests based on requirements.
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

# Create a LLMJudge
llm_judge = LLMJudge()


@pytest.mark.asyncio
async def test_tester_agent_langsmith(pytestconfig):
    """
    Tests the tester agent graph using langsmith.aevaluate against a LangSmith dataset.
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

    graph_compiled = tester_graph_builder.compile(checkpointer=MemorySaver())

    results = await client.aevaluate(
        create_async_graph_caller(graph_compiled),
        data=LANGSMITH_DATASET_NAME,
        evaluators=[
            llm_judge.create_correctness_evaluator(
                plaintext=False, prompt=CORRECTNESS_PROMPT
            )
        ],
        experiment_prefix="tester-agent-correctness-eval",
        num_repetitions=3,
        max_concurrency=2,
    )

    # Assert that results were produced
    assert results is not None, "evaluation did not return results"
