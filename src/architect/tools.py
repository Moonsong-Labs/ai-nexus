"""Define he agent's tools."""

import uuid
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore

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
        user_id = config["configurable"]["user_id"]
        await store.aput(
            ("memories", user_id),
            key=str(mem_id),
            value={"content": content, "context": context},
        )
        return f"Stored memory {mem_id}"

    return memorize


def create_recall_tool(agent_config: Configuration) -> BaseTool:
    """Create a tool to memorize information into the database."""

    @tool("recall", parse_docstring=True)
    async def recall(
        filename: str,
        store: Annotated[BaseStore, InjectedStore],
        config: Annotated[RunnableConfig, InjectedToolArg],
    ):
        """Find a memory with the filename in the database.

        Args:
            filename: The name of the file in the message. For example:
                "productOverview.md"
        """
        user_id = agent_config.user_id

        file = await store.asearch(
            ("memories", user_id),
            query=filename,
            limit=10,
        )

        return file

    return recall
