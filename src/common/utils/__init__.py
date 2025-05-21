"""Utility functions used in our graph."""

from langchain_core.messages import AnyMessage
from termcolor import colored


def split_model_and_provider(fully_specified_name: str) -> dict:
    """Initialize the configured chat model."""
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = None
        model = fully_specified_name
    return {"model": model, "provider": provider}


def format_message(msg: AnyMessage, *, actor: str = None):
    """Format a message for printing."""
    content = msg.content
    if actor is None:
        actor = msg.type.upper()
    if msg.tool_calls:
        tool_calls = ",".join(
            [f"{colored(tc["name"], "cyan")}" for tc in msg.tool_calls]
        )
        tool_calls = f"tool(s): {tool_calls}"
        if content == "":
            content = tool_calls
        else:
            content = f"{content}\n{tool_calls}"
    return f"\n{'=' * 50} {actor:^15} {'=' * 50}\n{content}\n{'=' * 112}\n"
