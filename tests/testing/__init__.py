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
        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "model": "google_genai:gemini-2.0-flash-lite",
            }
        }

        result = await graph.ainvoke(inputs, config=config)
        return result["messages"][-1].content
 
    return call_model


__all__ = [
    get_logger.__name__,
    create_async_graph_caller.__name__,
]
