"""Graphs that extract memories on a schedule."""

import logging
from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore

from agent_template import configuration, utils
from agent_template.state import State

logger = logging.getLogger(__name__)


async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    # Get configuration
    configurable = configuration.Configuration.from_runnable_config(config)
    
    # Prepare the system prompt with memories and current time
    sys = configurable.system_prompt.format(time=datetime.now().isoformat()
    )

    # Invoke the language model with the prepared prompt and tools
    state.initialize_memories(configurable)
    memory_tools = state.semantic_memory.get_tools()
    msg = await llm.bind_tools(memory_tools).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    return {"messages": [msg]}


def route_message(state: State):
    return END


config = configuration.Configuration()

# Initialize a default state to configure initial memories
initial_state = State(user_id=config.user_id)
initial_state.initialize_memories(config)

# Create the graph + all nodes
builder = StateGraph(State)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()

# Create memory tools node with the State's memories
memory_tools = initial_state.semantic_memory.get_tools()
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
