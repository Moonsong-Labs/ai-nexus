import uuid
from functools import partial

import pytest
from datasets.pr_memory_updater_dataset import (
        PR_MEMORY_UPDATER_DATASET_NAME as DATASET_NAME,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langsmith import Client
from testing import get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

from pr_memory_updater.graph import PRMemoryUpdaterGraph
from pr_memory_updater.tools import checkout_and_edit

## Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()

async def eval_target(graph, inputs: dict) -> dict:
        """
        Asynchronously evaluates the PR memory updater graph on a given repository and pull request.
        
        Constructs a unique configuration and invokes the graph to update project memory within a checked-out working directory. Returns the result of the memory update operation, or an error message if the process fails.
        
        Args:
            inputs: A dictionary containing "repository" and "pr_num" keys specifying the target repository and pull request number.
        
        Returns:
            A dictionary with the key "output" containing the result of the memory update, or an error message and an "error" flag if an exception occurs.
        """
        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
            }
        }

        # TODO: use PR details JSON as part of dataset input?
        repo = inputs["repository"]
        pr = inputs["pr_num"]

        async def invoke_memory_updater(dir):
            """
            Sends a user message to the PR memory updater agent to update project memory for a specific repository and pull request in the given working directory.
            
            Args:
                dir: The working directory path where the memory update should be performed.
            """
            messages = {
                "messages": [{
                    "role": "user",
                    "content": f"Update the project memory. The repo is {repo} and the PR is number {pr}. Working directory is: {dir}"
                }]
            }

            try:
                await graph.ainvoke(messages, config)
            except Exception as e:
                logger.error(f"Failed to invoke agent: {str(e)}")

        try:
            result = await checkout_and_edit(repo, pr, thunk=invoke_memory_updater)
            return {"output": result}
        except Exception as e:
            logger.error(
                f"Error while updating project {repo} memory for PR #{pr}: {str(e)}"
            )
            return {
                "output": f"Error while updating project memory: {str(e)}",
                "error": True,
            }

@pytest.mark.asyncio
async def test_pr_memory_updater(pytestconfig):
    """
    Asynchronously evaluates the PR Memory Updater agent on a LangSmith dataset and verifies results.
    
    This test checks for the existence of the required dataset in LangSmith, runs the PR Memory Updater agent over the dataset using an LLM-based correctness evaluator, prints detailed evaluation results, and asserts that evaluation results are produced.
    """
    client = Client()

    if not client.has_dataset(dataset_name=DATASET_NAME):
        logger.error("Dataset %s not found in LangSmith!", DATASET_NAME)
        # Print existing datasets for debugging
        datasets = client.list_datasets()
        logger.error("Existing datasets: %s", datasets)
        for dataset in datasets:
            logger.error("Dataset ID: %s, Name: %s", dataset.id, dataset.name)
        pytest.fail(f"Dataset {DATASET_NAME} not found in LangSmith!")

    logger.info(f"evaluating dataset: {DATASET_NAME}")

    memory_saver = MemorySaver()  # Checkpointer for the graph
    memory_store = InMemoryStore()

    # Compile the graph - needs checkpointer for stateful execution during evaluation
    graph = PRMemoryUpdaterGraph(
        checkpointer=memory_saver, store=memory_store
    ).compiled_graph

    # Define the function to be evaluated for each dataset example
    results = await client.aevaluate(
        partial(eval_target, graph),
        data=DATASET_NAME,  # The whole dataset is used
        evaluators=[llm_judge.create_correctness_evaluator()],
        experiment_prefix="pr-memory-updater-graph-gemini-2.5-flash-correctness-eval",
        num_repetitions=1,
        max_concurrency=4,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
