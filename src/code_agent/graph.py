"""Graphs that extract memories on a schedule."""

import asyncio
import logging
from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool

from code_agent.prompts import SYSTEM_PROMPT
from code_agent.state import State
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

llm = init_chat_model("google_genai:gemini-2.0-flash")

github_api_wrapper = GitHubAPIWrapper()
github_toolkit = GitHubToolkit.from_github_api_wrapper(github_api_wrapper)

github_whitelisted_tools = [
    "set_active_branch",
    "create_a_new_branch",
    "get_files_from_a_directory",
    "create_pull_request",
    "list_pull_requests_files",
    "create_file",
    "read_file",
    "delete_file",
    "overview_of_existing_files_in_main_branch",
    "overview_of_files_in_current_working_branch",
    "search_code",
]

# Convert LangChain GitHub tools to be Gemini-compatible
def make_gemini_compatible(tool):
    tool.name = tool.name.lower().replace(" ", "_").replace("'", "")
    return tool

all_github_tools = [make_gemini_compatible(tool) for tool in github_toolkit.get_tools()]

# Print whitelist and actual tool names for debugging
print("\nWhitelisted tools:")
for tool in github_whitelisted_tools:
    print(f"- {tool}")

print("\nAvailable tools:")
for tool in all_github_tools:
    print(f"- {tool.name}")

github_tools = [tool for tool in all_github_tools if tool.name in github_whitelisted_tools]
print(f"\nMatched {len(github_tools)} tools")

def call_model(state: State) -> dict:
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    
    # Create a list of messages properly
    messages = [system_msg] + state["messages"]
    
    # Invoke the language model with the prepared prompt and tools
    messages_after_invoke = llm.bind_tools(github_tools).invoke(messages)
    return {"messages": messages_after_invoke}

# Create the graph + all nodes
builder = StateGraph(State)

tool_node = ToolNode(tools=github_tools)

# Define the flow
builder.add_node(call_model)
builder.add_node("tools", tool_node)

builder.add_edge("__start__", "call_model")
builder.add_conditional_edges("call_model", tools_condition)

graph = builder.compile()
graph.name = "Code Agent"

__all__ = ["graph"]