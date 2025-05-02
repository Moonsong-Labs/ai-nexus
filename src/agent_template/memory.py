import json
import logging
from pathlib import Path

from langgraph.store.base import BaseStore

logger = logging.getLogger(__name__)

# Define the directory where static memory files are stored
STATIC_MEMORIES_DIR = Path(".langgraph/static_memories/")


async def _load_memories_from_directory(directory_path: Path, store: BaseStore):
    """Load memories from all JSON files in the specified directory into the store."""
    if not directory_path.is_dir():
        logger.warning(f"Static memories directory not found at {directory_path}")
        return

    total_memories_loaded = 0
    for json_file_path in directory_path.glob("*.json"):
        try:
            with open(json_file_path, "r") as f:
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
        static_memories = await store.asearch(("static_memories", "global"), query="", limit=1)
        if static_memories:
            logger.debug("Static memories already exist in store, skipping load.")
            return
    except Exception as e:
        # Log the error but proceed, as the store might be empty or have issues
        logger.warning(f"Could not check for existing static memories, proceeding to load: {e}")

    # Define the directory and load memories
    logger.info("Attempting to load static memories into store.")
    await _load_memories_from_directory(STATIC_MEMORIES_DIR, store) 