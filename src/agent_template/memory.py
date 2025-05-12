"""Memory management for the agent template.

This module provides functionality for managing semantic memories for agents.
It includes tools for loading static memories from files, searching memories,
and managing memory storage with proper namespacing for different users.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

from langchain_core.tools import Tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
from pydantic import BaseModel, Field

from agent_template.configuration import Configuration

logger = logging.getLogger(__name__)

REPO_ROOT = Path(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
STATIC_MEMORIES_DIR = REPO_ROOT / ".langgraph/static_memories/"

# Define valid memory categories
MEMORY_CATEGORIES = [
    "knowledge",  # Facts and information
    "rule",  # Rules, preferences, or constraints
    "procedure",  # How-to knowledge or procedures
]


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


class CategoryMemory(BaseModel):
    """Categorized memory with a specific type."""

    content: str
    category: Literal["knowledge", "rule", "procedure"]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SemanticMemory:
    """Encapsulates semantic memory functionality for an agent."""

    def __init__(
        self,
        agent_name: str = "default",
        store: Optional[BaseStore] = None,
        config: Optional[Configuration] = None,
    ):
        """Initialize the semantic memory.

        Args:
            agent_name: The agent name to use for memory namespace.
            store: Optional BaseStore to use. If None, a new one will be created.
            config: Configuration object with memory settings.
        """
        self.agent_name = agent_name
        self.store = store
        self._tools = None
        self.namespace = (
            "memories",
            "semantic",
        )
        self.initialize(config)

    def initialize(self, config: Optional[Configuration]) -> None:
        """Initialize the memory store and load static memories if configured.

        Args:
            config: Configuration object with memory enablement flags.
        """
        # Initialize the memory store with embeddings
        if self.store is None:
            self.store = create_memory_store()

        # Load static memories if configured
        if config and config.use_static_mem:
            load_static_memories(self.store, config.user_id)
            logger.info(f"Loaded static memories for user {config.user_id}")

    def get_tools(self) -> List[Tool]:
        """Get the memory management tools.

        Returns:
            A list of memory tools for the agent.
        """
        if not self._tools:
            self._tools = create_memory_tools(self.namespace, self.store)
        return self._tools


def create_memory_tools(namespace: str, store: BaseStore) -> List[Tool]:
    """Create memory management and search tools for the agent.

    Args:
        namespace: The namespace to use for memory operations
        store: The memory store to use for tool operations

    Returns:
        A list of memory-related tools (manage and search)
    """

    # Create memory dump tool
    def memory_dump(output_dir: str = "./agent_memories") -> str:
        """Dump all semantic memories associated with the agent to a file.

        Args:
            output_dir: Directory path where the memory dump will be saved

        Returns:
            str: A message indicating the result of the operation
        """
        try:
            memories = []

            # Simply search the current namespace
            try:
                results = store.search(("memories"), query=None, limit=10000)
                memories = [
                    {**m.value, "key": m.key, "namespace": m.namespace} for m in results
                ]
                logger.info(f"Found {len(memories)} memories in namespace {namespace}")
            except Exception as e:
                logger.warning(f"Error searching namespace {namespace}: {str(e)}")

            # Create the output directory
            output_path = Path(output_dir)
            if not output_path.is_absolute():
                output_path = Path.cwd() / output_path

            output_path.mkdir(parents=True, exist_ok=True)

            # Use a simple filename based on the agent name or 'default'
            agent_name = "default"
            if len(namespace) > 1:
                agent_name = namespace[1]

            file_path = output_path / f"memory_dump_{agent_name}.json"

            # Write the file
            with open(file_path, "w") as f:
                json.dump(memories, f, indent=2)

            if len(memories) == 0:
                return f"No memories found. Created empty dump file at {file_path}"
            else:
                return f"Successfully dumped {len(memories)} memories to {file_path}"

        except Exception as e:
            error_msg = f"Error dumping memories: {str(e)}"
            logger.error(error_msg)
            return error_msg

    # Use LangMem's built-in tools with our category schema
    tools = [
        # Tool for storing categorized memories
        create_manage_memory_tool(
            namespace=namespace, store=store, schema=CategoryMemory
        ),
        # Tool for searching memories
        create_search_memory_tool(namespace=namespace, store=store),
        # Custom tool for dumping memories to file
        Tool(
            name="memory_dump",
            description="Dump the agent's semantic memory to a file. If no output directory is specified, uses the default './agent_memories'",
            func=memory_dump,
        ),
    ]
    return tools


def create_memory_store() -> BaseStore:
    """Create a new memory store with Gemini embeddings.

    Returns:
        A new InMemoryStore configured with Gemini embeddings
    """
    gemini_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-exp-03-07"
    )
    return InMemoryStore(
        index={
            "dims": 3072,
            "embed": gemini_embeddings,
        }
    )
