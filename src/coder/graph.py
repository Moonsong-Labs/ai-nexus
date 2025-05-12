"""Graphs that extract memories on a schedule."""

import os

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import Tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore

from coder.prompts import SYSTEM_PROMPT
from coder.state import State

llm = init_chat_model("google_genai:gemini-2.0-flash")


class CallModel:
    def __init__(self, github_tools: list[Tool]):
        self.github_tools = github_tools

    async def __call__(self, state: State) -> dict:
        system_msg = SystemMessage(content=SYSTEM_PROMPT)
        messages = [system_msg] + state["messages"]
        messages_after_invoke = await llm.bind_tools(self.github_tools).ainvoke(
            messages
        )
        return {"messages": messages_after_invoke}


def coder_stub(state: dict, config: RunnableConfig, store: BaseStore):
    """Stub function for the coder graph."""
    # Access state as a dictionary, not as an object
    tool_call_id = state["messages"][-1].tool_calls[0]["id"]
    return {
        "messages": [
            ToolMessage(content="I have finished coding.", tool_call_id=tool_call_id)
        ]
    }


def build_stub_graph():
    builder = StateGraph(State)
    builder.add_node("coder_stub", coder_stub)
    builder.set_entry_point("coder_stub")
    builder.set_finish_point("coder_stub")
    graph = builder.compile()
    graph.name = "coder"
    return graph


def build_graph(github_toolset: list[Tool]) -> StateGraph:
    """Return a StateGraph builder for the real coder graph."""
    builder = StateGraph(State)

    tool_node = ToolNode(tools=github_toolset)

    builder.add_node("call_model", CallModel(github_toolset))
    builder.add_node("tools", tool_node)

    builder.add_edge("__start__", "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    graph = builder.compile()
    graph.name = "coder"
    return graph


def graph_builder(tools: list[Tool]):
    """Build and compile the coder graph, deciding between stub and real implementation."""
    _coder_stub_enabled = os.getenv("CODER_STUB_ENABLE", "true").lower() != "false"

    if _coder_stub_enabled:
        return build_stub_graph()
    else:
        # If stub is disabled, build the real graph
        return build_graph(tools)


__all__ = ["graph_builder"]
