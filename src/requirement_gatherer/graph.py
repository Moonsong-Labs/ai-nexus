"""Graphs that extract memories on a schedule."""

import asyncio
import logging
from datetime import datetime
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore
from langgraph.types import interrupt
from langchain_core.messages import AIMessage

from pydantic import BaseModel, Field

from requirement_gatherer import configuration, tools, utils
from requirement_gatherer.state import State


class Veredict(BaseModel):
    """Feedback to decide if all requirements are meet."""

    veredict: Literal["Completed", "needs_more"] = Field(
        description="Decide if requirements are complete"
    )


logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()
evaluator_llm = init_chat_model()
evaluator = evaluator_llm.with_structured_output(Veredict)


def call_evaluator_model(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)
    sys_prompt_content = configurable.evaluator_system_prompt.format(
        time=datetime.now().isoformat()
    )
    
    # Prepare the list of messages for the evaluator.
    # The first message should be the system prompt.
    evaluator_input_messages = [{"role": "system", "content": sys_prompt_content}]

    # Process the rest of the messages from the state.
    for msg in state.messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            # If an AIMessage from history has tool_calls, we'll simplify it
            # for the evaluator. This is to prevent potential conflicts if the
            # evaluator's structured output mechanism mishandles prior, unrelated tool_calls.
            # We'll pass only its text content, if available and is a string.
            if msg.content and isinstance(msg.content, str):
                # Create a new AIMessage with only the content and original id (if present).
                simplified_ai_msg = AIMessage(
                    content=msg.content, 
                    id=getattr(msg, 'id', None) # Safely get id
                )
                evaluator_input_messages.append(simplified_ai_msg)
            # If the AIMessage had tool_calls but no valid string content,
            # it's omitted from the evaluator_input_messages to avoid sending
            # potentially empty or problematic messages. The message that caused
            # the error in your trace did have valid string content.
        else:
            # For all other message types, or AIMessages without tool_calls, pass them as is.
            evaluator_input_messages.append(msg)
    
    veredict = evaluator.invoke(
        evaluator_input_messages, # Pass the processed list of messages
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    print(veredict)
    return {"veredict": veredict}


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
    # This helps the model understand the context and temporal relevance
    sys = configurable.gatherer_system_prompt.format(
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


def route_memory(state: State):
    """Determine the next step based on the presence of tool calls."""
    msg = state.messages[-1]
    if msg.tool_calls:
        return "store_memory"
    return "human_feedback"


def route_veredict(state: State):
    """Determine the nect step based on task completion."""
    if state.veredict and state.veredict.veredict == "Completed":
        return END
    return "call_model"


def human_feedback(state: State):
    msg = state.messages[-1].content

    user_input = interrupt({"query": msg})

    return {"messages": user_input}


memory = MemorySaver()

builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(call_model)
builder.add_node(call_evaluator_model)
builder.add_node(human_feedback)
builder.add_node(store_memory)

builder.add_edge("__start__", "call_model")
builder.add_conditional_edges("call_model", route_memory, ["store_memory", "human_feedback"])
builder.add_edge("store_memory", "call_model")
builder.add_edge("human_feedback", "call_evaluator_model")
builder.add_conditional_edges(
    "call_evaluator_model", route_veredict, ["call_model", END]
)

graph = builder.compile()
graph.name = "Requirement Gatherer Agent"


__all__ = ["graph"]
