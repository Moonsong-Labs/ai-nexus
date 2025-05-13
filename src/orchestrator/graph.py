"""Graphs that orchestrates a software project."""

import logging
from datetime import datetime
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore

from code_reviewer.graph import graph as code_reviewer_graph

# Import specific agent graphs
from coder.lg_server import graph as coder_graph
from common import utils
from orchestrator import configuration, stubs, tools
from orchestrator.state import State

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
model_orchestrator = init_chat_model()


async def orchestrate(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    sys = configurable.system_prompt.format(time=datetime.now().isoformat())

    msg = await model_orchestrator.bind_tools(
        [tools.Delegate, tools.store_memory]
    ).ainvoke(
        [SystemMessage(sys), *state.messages],
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


def delegate_to(
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
                return coder_graph.name
            elif tool_call["args"]["to"] == "tester":
                return stubs.tester.__name__
            elif tool_call["args"]["to"] == "reviewer":
                return code_reviewer_graph.name
            # elif tool_call["args"]["to"] == "memorizer":
            #     return stubs.memorizer.__name__
            else:
                raise ValueError


# Create the graph + all nodes
builder = StateGraph(State, config_schema=configuration.Configuration)

# Define the flow of the memory extraction process
builder.add_node(orchestrate)
# builder.add_node(store_memory)
builder.add_node(stubs.requirements)
builder.add_node(stubs.architect)
builder.add_node(coder_graph)
builder.add_node(stubs.tester)
builder.add_node(code_reviewer_graph)
builder.add_node(stubs.memorizer)

builder.add_edge(START, orchestrate.__name__)
builder.add_conditional_edges(
    orchestrate.__name__,
    delegate_to,
)
builder.add_edge(stubs.requirements.__name__, orchestrate.__name__)
builder.add_edge(stubs.architect.__name__, orchestrate.__name__)
builder.add_edge("coder", orchestrate.__name__)
builder.add_edge(stubs.tester.__name__, orchestrate.__name__)
builder.add_edge(code_reviewer_graph.name, orchestrate.__name__)
builder.add_edge(stubs.memorizer.__name__, orchestrate.__name__)

graph = builder.compile()
graph.name = "Orchestrator"


__all__ = ["graph"]
