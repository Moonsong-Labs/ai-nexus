from code_agent.graph import graph
import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"

import asyncio

async def main():
    user_input = "Add a logger and log a timestamp when the program starts."
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