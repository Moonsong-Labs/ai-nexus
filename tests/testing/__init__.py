import logging
import uuid
from typing import Any, Awaitable, Callable

from langgraph.graph.state import CompiledStateGraph
from termcolor import colored


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
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await graph.ainvoke(inputs, config=config)
        return result["messages"][-1].content

    return call_model


async def print_results(results: Any):
    """Print AsyncEvaluationResults."""
    async for result in results:
        run = result["run"]
        eval_result = result["evaluation_results"]["results"][-1]  # get last result

        print(
            f"{colored('run', 'cyan')}#{colored(run.id, 'cyan')} [score: {colored(eval_result.score, 'green')}] ({run.extra['metadata']['num_repetitions']} reps)"
        )

        print("== Input ==")
        for msg in run.inputs["inputs"]["messages"]:
            print(
                f"\t{colored(msg['role'], 'yellow'):<18}: {colored(msg['content'], 'grey')}"
            )

        print("== Output ==")
        print(
            f"\t{colored('ai', 'yellow'):<18}: {colored(run.outputs['output'], 'grey')}"
        )

        print("== Reference Output ==")
        msg_out = result["example"].outputs["message"]
        print(
            f"\t{colored(msg_out['role'], 'yellow'):<18}: {colored(msg_out['content'], 'grey')}"
        )

        print("== Evaluation ==")
        print(f"\t{colored(eval_result.comment, 'grey')}")
        print("---" * 30)


__all__ = [
    get_logger.__name__,
    print_results.__name__,
    create_async_graph_caller.__name__,
]
