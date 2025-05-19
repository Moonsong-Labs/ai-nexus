"""Define he agent's tools."""

import uuid
from typing import Annotated, Optional

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from langgraph.types import Command

from architect.configuration import Configuration


def create_memorize_tool(agent_config: Configuration) -> BaseTool:
    """Create a tool to memorize information into the database."""

    @tool("memorize", parse_docstring=True)
    async def memorize(
        content: str,
        context: str,
        store: Annotated[BaseStore, InjectedStore],
        config: Annotated[RunnableConfig, InjectedToolArg],
        memory_id: Optional[uuid.UUID] = None,
    ):
        """Upsert a memory in the database.

        If a memory conflicts with an existing one, then just UPDATE the
        existing one by passing in memory_id - don't create two memories
        that are the same. If the user corrects a memory, UPDATE it.

        Args:
            content: The main content of the memory. For example:
                "User expressed interest in learning about French."
            context: Additional context for the memory. For example:
                "This was mentioned while discussing career options in Europe."
            memory_id: ONLY PROVIDE IF UPDATING AN EXISTING MEMORY.
            The memory to overwrite.
        """
        mem_id = memory_id or uuid.uuid4()
        user_id = agent_config.user_id
        await store.aput(
            ("memories", user_id),
            key=str(mem_id),
            value={"content": content, "context": context},
        )
        return f"Stored memory {mem_id}"

    return memorize


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
