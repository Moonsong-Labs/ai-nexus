"""Graphs that extract memories on a schedule."""

from langchain.chat_models import init_chat_model
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from coder.prompts import SYSTEM_PROMPT
from coder.state import State

llm = init_chat_model("google_genai:gemini-2.0-flash")

class CallModel:
    def __init__(self, github_tools: list[Tool]):
        self.github_tools = github_tools

    async def __call__(self, state: State) -> dict:
        system_msg = SystemMessage(content=SYSTEM_PROMPT)
        messages = [system_msg] + state["messages"]
        messages_after_invoke = await llm.bind_tools(self.github_tools).ainvoke(messages)
        return {"messages": messages_after_invoke}

def graph_builder(github_toolset: list[Tool]) -> StateGraph:
    builder = StateGraph(State)

    tool_node = ToolNode(tools=github_toolset)

    builder.add_node("call_model", CallModel(github_toolset))
    builder.add_node("tools", tool_node)

    builder.add_edge("__start__", "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder

__all__ = ["graph_builder"]

#import asyncio

# if __name__ == "__main__":
#     async def main():
#         user_input = "This is a python project. Add an entry point (main.py) to the project and print Hello World."
#         config = {"configurable": {"thread_id": "1"}}

#         events = graph.astream(
#             {"messages": [{"role": "user", "content": user_input}]},
#             config,
#             stream_mode="values",
#         )
#         async for event in events:
#                 if "messages" in event:
#                     event["messages"][-1].pretty_print()

#     asyncio.run(main())

#     print(mock_api.operations)