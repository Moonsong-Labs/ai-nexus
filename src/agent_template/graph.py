"""Graphs that extract memories on a schedule."""

import logging

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent_template.agent import Agent
from agent_template.configuration import Configuration
from agent_template.state import State

logger = logging.getLogger(__name__)


def graph_builder() -> StateGraph:
    # Create the graph + all nodes
    builder = StateGraph(State)

    # Create the configuration instance
    config = Configuration()
    config.use_static_mem = True

    # Create the agent instance
    agent = Agent(config)
    agent.initialize(config)

    # Add nodes to the graph
    builder.add_node("call_model", agent.__call__)

    tool_node = ToolNode(agent.get_tools())
    builder.add_node("tools", tool_node)

    # Define the flow
    builder.add_edge("__start__", "call_model")
    # builder.add_conditional_edges("__start__", agent.route_message, ["agent_init", "call_model"])
    builder.add_conditional_edges("call_model", tools_condition)
    # builder.add_edge("agent_init", "call_model")
    builder.add_edge("tools", "call_model")
    builder.add_edge("call_model", END)

    return builder


graph = graph_builder().compile()
graph.name = "Agent Template"


__all__ = ["graph"]
