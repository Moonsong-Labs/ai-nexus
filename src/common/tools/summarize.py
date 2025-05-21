"""Common tool for summarizing agent output."""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command


# ruff: noqa: T201
@tool("summarize", parse_docstring=True)
async def summarize(
    summary: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Summarize the agent output.

    Args:
        summary: The entire summary.
    """
    print("=== Summary ===")
    print(f"{summary}")
    print("=================")

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=summary,
                    tool_call_id=tool_call_id,
                )
            ],
            "summary": summary,
        }
    )
