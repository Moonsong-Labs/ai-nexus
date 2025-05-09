"""Memory management for the agent template.

This module provides functionality for managing semantic memories for agents.
It includes tools for loading static memories from files, searching memories,
and managing memory storage with proper namespacing for different users.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import Tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

logger = logging.getLogger(__name__)

REPO_ROOT = Path(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
STATIC_MEMORIES_DIR = REPO_ROOT / ".langgraph/static_memories/"


def load_static_memories(store: BaseStore, user_id: str = "default") -> int:
    """Load static memories directly from the static memories directory into the store.

    Args:
        store: The memory store to load memories into
        user_id: The user ID to use for memory namespace

    Returns:
        Total number of memories loaded
    """
    total_memories_loaded = 0
    for json_file_path in STATIC_MEMORIES_DIR.glob("*.json"):
        try:
            with open(json_file_path) as f:
                memories = json.load(f)

            if not isinstance(memories, list):
                logger.warning(
                    f"Skipping {json_file_path}: content is not a list of memories."
                )
                continue

            for i, memory in enumerate(memories):
                file_name = json_file_path.stem
                memory_key = f"{file_name}_{i}"
                # Using synchronous put method
                store.put(("memories", "static", user_id), memory_key, memory)

            total_memories_loaded += len(memories)
            logger.info(f"Loaded {len(memories)} memories from {json_file_path.name}")
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {json_file_path}")
        except Exception as e:
            logger.error(f"Error loading static memories from {json_file_path}: {e}")

    if total_memories_loaded > 0:
        logger.info(
            f"Loaded {total_memories_loaded} static memories for user {user_id}"
        )
    else:
        logger.info(f"No static memories found or loaded from {STATIC_MEMORIES_DIR}")

    return total_memories_loaded


class SemanticMemory:
    """Encapsulates semantic memory functionality for an agent."""

    def __init__(self, user_id: str = "default", store: Optional[BaseStore] = None):
        """Initialize the semantic memory.

        Args:
            user_id: The user ID to use for memory namespace.
            store: Optional BaseStore to use. If None, a new one will be created.
        """
        self.user_id = user_id
        self.store = store
        self._tools = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the memory store with embeddings."""
        if self.store is None:
            gemini_embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-exp-03-07"
            )
            self.store = InMemoryStore(
                index={
                    "dims": 3072,
                    "embed": gemini_embeddings,
                }
            )

    def get_tools(self) -> List[Tool]:
        """Get the memory management tools.

        Returns:
            A list of memory tools for the agent.
        """
        if not self._tools:
            self._tools = [
                create_manage_memory_tool(
                    namespace=("memories", self.user_id), store=self.store
                ),
                create_search_memory_tool(
                    namespace=("memories", self.user_id), store=self.store
                ),
            ]
        return self._tools

    async def search_memories(self, query: str, limit: int = 5):
        """Search memories based on the query.

        Args:
            query: The search query.
            limit: Maximum number of results to return.

        Returns:
            A list of memory search results.
        """
        return await self.store.asearch(
            ("memories", self.user_id), query=query, limit=limit
        )
