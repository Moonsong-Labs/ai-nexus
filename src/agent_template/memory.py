"""Missing docs."""

import json
import logging
from pathlib import Path

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool

logger = logging.getLogger(__name__)

# Define the directory where static memory files are stored
STATIC_MEMORIES_DIR = Path(".langgraph/static_memories/")


def get_langmem_tools(user_id: str) -> list:
    """Create and return a list of memory tools for the agent.

    Initializes an in-memory store with Gemini embeddings and creates
    management and search tools for the specified user ID.

    Args:
        user_id (str): The user ID for which to create the memory tools.

    Returns:
        list: A list of memory tools for the agent.
    """
    gemini_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-exp-03-07"
    )

    store = InMemoryStore(
        index={
            "dims": 3072,
            "embed": gemini_embeddings,
        }
    )

    memory_tools = [
        create_manage_memory_tool(namespace=("memories", user_id), store=store),
        create_search_memory_tool(namespace=("memories", user_id), store=store),
    ]

    return memory_tools


async def _load_memories_from_directory(directory_path: Path, store: BaseStore):
    """Load memories from all JSON files in the specified directory into the store."""
    if not directory_path.is_dir():
        logger.warning(f"Static memories directory not found at {directory_path}")
        return

    total_memories_loaded = 0
    for json_file_path in directory_path.glob("*.json"):
        try:
            with open(json_file_path) as f:
                memories = json.load(f)

            if not isinstance(memories, list):
                logger.warning(
                    f"Skipping {json_file_path}: content is not a list of memories."
                )
                continue

            # Add each memory from the current file to the store
            for i, memory in enumerate(memories):
                # Use a unique key combining filename and index
                file_name = json_file_path.stem
                memory_key = f"{file_name}_{i}"
                # Use positional arguments for aput
                await store.aput(("static_memories", "global"), memory_key, memory)
            logger.info(f"Loaded {len(memories)} memories from {json_file_path.name}")
            total_memories_loaded += len(memories)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {json_file_path}")
        except Exception as e:
            logger.error(f"Error loading static memories from {json_file_path}: {e}")

    if total_memories_loaded > 0:
        logger.info(
            f"Finished loading static memories. Total loaded: {total_memories_loaded}"
        )
    else:
        logger.info("No static memories found or loaded from the directory.")


async def ensure_static_memories(store: BaseStore):
    """Ensure static memories are loaded in the store by checking existence and loading if necessary."""
    # Check if any static memories exist
    try:
        # Try passing only namespace positionally, rest as keywords
        static_memories = await store.asearch(
            ("static_memories", "global"), query="", limit=1
        )
        if static_memories:
            logger.debug("Static memories already exist in store, skipping load.")
            return
    except Exception as e:
        # Log the error but proceed, as the store might be empty or have issues
        logger.warning(
            f"Could not check for existing static memories, proceeding to load: {e}"
        )

    # Define the directory and load memories
    logger.info("Attempting to load static memories into store.")
    await _load_memories_from_directory(STATIC_MEMORIES_DIR, store)


def format_static_memories_for_prompt(static_memories: list) -> str:
    """Format a list of static memories for inclusion in a prompt.

    Args:
        static_memories: A list of memory objects, typically from store.asearch.

    Returns:
        A string formatted for inclusion in the LLM prompt, or an empty string
        if no relevant memories are found.
    """
    if not static_memories:
        return ""

    memory_texts = []
    # Add user memories (note: the original code calls these "user memories" but they are static_memories)
    for mem in static_memories:
        memory_text = f"[{mem.key}]: {mem.value} (similarity: {mem.score})"
        memory_texts.append(memory_text)

    formatted_str = "\n".join(memory_texts)

    # Add static memories with special formatting
    # This part seems redundant or mislabeled in the original code, as static_memories
    # are already being processed. Assuming the intent was to format them in a specific way
    # if they exist.
    static_memory_texts_special = []
    for mem in static_memories:
        content = mem.value.get("content", "No content")
        context = mem.value.get("context", "No context")
        memory_text = f"[{mem.key}]: content: {content}, context: {context}"
        static_memory_texts_special.append(memory_text)

    if static_memory_texts_special:
        if formatted_str:
            formatted_str += "\n\n<static_memories>\n"
        else:
            formatted_str = "<static_memories>\n"

        formatted_str += "\n".join(static_memory_texts_special)
        formatted_str += "\n</static_memories>"

    if formatted_str:
        return f"""
<memories>
{formatted_str}
</memories>"""
    return ""
