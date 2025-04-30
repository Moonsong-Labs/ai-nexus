"""Graphs that extract memories on a schedule."""

import asyncio
import logging
from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from code_agent import configuration, tools, utils
from code_agent.state import State

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()

# Define available tools
available_tools = [
    tools.upsert_memory,
    tools.get_repo_contents,
    tools.create_pull_request
]

msg = llm.invoke("hello", {"configurable": utils.split_model_and_provider(configuration.Configuration().model)})

async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    # Retrieve the most recent memories for context
    memories = await store.asearch(
        ("memories", configurable.user_id),
        query=str([m.content for m in state.messages[-3:]]),
        limit=10,
    )

    # Format memories for inclusion in the prompt
    formatted = "\n".join(
        f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories
    )
    if formatted:
        formatted = f"""
<memories>
{formatted}
</memories>"""

    # Prepare the system prompt with user memories and current time
    sys = configurable.system_prompt.format(
        user_info=formatted, time=datetime.now().isoformat()
    )

    # Invoke the language model with the prepared prompt and tools
    msg = await llm.bind_tools(available_tools).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    return {"messages": [msg]}


async def store_memory(state: State, config: RunnableConfig, *, store: BaseStore):
    # Extract tool calls from the last message
    tool_calls = state.messages[-1].tool_calls

    # Concurrently execute all tool calls
    saved_memories = await asyncio.gather(
        *(
            tools.upsert_memory(**tc["args"], config=config, store=store)
            for tc in tool_calls
            if tc["name"] == "upsert_memory"
        )
    )

    # Format the results of memory storage operations
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
        return "store_memory"
    return END


# Create the graph + all nodes
builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(call_model)
builder.add_edge("__start__", "call_model")
builder.add_node(store_memory)
builder.add_conditional_edges("call_model", route_message, ["store_memory", END])
builder.add_edge("store_memory", "call_model")
graph = builder.compile()
graph.name = "Code Agent"


__all__ = ["graph"]
