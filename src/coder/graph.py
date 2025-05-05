"""Graphs that extract memories on a schedule."""

import logging

from langchain.chat_models import init_chat_model
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from coder.prompts import SYSTEM_PROMPT
from coder.state import State
from coder.tools import github_tools, mock_github_tools
from coder.mocks import MockGithubApi
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

llm = init_chat_model("google_genai:gemini-2.0-flash")

mock_api = MockGithubApi()
github_tools = mock_github_tools(mock_api)

async def call_model(state: State) -> dict:
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    
    # Create a list of messages properly
    messages = [system_msg] + state["messages"]
    
    # Invoke the language model with the prepared prompt and tools
    messages_after_invoke = await llm.bind_tools(github_tools).ainvoke(messages)
    return {"messages": messages_after_invoke}

# Create the graph + all nodes
builder = StateGraph(State)

tool_node = ToolNode(tools=github_tools)

# Define the flow
builder.add_node(call_model)
builder.add_node("tools", tool_node)

builder.add_edge("__start__", "call_model")
builder.add_conditional_edges("call_model", tools_condition)
builder.add_edge("tools", "call_model")

graph = builder.compile()
graph.name = "Code Agent"

__all__ = ["graph"]

import asyncio

if __name__ == "__main__":
    async def main():
        user_input = "This is a python project.Add an entry point to the project and print Hello World."
        config = {"configurable": {"thread_id": "1"}}

        events = graph.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="values",
        )
        async for event in events:
                if "messages" in event:
                    event["messages"][-1].pretty_print()

    asyncio.run(main())