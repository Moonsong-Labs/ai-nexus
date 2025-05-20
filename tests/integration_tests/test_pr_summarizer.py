import subprocess
import tempfile

import pytest
from datasets.pr_summarizer_dataset import PR_SUMMARIZER_DATASET_NAME as DATASET_NAME
from langsmith import Client
from testing import get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

# from requirement_gatherer.graph import RequirementsGraph

## Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()

def invoke_project_memory_from_pr(repo: str, pr: str) -> str:
    """
    Invoke the `update_project_memory_from_pr` script

    Will take care of checking out the PR in a temporary directory and doing the necessary setup for the script to run

    Will return a diff of the applied changes from the agent
    """
    #TODO: ensure GEMINI_API_KEY is set?
    #TODO: ensure git, gh, jq, curl are available?
    #TODO: ensure gh is authenticated?

    # retrieve last commit of the PR to create checkout from
    # choosing this instead of `main` to avoid out-of-sync PRs
    result = subprocess.run(f"gh pr view {pr} -R {repo} --json commits | jq '.commits | last | .oid'", shell=True,  capture_output=True)

    # drop trailing newline
    rev = result.stdout.decode('utf-8').strip()

    memory_changes = None

    # script excepts to be run in a checkout
    # so set it up for given PR at tmpdir to not pollute environment
    with tempfile.TemporaryDirectory() as dir:
        subprocess.run(f"git clone https://github.com/{repo} --depth=1 --revision={rev} .", shell=True, cwd=dir)

        # mark scripts as runnable
        subprocess.run("chmod +x ./scripts/update_project_memory_from_pr.sh ./scripts/fetch_pr_details.sh", shell=True, cwd=dir)

        # invoke scripts/update_project_memory_from_pr.sh
        subprocess.run(f"./scripts/update_project_memory_from_pr.sh -r {repo} -p {pr}", shell=True, cwd=dir)

        # retrieve the updates that were made from the script
        memory_changes = subprocess.run("git diff", shell=True, cwd=dir, capture_output=True).stdout.decode('utf-8').strip()

    return memory_changes


@pytest.mark.asyncio
async def test_pr_summarizer(pytestconfig):
    """
    Asynchronously tests the PR Summarizer agent using LangSmith's evaluation framework.

    This test verifies that the specified LangSmith dataset exists, evaluates the PR Summarizer agent over the dataset using an LLM-based correctness evaluator, and asserts that evaluation results are produced.
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
        experiment_prefix="pr-summarizer-gemini-2.5-correctness-eval-plain",
        num_repetitions=4,
        max_concurrency=4,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
