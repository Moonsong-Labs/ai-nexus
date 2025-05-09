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
from testing import create_async_graph_caller, get_logger
from testing.evaluators import LLMJudge

from architect.graph import builder as graph_builder

# Setup basic logging for the test
logger = get_logger(__name__)

# Create a LLMJudge
llm_judge = LLMJudge()

ARCHITECT_DATASET_NAME = "Architect-dataset"

@pytest.mark.asyncio
async def test_architect_easy_review_langsmith(pytestconfig):
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

    memory_saver = MemorySaver()  # Checkpointer for the graph
    memory_store = InMemoryStore()

    # Compile the graph - needs checkpointer for stateful execution during evaluation
    graph_compiled = graph_builder.compile(checkpointer=memory_saver, store=memory_store)

    # Define the function to be evaluated for each dataset example
    async def run_graph_with_config(inputs, attachments):
        # Check if the input is already formatted as 'messages'
        if "messages" in inputs and isinstance(inputs["messages"], list):
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
                    for msg in inputs["messages"]
                    # Basic validation: Ensure it's a dict with content before processing
                    if isinstance(msg, dict) and "content" in msg
                    # Call helper and filter out None results inline using assignment expression
                    if (created_msg := _create_message(msg)) is not None
                ]
                # Ensure we have actual messages after conversion
                if not graph_input_messages:
                    logger.error(
                        "Failed to parse messages from example: %s", inputs
                    )
                    return {
                        "output": "Error: Could not parse messages from dataset example."
                    }
                graph_input = {"messages": graph_input_messages}
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
            graph_input_content = inputs["input"]
            graph_input = {"messages": [HumanMessage(content=graph_input_content)]}
        else:
            # Attempt to find another suitable string input key
            input_key = next(
                (k for k in inputs if isinstance(inputs[k], str)), None
            )
            if input_key:
                logger.warning(
                    "Dataset example missing 'messages' and 'input' keys, using '%s': %s",
                    input_key,
                    inputs,
                )
                graph_input_content = inputs[input_key]
                graph_input = {"messages": [HumanMessage(content=graph_input_content)]}
            else:
                logger.error(
                    "Cannot find suitable input key ('messages', 'input', or string) in example: %s",
                    inputs,
                )
                return {"output": "Error: Could not find input in dataset example."}

        # Generate a unique thread_id for each evaluation run
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        try:
            test_message = list()

            # Invoke the graph
            for key, attachment in attachments.items():
                test_message.append(SystemMessage(content=f"These are the contents of the {key} file:\n\n{attachment["reader"].read()}"))

            test_message.extend(graph_input["messages"])
            graph_input = {"messages": test_message}

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
                inputs,
                invoke_exception,
                exc_info=True,
            )
            return f"Error during graph execution: {invoke_exception}"   

    a = client.list_examples(dataset_name=ARCHITECT_DATASET_NAME, example_ids="b82b1d7d-df41-410b-97e4-a38100295489")

    results = await client.aevaluate(
        run_graph_with_config,
        data=ARCHITECT_DATASET_NAME,  # The whole dataset is used
        # data=client.list_examples(  # Only the dev split is used
        #     dataset_name=LANGSMITH_DATASET_NAME, splits=["dev"]
        # ),
        # input_mapper=lambda x: x, # Default is identity, maps dataset example to target input
        evaluators=[llm_judge.create_correctness_evaluator(continuous=False)],
        experiment_prefix="architect-gemini-2.5-correctness-eval",
        num_repetitions=1,
        max_concurrency=4,
        # metadata={"revision_id": "my-test-run-001"} # Optional: Add metadata
    )

    # Assert that results were produced.
    assert results is not None, "evaluation did not return results"
