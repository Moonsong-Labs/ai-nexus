import uuid
from typing import Awaitable, Callable

import pytest
from datasets.task_manager_dataset import (
    TASK_MANAGER_DATASET_NAME as LANGSMITH_DATASET_NAME,
)
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langsmith import Client
from testing import get_logger
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

# from task_manager.graph import builder as graph_builder
from task_manager.graph import TaskManagerGraph
from task_manager.configuration import TASK_MANAGER_MODEL

# Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()


def create_task_manager_graph_caller(
    graph: CompiledStateGraph,
) -> Callable[[dict], Awaitable[dict]]:
    """
    Create a task-manager specific graph caller that properly handles the dataset format.
    This avoids modifying the original graph caller that might be used by other tests.
    """
    logger = get_logger("task_manager_graph_caller")

    async def call_model(inputs: dict):
        # Handle different input formats
        messages = []

        # Case 1: Direct message content
        if "message" in inputs and isinstance(inputs["message"], str):
            content = inputs["message"]
            if content and content.strip():
                messages.append(HumanMessage(content=content))
            else:
                messages.append(HumanMessage(content="Task manager test query"))

        # Case 2: Message object with content
        elif (
            "message" in inputs
            and isinstance(inputs["message"], dict)
            and "content" in inputs["message"]
        ):
            content = inputs["message"]["content"]
            if content and content.strip():
                messages.append(HumanMessage(content=content))
            else:
                messages.append(HumanMessage(content="Task manager test query"))

        # Case 3: Messages array (used by LangSmith dataset)
        elif "messages" in inputs and isinstance(inputs["messages"], list):
            for msg in inputs["messages"]:
                if (
                    isinstance(msg, dict)
                    and "role" in msg
                    and msg["role"] == "human"
                    and "content" in msg
                ):
                    content = msg["content"]
                    if content and content.strip():
                        messages.append(HumanMessage(content=content))

        # Default case if no valid messages were found
        if not messages:
            messages.append(HumanMessage(content="Task manager test query"))

        logger.info(f"Processed messages for task manager: {messages}")

        state = {"messages": messages}

        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "model": TASK_MANAGER_MODEL,
            }
        }

        try:
            result = await graph.ainvoke(state, config=config)

            if isinstance(result, dict) and "messages" in result and result["messages"]:
                return result["messages"][-1].content

            return str(result)
        except Exception as e:
            logger.error(f"Error invoking graph: {e}")
            return f"Error: {str(e)}"

    return call_model


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
    # graph_compiled = graph_builder.compile(checkpointer=MemorySaver())
    graph = TaskManagerGraph(checkpointer=MemorySaver())

    results = await client.aevaluate(
        create_task_manager_graph_caller(
            graph
        ),
        data=LANGSMITH_DATASET_NAME,  # The whole dataset is used
        evaluators=[llm_judge.create_correctness_evaluator(plaintext=True)],
        experiment_prefix="task-manager-gemini-2.5-correctness-eval-plain",
        num_repetitions=4,
        max_concurrency=4,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
