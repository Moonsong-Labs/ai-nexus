"""Common tool for summarizing agent output."""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.types import Command


def create_summarize_tool(agent_name: str) -> BaseTool:
    """Create a tool to register a summary as an agent output summary."""

    # ruff: noqa: T201
    @tool("summarize", parse_docstring=True)
    async def summarize(
        summary: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """Record the given summary as the summary of the agent output.

        Args:
           summary: The entire summary to record.
        """
        print(f"======= Summary for {agent_name} =======")
        print(f"{summary}")
        print("==========================================")

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

    return summarize
