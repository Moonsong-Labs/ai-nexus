"""Graphs that extract memories on a schedule."""

import logging
from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore

from agent_template import configuration, utils
from agent_template.memory import (
    ensure_static_memories,
    format_static_memories_for_prompt,
)
from agent_template.state import State
from agent_template.tools import get_memory_tools

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()


async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    # Ensure static memories are loaded
    await ensure_static_memories(store)

    configurable = configuration.Configuration.from_runnable_config(config)

    query_text = str([m.content for m in state.messages[-3:]])

    # Retrieve static memories using only namespace positionally
    static_memories = await store.asearch(
        ("static_memories", "global"), query=query_text, limit=5
    )

    logger.info(f"Found {len(static_memories)} relevant static memories")

    # Format memories for inclusion in the prompt
    formatted = format_static_memories_for_prompt(static_memories)

    # Prepare the system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys = configurable.system_prompt.format(
        static_memories=formatted, time=datetime.now().isoformat()
    )

    # Invoke the language model with the prepared prompt and tools
    # "bind_tools" gives the LLM the JSON schema for all tools in the list so it knows how
    # to use them.
    memory_tools = get_memory_tools(configurable)
    msg = await llm.bind_tools(memory_tools).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    return {"messages": [msg]}


def route_message(state: State):
    return END


# Create the graph + all nodes
builder = StateGraph(State)

config = configuration.Configuration()

# Create memory tools node
memory_tools = get_memory_tools(config)
memory_tools_node = ToolNode(tools=memory_tools)

# Define the flow of the memory extraction process
builder.add_node(call_model)
builder.add_node("tools", memory_tools_node)

builder.add_edge("__start__", "call_model")
builder.add_conditional_edges("call_model", tools_condition)
builder.add_edge("tools", "call_model")

graph = builder.compile()
graph.name = "Agent Template"


__all__ = ["graph"]
