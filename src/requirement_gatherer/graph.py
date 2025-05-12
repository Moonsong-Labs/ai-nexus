"""Graphs that extract memories on a schedule."""

import asyncio
import logging
from datetime import datetime
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from requirement_gatherer import configuration, tools, utils
from requirement_gatherer.state import State


class Verdict(BaseModel):
    """Feedback to decide if all requirements are meet."""

    verdict: Literal["Completed", "needs_more"] = Field(
        description="Decide if requirements are complete"
    )


logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()
evaluator_llm = init_chat_model()
evaluator = evaluator_llm.with_structured_output(Verdict)


def call_evaluator_model(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    # Retrieve the most recent memories for context
    memories = store.search(
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
    sys = configurable.evaluator_system_prompt.format(
        user_info=formatted, time=datetime.now().isoformat()
    )

    verdict = evaluator.invoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    return {"verdict": verdict}


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
    msg = await llm.bind_tools([tools.upsert_memory, tools.finalize]).ainvoke(
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

async def evaluate_verdict(state: State, config: RunnableConfig, *, store: BaseStore):
    # Extract tool calls from the last message
    tool_calls = state.messages[-1].tool_calls
    tool_call = tool_calls[0]

    print("CHECK")
    for i, msg in enumerate(state.messages):
        print(f"[{i:<3}] {msg}")
    result = call_evaluator_model(State(messages=state.messages[:-1]), config=config, store=store)

    print(f"EVAL {result}")
    # Format the results of memory storage operations
    # This provides confirmation to the model that the actions it took were completed
    results = [
        {
            "role": "tool",
            "content": "All good",
            "tool_call_id": tool_call["id"],
        }
    ]
    return {"messages": results}


def route_memory(state: State):
    """Determine the next step based on the presence of tool calls."""
    msg = state.messages[-1]
    tool_calls = msg.tool_calls

    if (
        len(tool_calls) != 0
        and tool_calls[0]["name"] == "finalize"
        and tool_calls[0]["args"]["verdict"] == "evaluate"
    ):
        print("[Requirements FINALIZED]")
        print(msg)
        if state.verdict == "Completed":
            print("[Requirements DONE]")
            print(msg)
            return END
        else:
            return evaluate_verdict.__name__
    elif msg.tool_calls:
        return "store_memory"
    return human_ai_feedback.__name__


def route_verdict(state: State):
    """Determine the nect step based on task completion."""
    print(f"VERDICT {state.verdict}")
    if state.verdict == "Completed":
        return END
    return "call_model"


demo_user = init_chat_model()


async def human_ai_feedback(state: State, config: RunnableConfig):
    msg = state.messages[-1].content

    print(f"\n{'=' * 50} QUESTION {'=' * 50}\n{msg}\n{'=' * 150}\n")

    sys = """You are an end-user that wants to create a software product. Your requirements are simple but specific.
You will be reply to any questions as per the following rubric:

<Rubric>
  - You MUST always reply with an answer
  - You must NEVER reply with a question

  A correct reply:
  - Provides accurate and complete information
  - Contains no factual errors
  - Addresses all parts of the question
  - Is logically consistent
  - Is less that 2 sentences

  When replying, you should:
  - Be consistent with the earlier messages
  - If a new information is asked, create a simple situation
  - Do NOT let the user know you made a guess
  - If the conversation is getting long, do NOT add more requirements, if avoidable
</Rubric>

<Instructions>
  - Carefully read the input
  - Based on the input, reply to the question in a simple and consistent way 
  - If a new information is asked for, reply with the simplest guess but do not inform that it is a guess
</Instructions>

<Reminder>
You MUST always reply with an answer
</Reminder>

<input>
{input}
</input>
    """

    from langchain_core.messages import HumanMessage, SystemMessage

    configurable = configuration.Configuration.from_runnable_config(config)
    reply = await demo_user.ainvoke(
        [
            SystemMessage(content=sys.format(input=state.messages)),
            HumanMessage(content=msg),
        ],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )

    print(f"\n{'=' * 50} ANSWER {'=' * 50}\n{reply.content}\n{'=' * 150}\n")

    # user_input = interrupt({"query": msg})
    # return {"messages": user_input}
    from langchain_core.messages import HumanMessage

    return {"messages": [HumanMessage(content=reply.content)]}


async def human_feedback(state: State, config: RunnableConfig):
    msg = state.messages[-1].content
    user_input = interrupt({"query": msg})
    return {"messages": user_input}


memory = MemorySaver()

builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(call_model)
builder.add_node(human_ai_feedback)
builder.add_node(store_memory)
builder.add_node(evaluate_verdict)

builder.add_edge(START, "call_model")
builder.add_conditional_edges(
    "call_model", route_memory, ["store_memory", human_ai_feedback.__name__, evaluate_verdict.__name__, END]
)
builder.add_edge("store_memory", "call_model")
builder.add_edge(evaluate_verdict.__name__, "call_model")
builder.add_edge(human_ai_feedback.__name__, "call_model")

# builder.add_conditional_edges(
#     "call_model", route_verdict, [call_model.__name__, END]
# )

graph = builder.compile()
graph.name = "Requirement Gatherer Agent"


__all__ = ["graph"]
