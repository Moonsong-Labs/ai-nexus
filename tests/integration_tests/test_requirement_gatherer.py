import pytest
from datasets.requirement_gatherer_dataset import REQUIREMENT_GATHERER_DATASET_NAME, FIRST_MESSAGE
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langsmith import Client
from testing import create_async_graph_caller_for_gatherer, get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation
import uuid
from langchain_core.messages import ToolMessage

from requirement_gatherer.configuration import Configuration as GathererConfig
from requirement_gatherer.graph import RequirementsGraph

## Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()


REQUIREMENT_GATHERER_CORRECTNESS_PROMPT = """You are an expert data labeler evaluating model outputs for correctness. 
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


@pytest.mark.asyncio
async def test_requirement_gatherer_langsmith(pytestconfig):
    """
    Asynchronously tests the RequirementsGraph agent using LangSmith's evaluation framework.

    This test verifies that the specified LangSmith dataset exists, evaluates the RequirementsGraph agent over the dataset using an LLM-based correctness evaluator, and asserts that evaluation results are produced.
    """
    client = Client()

    if not client.has_dataset(dataset_name=REQUIREMENT_GATHERER_DATASET_NAME):
        logger.error(
            "Dataset %s not found in LangSmith!", REQUIREMENT_GATHERER_DATASET_NAME
        )
        # Print existing datasets for debugging
        datasets = client.list_datasets()
        logger.error("Existing datasets: %s", datasets)
        for dataset in datasets:
            logger.error("Dataset ID: %s, Name: %s", dataset.id, dataset.name)
        pytest.fail(
            f"Dataset {REQUIREMENT_GATHERER_DATASET_NAME} not found in LangSmith!"
        )

    logger.info(f"evaluating dataset: {REQUIREMENT_GATHERER_DATASET_NAME}")
    memory_saver = MemorySaver()  # Checkpointer for the graph
    memory_store = InMemoryStore()
    agent_config = GathererConfig(use_human_ai=True)
    
    # Compile the graph - needs checkpointer for stateful execution during evaluation
    graph = RequirementsGraph(
        checkpointer=memory_saver, store=memory_store, agent_config=agent_config
    ).compiled_graph

    # Define the function to be evaluated for each dataset example
    results = await client.aevaluate(
        create_async_graph_caller_for_gatherer(graph),
        data=REQUIREMENT_GATHERER_DATASET_NAME,  # The whole dataset is used
        evaluators=[
            llm_judge.create_correctness_evaluator(
                plaintext=True, prompt=REQUIREMENT_GATHERER_CORRECTNESS_PROMPT
            )
        ],
        experiment_prefix="requirement-gatherer-gemini-2.5-correctness-eval-plain",
        num_repetitions=1,
        max_concurrency=4,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"


@pytest.mark.asyncio
async def test_requirement_gatherer_ends_with_summarize_tool_call():
    """
    Tests that the RequirementsGraph produces a ToolMessage with name 'summarize'
    as the second to last message.
    """
    logger.info("Testing if requirement gatherer ends with summarize tool call.")
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()
    agent_config = GathererConfig(use_human_ai=True) 

    graph = RequirementsGraph(
        checkpointer=memory_saver, store=memory_store, agent_config=agent_config
    ).compiled_graph

    test_input = {"messages": [{"role": "user", "content": FIRST_MESSAGE}]}
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "model": "google_genai:gemini-2.0-flash-lite",
        }
    }

    result = await graph.ainvoke(test_input, config=config)

    assert result is not None, "Graph did not return a result."
    assert "messages" in result, "Result dictionary does not contain 'messages'."
    assert len(result["messages"]) >= 2, "Graph did not produce at least two messages."

    second_last_message = result["messages"][-2]

    assert isinstance(
        second_last_message, ToolMessage
    ), f"Expected second to last message to be a ToolMessage, got {type(second_last_message).__name__}"
    assert (
        second_last_message.name == "summarize"
    ), f"Expected ToolMessage name to be 'summarize', got '{second_last_message.name}'"

    logger.info("Test for summarize tool call passed successfully.")



