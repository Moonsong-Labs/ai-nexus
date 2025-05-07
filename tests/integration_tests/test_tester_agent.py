import logging
import uuid

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langsmith import Client
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT

# Stop changing this for graph, we need the builder
from tester.graph import builder as tester_graph

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict):
    evaluator = create_llm_as_judge(
        prompt=CORRECTNESS_PROMPT,
        model="google_genai:gemini-2.0-flash-lite",
        feedback_key="correctness",
    )

    try:
        outputs_contents = outputs["output"]

        eval_result = evaluator(
            inputs=inputs,
            outputs=outputs_contents,
            reference_outputs=reference_outputs,
        )
        return eval_result
    except Exception as e:
        pytest.fail(f"Error during evaluation: {e}")
        return 0


@pytest.mark.asyncio
async def test_tester_hello_response():
    """
    Tests the tester agent responds to a hello message without asking questions.
    """

    client = Client()
    # Create both a memory saver for checkpointing and an in-memory store
    memory_saver = MemorySaver()
    memory_store = InMemoryStore()

    # Compile the graph with both the checkpointer and store
    graph_compiled = tester_graph.compile(checkpointer=memory_saver, store=memory_store)

    async def call_tester_agent(input_message: dict):
        # put all this into a try block
        try:
            input_message = input_message["message"]

            result = await graph_compiled.ainvoke(
                {"messages": [HumanMessage(content=input_message)]},
                config={
                    "configurable": {
                        "thread_id": str(uuid.uuid4()),
                        "user_id": "test_user",
                    }
                },
            )
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
        except Exception as invoke_exception:
            logger.error(
                "Error invoking graph for input %s: %s",
                input_message,
                invoke_exception,
                exc_info=True,
            )
            return f"Error during graph execution: {invoke_exception}"

        return output_content

    try:
        logger.info(
            "Testing tester agent with input dataset: tester-agent-test-dataset"
        )
        results = await client.aevaluate(
            call_tester_agent,
            data="tester-agent-test-dataset",
            evaluators=[correctness_evaluator],
            experiment_prefix="tester-agent-hello-response",
            num_repetitions=1,
        )
        logger.info(f"LangSmith Evaluation Results: {results}")

        assert results is not None, "LangSmith evaluation did not return results."

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        pytest.fail(f"Test failed with error: {e}")
