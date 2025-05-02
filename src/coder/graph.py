"""Graphs that extract memories on a schedule."""

import asyncio
import logging

from langchain.chat_models import init_chat_model
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool

from coder.prompts import SYSTEM_PROMPT
from coder.state import State
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
    "update_file",
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

github_tools = [tool for tool in all_github_tools if tool.name in github_whitelisted_tools]
assert len(github_tools) == len(github_whitelisted_tools), "Github tool mismatch"

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