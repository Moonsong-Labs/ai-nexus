"""Graphs that extract memories on a schedule."""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from agent_template import configuration, tools, utils
from agent_template.state import State

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()


# Helper function to load static memories
async def ensure_static_memories(store: BaseStore):
    """Ensure static memories are loaded in the store."""
    # Check if any static memories exist
    try:
        # Try passing only namespace positionally, rest as keywords
        static_memories = await store.asearch(
            ("static_memories", "global"),
            query="",
            limit=1
        )
        if static_memories:
            logger.info("Static memories already exist in store")
            return
    except Exception as e:
        logger.error(f"Error checking for static memories: {e}")
        return
        
    # Load memories from file
    logger.info("Loading static memories into store")
    static_memories_path = Path(".langgraph/static_memories/project_info.json")
    
    if not static_memories_path.exists():
        logger.warning(f"Static memories file not found at {static_memories_path}")
        return
        
    try:
        with open(static_memories_path, "r") as f:
            memories = json.load(f)
            
        # Add each memory to the store
        for i, memory in enumerate(memories):
            # Use positional arguments for aput as that seems to work
            await store.aput(
                ("static_memories", "global"),
                f"static_{i}",
                memory
            )
        logger.info(f"Loaded {len(memories)} static memories into store")
    except Exception as e:
        logger.error(f"Error loading static memories: {e}")


async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    # Ensure static memories are loaded
    await ensure_static_memories(store)
    
    configurable = configuration.Configuration.from_runnable_config(config)

    query_text = str([m.content for m in state.messages[-3:]])

    # Retrieve the most recent memories for context
    memories = await store.asearch(
        ("memories", configurable.user_id),
        query=query_text,
        limit=10,
    )

    # Retrieve static memories using only namespace positionally
    static_memories = await store.asearch(
        ("static_memories", "global"),
        query=query_text,
        limit=5
    )
    
    logger.info(f"Found {len(static_memories)} relevant static memories")
    
    # Format memories for inclusion in the prompt
    memory_texts = []
    
    # Add user memories
    for mem in memories:
        memory_text = f"[{mem.key}]: {mem.value} (similarity: {mem.score})"
        memory_texts.append(memory_text)
    
    formatted = "\n".join(memory_texts)
    
    # Add static memories with special formatting
    if static_memories:
        static_memory_texts = []
        for mem in static_memories:
            content = mem.value.get('content', 'No content')
            context = mem.value.get('context', 'No context')
            memory_text = f"[{mem.key}]: content: {content}, context: {context}"
            static_memory_texts.append(memory_text)
        
        if static_memory_texts:
            if formatted:
                formatted += "\n\n<static_memories>\n"
            else:
                formatted = "<static_memories>\n"
                
            formatted += "\n".join(static_memory_texts)
            formatted += "\n</static_memories>"
    
    if formatted:
        formatted = f"""
<memories>
{formatted}
</memories>"""

    # Prepare the system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys = configurable.system_prompt.format(
        user_info=formatted, time=datetime.now().isoformat()
    )

    # Invoke the language model with the prepared prompt and tools
    # "bind_tools" gives the LLM the JSON schema for all tools in the list so it knows how
    # to use them.
    msg = await llm.bind_tools([tools.upsert_memory]).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    return {"messages": [msg]}


async def store_memory(state: State, config: RunnableConfig, *, store: BaseStore):
    # Extract tool calls from the last message
    tool_calls = state.messages[-1].tool_calls

    # Concurrently execute all upsert_memory calls
    saved_memories = await asyncio.gather(
        *(
            tools.upsert_memory(**tc["args"], config=config, store=store)
            for tc in tool_calls
        )
    )

    # Format the results of memory storage operations
    # This provides confirmation to the model that the actions it took were completed
    results = [
        {
            "role": "tool",
            "content": mem,
            "tool_call_id": tc["id"],
        }
        for tc, mem in zip(tool_calls, saved_memories)
    ]
    return {"messages": results}


def route_message(state: State):
    """Determine the next step based on the presence of tool calls."""
    msg = state.messages[-1]
    if msg.tool_calls:
        # If there are tool calls, we need to store memories
        return "store_memory"
    # Otherwise, finish; user can send the next message
    return END


# Create the graph + all nodes
builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(call_model)
builder.add_edge("__start__", "call_model")
builder.add_node(store_memory)
builder.add_conditional_edges("call_model", route_message, ["store_memory", END])
# Right now, we're returning control to the user after storing a memory
# Depending on the model, you may want to route back to the model
# to let it first store memories, then generate a response
builder.add_edge("store_memory", "call_model")
graph = builder.compile()
graph.name = "Agent Template"


__all__ = ["graph"]
