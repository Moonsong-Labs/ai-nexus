"""Task Manager graph."""

import logging
import re
import json
from datetime import datetime
import os

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import END, StateGraph

from task_manager import configuration, tools, utils
from task_manager.state import State

logger = logging.getLogger(__name__)

# Initialize the language model
llm = init_chat_model()


async def call_model(state: State, config: RunnableConfig) -> dict:
    """Process user input and generate tasks."""
    configurable = configuration.Configuration.from_runnable_config(config)
    
    # Check if the last user message is the TEST command
    if state.messages and hasattr(state.messages[-1], 'content'):
        # In LangChain, HumanMessage objects represent user messages
        user_message = state.messages[-1].content
        logger.debug(f"Processing user message: {user_message}")

    # Prepare the system prompt with current time
    sys = configurable.system_prompt.format(
        user_info="", time=datetime.now().isoformat()
    )

    # Invoke the language model with the prepared prompt and tools
    msg = await llm.bind_tools([tools.read_file, tools.create_file, tools.list_files]).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    
    # Extract project name from the user's message or recent messages
    project_name = None
    for message in reversed(state.messages):
        if hasattr(message, 'content'):
            # Try to find "Project name: X" or "Project: X" pattern
            name_match = re.search(r'Project[\s\w]*[:\-]?\s*["\']?([a-zA-Z0-9_\- ]+)["\']?', message.content, re.IGNORECASE)
            if name_match:
                project_name = name_match.group(1).strip().replace(" ", "_").lower()
                break
    
    # When the model responds, try to save any tasks.json content to a file
    if msg.content and project_name:
        # Check if the content has json-formatted tasks list
        if '[' in msg.content and '"id":' in msg.content:
            logger.info(f"Tasks generated, attempting to save to file for project: {project_name}")
            save_result = await tools.save_tasks_json(project_name, msg.content)
            logger.info(f"Save result: {save_result}")
    
    return {"messages": [msg]}

def process_tools(state: State):
    """Determine whether to process tool calls or end the conversation.
    
    If the last message contains tool calls, route to tools node.
    Otherwise, end the conversation (END).
    """
    msg = state.messages[-1]
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        logger.info("Tool calls detected, routing to tools")
        return "tools"
    
    # If no tool calls, end conversation
    logger.info("No tool calls, ending conversation")
    return END


# Create the graph + all nodes
builder = StateGraph(State, config_schema=configuration.Configuration)
tool_node = ToolNode([tools.read_file, tools.create_file, tools.list_files])

# Define the flow of the task manager process
builder.add_node(call_model)
builder.add_edge("__start__", "call_model")
builder.add_node("tools", tool_node)
# builder.add_conditional_edges("call_model", process_tools, ["tools", END])
builder.add_conditional_edges(
    "call_model",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "call_model")
graph = builder.compile()
graph.name = "Task Manager"


__all__ = ["graph"]
