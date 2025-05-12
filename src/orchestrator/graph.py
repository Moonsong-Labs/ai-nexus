"""Graphs that orchestrates a software project."""

import logging
from datetime import datetime
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

from common import utils
from orchestrator import configuration, stubs, tools
from orchestrator.state import State
from requirement_gatherer.graph import builder as requirements_gatherer_builder
from requirement_gatherer.state import State as RequirementsState

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
model_orchestrator = init_chat_model()


async def orchestrate(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    sys_msg = configurable.system_prompt.format(time=datetime.now().isoformat())

    msg = await model_orchestrator.bind_tools(
        [tools.Delegate, tools.store_memory]
    ).ainvoke(
        [SystemMessage(sys_msg), *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )

    return {"messages": [msg]}


async def store_memory(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    sys = configurable.system_prompt.format(time=datetime.now().isoformat())

    msg = await model_orchestrator.bind_tools([tools.Delegate, tools.Memory]).ainvoke(
        [SystemMessage(sys), *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )

    return {"messages": [msg]}


checkpointer = InMemorySaver()
store = InMemoryStore()
requirements_gatherer = requirements_gatherer_builder.compile(
    name="Requirements Gatherer", checkpointer=checkpointer, store=store
)


async def delegate_to(
    state: State, config: RunnableConfig, store: BaseStore
) -> Literal[
    "__end__",
    "orchestrate",
    "requirements",
    "architect",
    "coder",
    "tester",
    "reviewer",
    "memorizer",
]:
    """Determine the next step based on the presence of tool calls."""
    message = state.messages[-1]
    if len(message.tool_calls) == 0:
        return END
    else:
        tool_call = message.tool_calls[0]
        if tool_call["name"] == "store_memory":
            return stubs.memorizer.__name__
        else:
            if tool_call["args"]["to"] == "orchestrator":
                return orchestrate.__name__
            elif tool_call["args"]["to"] == "requirements":
                return stubs.requirements.__name__
            elif tool_call["args"]["to"] == "architect":
                return stubs.architect.__name__
            elif tool_call["args"]["to"] == "coder":
                return stubs.coder.__name__
            elif tool_call["args"]["to"] == "tester":
                return stubs.tester.__name__
            elif tool_call["args"]["to"] == "reviewer":
                return stubs.reviewer.__name__
            # elif tool_call["args"]["to"] == "memorizer":
            #     return stubs.memorizer.__name__
            else:
                raise ValueError


async def requirements(state: State, config: RunnableConfig, store: BaseStore):
    tool_call = state.messages[-1].tool_calls[0]
    message = tool_call["args"]["content"]
    print(f"sending to requirements {message}")
    config["recursion_limit"] = 560
    result = await requirements_gatherer.ainvoke(
        RequirementsState(
            messages=[HumanMessage(content=tool_call["args"]["content"])]
        ),
        config,
    )
    import pprint

    print("== GOT RESULT ==")
    pprint.pp(result["messages"][-3], indent=2)
    # print("RETURN REQ")
    # pprint.pp(result["messages"], indent=2)
    return {
        "messages": [
            ToolMessage(
                content=result["messages"][-3].content,
                tool_call_id=tool_call["id"],
            )
        ]
    }


# Create the graph + all nodes
builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(orchestrate)
# builder.add_node(store_memory)
# builder.add_node(stubs.requirements)
builder.add_node(requirements)
builder.add_node(stubs.architect)
builder.add_node(stubs.coder)
builder.add_node(stubs.tester)
builder.add_node(stubs.reviewer)
builder.add_node(stubs.memorizer)

builder.add_edge(START, orchestrate.__name__)
builder.add_conditional_edges(
    orchestrate.__name__,
    delegate_to,
)
builder.add_edge(stubs.requirements.__name__, orchestrate.__name__)
builder.add_edge(stubs.architect.__name__, orchestrate.__name__)
builder.add_edge(stubs.coder.__name__, orchestrate.__name__)
builder.add_edge(stubs.tester.__name__, orchestrate.__name__)
builder.add_edge(stubs.reviewer.__name__, orchestrate.__name__)
builder.add_edge(stubs.memorizer.__name__, orchestrate.__name__)

# graph = builder.compile(name="Orchestrator")
graph = builder.compile(name="Orchestrator", checkpointer=checkpointer, store=store)


__all__ = ["graph"]
