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
from typing import List, Optional

from langchain_core.tools import Tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

from agent_template.configuration import Configuration
from agent_template.tools import create_file_dump_tool

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

    def __init__(self, agent_name: str = "default", store: Optional[BaseStore] = None, config: Optional[Configuration] = None):
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
            self.agent_name,
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

    async def search_memories(self, query: str, user_id: str, limit: int = 5):
        """Search memories based on the query.

        Args:
            query: The search query.
            user_id: The user ID to search memories for.
            limit: Maximum number of results to return.

        Returns:
            A list of memory search results.
        """
        # Create a namespace with the provided user_id
        search_namespace = list(self.namespace)
        
        # Replace the user_id placeholder if it exists
        if "{user_id}" in self.namespace:
            idx = self.namespace.index("{user_id}")
            search_namespace[idx] = user_id
        
        # Convert back to tuple
        search_namespace = tuple(search_namespace)
        
        return await self.store.search(search_namespace, query=query, limit=limit)


def create_memory_tools(namespace: str, store: BaseStore) -> List[Tool]:
    """Create memory management and search tools for the agent.

    Args:
        namespace: The namespace to use for memory operations
        store: The memory store to use for tool operations

    Returns:
        A list of memory-related tools (manage and search)
    """
    # Create the file dumping tool
    file_dump_tool = create_file_dump_tool()
    
    def memory_dump(output_dir: str = "./agent_memories") -> str:
        """Dump all semantic memories associated with the agent to a file.
        
        Args:
            output_dir: Directory path where the memory dump will be saved
                        
        Returns:
            str: A message indicating the result of the operation
        """
        search_prefix = (namespace[0], namespace[1])
        memories = [{**m.value, "key": m.key, "namespace": m.namespace} for m in store.search(search_prefix, query=None, limit=10000)]
        os.makedirs(output_dir, exist_ok=True)
        
        # Use fixed filename for the agent
        file_path = Path(output_dir) / f"memory_dump_{namespace[1]}.json"
        
        # Check if file exists and has the same content
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    existing_memories = json.load(f)
                if existing_memories == memories:
                    return f"Memory content unchanged. No update needed for {file_path}"
            except (json.JSONDecodeError, FileNotFoundError):
                pass  # Proceed with writing if file is invalid
                
        # Write the file only if content changed or file didn't exist
        with open(file_path, 'w') as f:
            json.dump(memories, f, indent=2)
        return f"Successfully dumped {len(memories)} memories to {file_path}"

    tools = [
        create_manage_memory_tool(namespace=namespace, store=store),
        create_search_memory_tool(namespace=namespace, store=store),
        Tool(
            name="memory_dump",
            description="Dump the agent's semantic memory to a file. If no output directory is specified, uses the default './agent_memories'",
            func=memory_dump
        )
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
