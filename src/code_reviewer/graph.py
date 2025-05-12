"""Graphs that extract memories on a schedule."""

import asyncio
import logging
from datetime import datetime
from typing import List

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from code_reviewer import configuration, tools, utils
from code_reviewer.state import State

class DiffHunkFeedback(BaseModel):
    """Feedback specific to a code modification."""

    change_required: bool = Field(description="Whether or not the feedback necessitates a change")
    file: str = Field(description="Filepath of the diff that this feedback relates to")
    offset: int = Field(description="Offset (line number) in the file that this feedback relates to")
    comment: str = Field(description="Comments about the diff hunk")

class DiffFeedback(BaseModel):
    """Feedback for an overall diff"""
    requests_changes: bool = Field(description="Whether or not any changes are requested for the diff")
    overall_comment: str = Field(description="Comments about the overall diff")
    feedback: List[DiffHunkFeedback] = Field(description="Individual feedback for subsections of this diff")

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()

async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    # Check the model supports memory:
    if hasattr(store, "asearch"):
        # Retrieve the most recent memories for context
        # Assumes store is provided and has asearch
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
    else:
        formatted = ""

    # Prepare the system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys = configurable.system_prompt.format(
        user_info=formatted, time=datetime.now().isoformat(),
    )
    # Invoke the language model with the prepared prompt and tools
    msg = (
        await llm.bind_tools([tools.upsert_memory])
        .with_structured_output(DiffFeedback)
        .ainvoke(
            [{"role": "system", "content": sys}, *state.messages],
            {"configurable": utils.split_model_and_provider(configurable.model)},
        )
    )
    return {"messages": [{"role": "assistant", "content": str(msg)}]}


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

async def call_tools(state: State) -> dict:
    """Check if the last message contains tool calls and call them."""

    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    messages = [system_msg] + state["messages"]
    messages_after_invoke = await llm.bind_tools(self.github_tools).ainvoke(
        messages
    )

    return {"messages": messages_after_invoke}


# Create the graph + all nodes
builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(call_model)
builder.add_node(store_memory)
builder.add_node("tools", call_tools)

builder.add_edge("__start__", "call_model")
builder.add_conditional_edges("call_model", tools_condition)
builder.add_conditional_edges("call_model", route_message, ["store_memory", END])
builder.add_edge("tools", "call_model")
# Right now, we're returning control to the user after storing a memory
# Depending on the model, you may want to route back to the model
# to let it first store memories, then generate a response
builder.add_edge("store_memory", "call_model")
graph = builder.compile()
graph.name = "Code Reviewer"

# Create the graph + all nodes
builder_no_memory = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder_no_memory.add_node(call_model)
builder_no_memory.add_edge("__start__", "call_model")
graph_no_memory = builder_no_memory.compile()
graph_no_memory.name = "code_reviewer_no_memory"


__all__ = [
    "graph",
    "builder",
    "graph_no_memory",
    "builder_no_memory",
]
