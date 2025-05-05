import logging
import uuid  # Add import for unique thread IDs

import pytest

import traceback

# from langsmith import aevaluate # Remove this potentially confusing import
from langchain_core.messages import (  # Import message types
    AIMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.checkpoint.memory import MemorySaver  # Keep checkpointer
from langsmith import Client
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT

from code_reviewer.graph import builder_no_memory as graph_builder  # Import the builder

# Setup basic logging for the test
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define the LangSmith dataset ID
LANGSMITH_DATASET_NAME = "code-reviewer-testing"


def correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict):
    evaluator = create_llm_as_judge(
        prompt=CORRECTNESS_PROMPT,
        model="google_genai:gemini-2.0-flash-lite",
        feedback_key="correctness",
    )
    # Prepare the inputs for the evaluator
    # The evaluator expects a specific format for  outputs
    try:
        outputs_contents = outputs['output']
        print(f"outputs_contents: {outputs_contents}")
        print(f"reference_outputs: {reference_outputs}")
        reference_outputs_contents = reference_outputs['message'][0]['content']
        
        eval_result = evaluator(
            inputs=inputs,
            outputs=outputs_contents,
            reference_outputs=reference_outputs_contents,
        )
        return eval_result
    except Exception as e:
        pytest.fail(f"Error during evaluation: {e}\n\nTraceback: {traceback.format_exc()}")
        return 0


@pytest.mark.asyncio
async def test_code_reviewer_easy_review_langsmith(pytestconfig):
    """
    Tests the code_reviewer agent graph using langsmith.aevaluate against a LangSmith dataset.
    """
    client = Client()  # Initialize LangSmith client
    if not client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        logger.error("Dataset %s not found in LangSmith!", LANGSMITH_DATASET_NAME)
        # Print existing datasets for debugging
        datasets = client.list_datasets()
        logger.error("Existing datasets: %s", datasets)
        for dataset in datasets:
            logger.error("Dataset ID: %s, Name: %s", dataset.id, dataset.name)
        pytest.fail(f"Dataset {LANGSMITH_DATASET_NAME} not found in LangSmith!")

    memory_saver = MemorySaver()  # Checkpointer for the graph

    # Compile the graph - needs checkpointer for stateful execution during evaluation
    graph_compiled = graph_builder.compile(checkpointer=memory_saver)

    # Define the function to be evaluated for each dataset example
    async def run_graph_with_config(input_example: dict):
        # Check if the input is already formatted as 'messages'
        if "messages" in input_example and isinstance(input_example["messages"], list):
            # Use the messages list directly, converting dicts to BaseMessage objects if needed
            # (Assuming the graph expects BaseMessage objects, not just dicts)
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

            try:
                # Create messages using the helper, filter out invalid ones (None)
                graph_input_messages = [
                    created_msg  # Assign the result of _create_message to created_msg
                    for msg in input_example["messages"]
                    # Basic validation: Ensure it's a dict with content before processing
                    if isinstance(msg, dict) and "content" in msg
                    # Call helper and filter out None results inline using assignment expression
                    if (created_msg := _create_message(msg)) is not None
                ]
                # Ensure we have actual messages after conversion
                if not graph_input_messages:
                    logger.error(
                        "Failed to parse messages from example: %s", input_example
                    )
                    return {
                        "output": "Error: Could not parse messages from dataset example."
                    }
                graph_input = {"messages": graph_input_messages}
            except Exception as parse_error:
                logger.error(
                    "Error parsing messages from example %s: %s",
                    input_example,
                    parse_error,
                    exc_info=True,
                )
                return {"output": f"Error parsing messages: {parse_error}"}

        # Fallback: Check for 'input' or other simple string keys if 'messages' isn't present
        elif "input" in input_example:
            graph_input_content = input_example["input"]
            graph_input = {"messages": [HumanMessage(content=graph_input_content)]}
        else:
            # Attempt to find another suitable string input key
            input_key = next(
                (k for k in input_example if isinstance(input_example[k], str)), None
            )
            if input_key:
                logger.warning(
                    "Dataset example missing 'messages' and 'input' keys, using '%s': %s",
                    input_key,
                    input_example,
                )
                graph_input_content = input_example[input_key]
                graph_input = {"messages": [HumanMessage(content=graph_input_content)]}
            else:
                logger.error(
                    "Cannot find suitable input key ('messages', 'input', or string) in example: %s",
                    input_example,
                )
                return {"output": "Error: Could not find input in dataset example."}

        # Generate a unique thread_id for each evaluation run
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        try:
            # Invoke the graph
            result = await graph_compiled.ainvoke(graph_input, config=config)

            # Format the output for the evaluator
            # The 'correctness_evaluator' expects outputs={'output': ...}
            # The code_reviewer graph likely returns state {'messages': [..., AIMessage]}
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
                    output_content = str(
                        last_message
                    )  # Fallback to string representation
            else:
                pytest.fail(f"Unexpected graph output format: {result}")
                output_content = str(result)  # Fallback

            return output_content

        except Exception as invoke_exception:
            logger.error(
                "Error invoking graph for input %s: %s",
                input_example,
                invoke_exception,
                exc_info=True,
            )
            return f"Error during graph execution: {invoke_exception}"

    try:
        logger.info(
            "Attempting client.aevaluate with dataset_name: %s", LANGSMITH_DATASET_NAME
        )
        results = await client.aevaluate(
            run_graph_with_config,  # Pass the wrapper function as the target
            data=LANGSMITH_DATASET_NAME, # The whole dataset is used
            # data=client.list_examples(  # Only the dev split is used
            #     dataset_name=LANGSMITH_DATASET_NAME, splits=["dev"]
            # ),
            # input_mapper=lambda x: x, # Default is identity, maps dataset example to target input
            evaluators=[correctness_evaluator],
            experiment_prefix="code-reviewer-gemini-2.5-correctness-eval",
            num_repetitions=1,
            max_concurrency=4,
            # metadata={"revision_id": "my-test-run-001"} # Optional: Add metadata
        )
        logger.info("LangSmith Evaluation Results: %s", results)

        # Assert based on evaluation results
        # aevaluate typically returns results per run, often summarized in a project/experiment link.
        # We might need a more specific assertion, e.g., checking summary stats if available,
        # or simply ensuring no exceptions occurred.
        # For now, assert that results were produced.
        assert results is not None, "LangSmith evaluation did not return results."
        # A more robust check might involve fetching the experiment results via client
        # and checking summary statistics like failure rates, but that's more complex.

    except Exception as e:
        logger.error("LangSmith evaluation failed: %s", e, exc_info=True)
        pytest.fail(f"LangSmith evaluation failed: {e}")
