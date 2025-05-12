"""Test the orchestrator locally"""

import asyncio
import json
import sys
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Literal

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
)
from langchain_core.runnables import RunnableConfig
from langsmith import RunTree
from langsmith.client import Client
from langsmith.evaluation import EvaluationResult
from pydantic import BaseModel
from termcolor import colored

from orchestrator import graph
from orchestrator.state import State


def print_messages_any(messages: list[dict]):
    next_tool_name = None
    for msg in messages:
        msg_type = msg["type"]
        msg_content = msg["content"].rstrip()
        if msg["type"] == "tool" and next_tool_name is not None:
            msg_type = f"tool ({next_tool_name})"
            next_tool_name = None
        print(
            f"{colored(msg_type, 'green'):<30}: {colored(msg_content, 'light_yellow')}"
        )
        if "tool_calls" in msg:
            # print(msg["tool_calls"])
            for tool_call in msg["tool_calls"]:
                tool = f"[{tool_call['name']}]"
                next_tool_name = tool_call["args"]["to"]
                if tool_call["name"] == "Delegate":
                    print(
                        f"{'    ' * 6}└── {colored(tool, 'cyan'):20}: {colored(tool_call['args']['to'], 'light_cyan')}"
                    )
                    print(
                        f"{'    ' * 9}     {colored(tool_call['args']['content'], 'light_grey')}"
                    )
                else:
                    print(
                        f"{'    ' * 6}└── {colored(tool, 'cyan'):20}: {colored(tool_call['args'], 'light_grey')}"
                    )


if __name__ == "__main__":
    args = sys.argv[1:]
    mode: Literal["exec", "read"] = "read"
    if len(args) > 0:
        mode = args[0]
    else:
        print("need an argument: exec|read")
        exit(1)

    if mode == "exec":
        result = asyncio.run(
            graph.ainvoke(
                State(messages=HumanMessage(content="I want to build a website")),
                config=RunnableConfig(configurable={"thread_id": str(uuid.uuid4())}),
            )
        )

        class _CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, uuid.UUID):
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                elif hasattr(
                    obj, "__dataclass_fields__"
                ):  # Check if obj is a dataclass
                    return asdict(obj)
                elif isinstance(obj, RunTree):
                    return obj.dict()
                elif isinstance(obj, BaseMessage):
                    return obj.model_dump()
                elif isinstance(obj, BaseModel):
                    return obj.model_dump()
                elif isinstance(obj, BaseModel):
                    return obj.model_dump()
                elif isinstance(obj, EvaluationResult):
                    return obj.dict()
                elif isinstance(obj, Client):  # Handle LangSmith Client
                    return {
                        "api_url": obj.api_url,
                        "tenant_id": str(obj._tenant_id)
                        if hasattr(obj, "_tenant_id")
                        else None,
                    }
                return super().default(obj)

        # print(f"Final Result: {result}")
        # print_messages(result["messages"])

        # import json
        result_json = json.dumps(result, cls=_CustomEncoder)
        with open("dump.json", "w") as f:
            f.write(result_json)

        print_messages_any(json.loads(result_json)["messages"])
    elif mode == "read":
        with open("dump.json") as f:
            result = json.load(f)
            print_messages_any(result["messages"])
    else:
        print(f"invalid mode: {mode}, allowed exec|read")
