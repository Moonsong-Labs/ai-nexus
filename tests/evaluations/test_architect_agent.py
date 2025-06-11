import uuid

import pytest
from langchain_core.messages import (  # Import message types
    AIMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langsmith import Client
from testing.evaluators import LLMJudge
from testing.formatter import Verbosity, print_evaluation

from architect.graph import ArchitectGraph
from common.logging import get_logger

# Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()

ARCHITECT_DATASET_NAME = "Architect-dataset"

ARCHITECT_CORRECTNESS_PROMPT = """You are an expert data labeler evaluating model outputs for correctness.
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
async def test_architect_write_system_requirements(pytestconfig):
    """
    Tests the architect agent graph using langsmith.aevaluate against a LangSmith dataset.
    """
    client = Client()

    if not client.has_dataset(dataset_name=ARCHITECT_DATASET_NAME):
        logger.error(f"dataset {ARCHITECT_DATASET_NAME} not found")
        datasets = list(client.list_datasets())
        logger.error(f"found {len(datasets)} existing datasets")
        for dataset in datasets:
            logger.error(f"\tid: {dataset.id}, name: {dataset.name}")
        pytest.fail(f"dataset {ARCHITECT_DATASET_NAME} not found")

    logger.info(f"evaluating dataset: {ARCHITECT_DATASET_NAME}")

    results = await client.aevaluate(
        run_graph_with_attachments,
        data=[client.read_example(example_id="ecadfbbe-bd5b-4108-aba7-8525cec7012e")],
        evaluators=[
            llm_judge.create_correctness_evaluator(
                plaintext=True, prompt=ARCHITECT_CORRECTNESS_PROMPT
            )
        ],
        experiment_prefix="architect-gemini-2.5-correctness-eval",
        num_repetitions=1,
        max_concurrency=4,
    )

    await print_evaluation(results, client, verbosity=Verbosity.SCORE_DETAILED)

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"


@pytest.mark.asyncio
async def test_architect_whole_dataset(pytestconfig):
    """
    Tests the architect agent graph using langsmith.aevaluate against a LangSmith dataset.
    """
    client = Client()

    if not client.has_dataset(dataset_name=ARCHITECT_DATASET_NAME):
        logger.error(f"dataset {ARCHITECT_DATASET_NAME} not found")
        datasets = list(client.list_datasets())
        logger.error(f"found {len(datasets)} existing datasets")
        for dataset in datasets:
            logger.error(f"\tid: {dataset.id}, name: {dataset.name}")
        pytest.fail(f"dataset {ARCHITECT_DATASET_NAME} not found")

    logger.info(f"evaluating dataset: {ARCHITECT_DATASET_NAME}")

    results = await client.aevaluate(
        run_graph_with_attachments,
        data=ARCHITECT_DATASET_NAME,
        evaluators=[
            llm_judge.create_correctness_evaluator(
                plaintext=True, prompt=ARCHITECT_CORRECTNESS_PROMPT
            )
        ],
        experiment_prefix="architect-gemini-2.5-correctness-eval",
        num_repetitions=1,
        max_concurrency=4,
    )

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"


# This function loads text files before the human prompt of
# the experiment to properly give context to the agent
async def run_graph_with_attachments(inputs: dict, attachments: dict):
    memory_saver = MemorySaver()  # Checkpointer for the graph
    memory_store = InMemoryStore()

    # Compile the graph - needs checkpointer for stateful execution during evaluation
    graph_compiled = ArchitectGraph(
        checkpointer=memory_saver, store=memory_store
    ).compiled_graph
    # Check if the input is already formatted as 'messages'
    if "messages" in inputs and isinstance(inputs["messages"], list):
        # Use the messages list directly, converting dicts to BaseMessage objects if needed
        # (Assuming the graph expects BaseMessage objects, not just dicts)
        try:
            # Create messages using the helper, filter out invalid ones (None)
            graph_input_messages = [
                created_msg  # Assign the result of _create_message to created_msg
                for msg in inputs["messages"]
                # Basic validation: Ensure it's a dict with content before processing
                if isinstance(msg, dict) and "content" in msg
                # Call helper and filter out None results inline using assignment expression
                if (created_msg := _create_message(msg)) is not None
            ]
            # Ensure we have actual messages after conversion
            if not graph_input_messages:
                logger.error("Failed to parse messages from example: %s", inputs)
                return {
                    "output": "Error: Could not parse messages from dataset example."
                }
        except Exception as parse_error:
            logger.error(
                "Error parsing messages from example %s: %s",
                inputs,
                parse_error,
                exc_info=True,
            )
            return {"output": f"Error parsing messages: {parse_error}"}

    # Fallback: Check for 'input' or other simple string keys if 'messages' isn't present
    elif "input" in inputs:
        graph_input_messages = [HumanMessage(content=inputs["input"])]
    else:
        # Attempt to find another suitable string input key
        input_key = next((k for k in inputs if isinstance(inputs[k], str)), None)
        if input_key:
            logger.warning(
                "Dataset example missing 'messages' and 'input' keys, using '%s': %s",
                input_key,
                inputs,
            )
            graph_input_messages = [HumanMessage(content=inputs[input_key])]
        else:
            logger.error(
                "Cannot find suitable input key ('messages', 'input', or string) in example: %s",
                inputs,
            )
            return {"output": "Error: Could not find input in dataset example."}

    # Generate a unique thread_id for each evaluation run
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    try:
        graph_attachments = list()

        # Adds attachments as System Messages before the human message
        for key, attachment in attachments.items():
            graph_attachments.append(
                SystemMessage(
                    content=f"These are the contents of the {key} file:\n\n{attachment['reader'].read()}"
                )
            )

        graph_attachments.extend(graph_input_messages)
        graph_input = {"messages": graph_attachments}

        # Invoke the graph
        result = await graph_compiled.ainvoke(graph_input, config=config)

        # Format the output for the evaluator
        # The 'correctness_evaluator' expects outputs={'output': ...}
        # The architect graph likely returns state {'messages': [..., AIMessage]}
        output_content = "Error: Graph did not return expected output format."  # Default error message
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if isinstance(last_message, AIMessage):
                output_content = last_message.content
            elif hasattr(
                last_message, "content"
            ):  # Handle other message types if needed
                output_content = last_message.content
            else:
                logger.warning(
                    "Last message is not AIMessage or lacks content: %s",
                    last_message,
                )
                output_content = str(last_message)  # Fallback to string representation
        else:
            pytest.fail(f"Unexpected graph output format: {result}")
            output_content = str(result)  # Fallback

        return output_content

    except Exception as invoke_exception:
        logger.error(
            "Error invoking graph for input %s: %s",
            inputs,
            invoke_exception,
            exc_info=True,
        )
        return f"Error during graph execution: {invoke_exception}"


# Helper function to create message objects with type checking
def _create_message(msg_dict: dict):
    """Creates BaseMessage objects (Human, AI, System, Chat) from dict, returns None if role is invalid or data missing."""
    message_role = msg_dict.get("role")
    if message_role == "human":
        # Assuming HumanMessage constructor handles potential missing keys robustly,
        # or add specific key checks here if needed.
        return HumanMessage(**msg_dict)
    elif message_role == "ai":
        return AIMessage(**msg_dict)
    elif message_role == "system":
        return SystemMessage(**msg_dict)
    elif message_role == "chat":
        if "role" in msg_dict:
            return ChatMessage(**msg_dict)
        else:
            logger.warning(
                "ChatMessage role specified but 'role' key missing in test data msg: %s. Skipping.",
                msg_dict,
            )
            return None
    else:
        # Log and return None for invalid roles to be filtered out later
        logger.warning(
            "Invalid or missing message role '%s' in test data msg: %s. Skipping.",
            message_role,
            msg_dict,
        )
        return None
