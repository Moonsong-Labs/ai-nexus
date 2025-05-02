from coder.graph import graph
import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"

import asyncio

async def main():
    user_input = "Use the math module to calculate the sum of two numbers on the entry point and show the result after Hello World is printed."
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