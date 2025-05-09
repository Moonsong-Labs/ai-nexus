import logging
import uuid
from typing import Awaitable, Callable

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph


def get_logger(name=None, *, level: int | str = logging.INFO) -> logging.Logger:
    """Create a logger with default format."""
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(name)

    # setting root level does not currently work.
    logger.setLevel(level)

    return logger


def create_async_graph_caller(
    graph: CompiledStateGraph,
) -> Callable[[dict], Awaitable[dict]]:
    """
    Create a basic graph caller that calls ainvoke on the dataset inputs with the provided config.
    Returns the last message.
    """

    async def call_model(inputs: dict):
        # Prepare inputs - make sure we have a properly formatted message
        input_message = inputs.get("message", "")
        if isinstance(input_message, dict) and "content" in input_message:
            input_content = input_message["content"]
        else:
            input_content = str(input_message)

        # Create a proper state with formatted messages
        state = {"messages": [HumanMessage(content=input_content)]}

        # Set up config with thread_id and model
        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "model": "google_genai:gemini-2.0-flash-lite",
            }
        }

        # Invoke the graph
        result = await graph.ainvoke(state, config=config)

        # Return the last message's content
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            return result["messages"][-1].content

        return str(result)

    return call_model


__all__ = [
    get_logger.__name__,
    create_async_graph_caller.__name__,
]
