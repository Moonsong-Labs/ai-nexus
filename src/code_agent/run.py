from code_agent.graph import graph
import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"

user_input = "This will be a python project. Add an entry point with a simple hello world program."
config = {"configurable": {"thread_id": "1"}}

events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)
for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()