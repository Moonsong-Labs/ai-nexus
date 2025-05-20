"""Test the orchestrator locally."""

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
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langsmith import RunTree
from langsmith.client import Client
from langsmith.evaluation import EvaluationResult
from pydantic import BaseModel
from termcolor import colored

from orchestrator.configuration import (
    ArchitectAgentConfig,
    RequirementsAgentConfig,
    RequirementsConfiguration,
    SubAgentConfig,
    TaskManagerAgentConfig,
    TaskManagerConfiguration,
)
from orchestrator.configuration import (
    Configuration as OrchestratorConfiguration,
)
from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State

OUTPUT_DUMP_FILE = "dump.json"  # output file for `read` operation


def print_messages_any(messages: list[dict]):
    """
    Pretty-prints a list of message dictionaries with formatted output.

    Displays each message's type and content using colored formatting. If messages contain nested tool calls, formats and indents them for readability, with special handling for "Delegate" tool calls.
    """
    next_tool_name = None
    for msg in messages:
        msg_type = msg["type"]
        msg_content = msg["content"].strip()
        if msg["type"] == "tool" and next_tool_name is not None:
            msg_type = f"{next_tool_name}"
            next_tool_name = None
        elif msg["type"] == "ai":
            msg_type = "orchestrator"

        print(
            f"{colored(msg_type, 'green'):<30}: {colored(msg_content, 'light_yellow')}"
        )
        if "tool_calls" in msg:
            for tool_call in msg["tool_calls"]:
                tool = f"[{tool_call['name']}]"
                next_tool_name = tool_call["name"]
                if tool_call["name"] in [
                    "requirements",
                    "architect",
                    "task_manager",
                    "coder_new_pr",
                    "coder_change_request",
                    "tester",
                    "code_reviewer",
                ]:
                    print(
                        f"{'    ' * 6}└── {colored(tool, 'cyan'):20} {colored(tool_call['args']['content'], 'light_grey')}"
                    )
                else:
                    print(
                        f"{'    ' * 6}└── {colored(tool, 'cyan'):20}: {colored(tool_call['args'], 'light_grey')}"
                    )


if __name__ == "__main__":
    args = sys.argv[1:]
    mode: Literal["exec", "read"] = "read"
    """One of the following modes:
        * `exec` executes the script and dumps a json file
        * `read` reads the json file
    """
    human_or_ai: Literal["human", "ai"] = "human"

    if len(args) < 1:
        print("need an argument: exec|read")
        exit(1)
    else:
        mode = args[0]
        if mode == "exec":
            if len(args) < 2:
                print("need an argument: human|ai")
                exit(1)
            else:
                human_or_ai = args[1]

    if mode == "exec":
        use_human_ai = human_or_ai == "ai"
        orchestrator = OrchestratorGraph(
            agent_config=OrchestratorConfiguration(
                requirements_agent=RequirementsAgentConfig(
                    use_stub=True,
                    config=RequirementsConfiguration(use_human_ai=use_human_ai),
                ),
                architect_agent=ArchitectAgentConfig(
                    use_stub=True,
                ),
                task_manager_agent=TaskManagerAgentConfig(
                    use_stub=True,
                    config=TaskManagerConfiguration(),
                ),
                coder_new_pr_agent=SubAgentConfig(
                    use_stub=True,
                ),
                coder_change_request_agent=SubAgentConfig(
                    use_stub=True,
                ),
            ),
            checkpointer=InMemorySaver(),
            store=InMemoryStore(),
        )

        async def _exec():
            """
            Executes the orchestrator asynchronously, handling user input for any interrupts.

            Runs the orchestrator with an initial human message, checks for interrupts requiring user input, and resumes execution as needed until completion. Returns the final orchestrator result.
            """
            config = orchestrator.create_runnable_config(
                RunnableConfig(
                    recursion_limit=250,
                    configurable={
                        "thread_id": str(uuid.uuid4()),
                    },
                )
            )
            result = await orchestrator.compiled_graph.ainvoke(
                State(messages=HumanMessage(content="I want to build a website")),
                config=config,
            )

            # Handle interrupts
            while True:
                graph_state = await orchestrator.compiled_graph.aget_state(config)
                if graph_state.interrupts:
                    interrupt = graph_state.interrupts[0]
                    response = input(
                        f"\n{'-' * 50}\n{colored('requirements', 'green')}: {colored(interrupt.value['query'], 'light_grey')}\n\n{colored('Answer', 'yellow')}: "
                    )
                    result = await orchestrator.compiled_graph.ainvoke(
                        Command(resume=response), config=config
                    )
                else:
                    break

            return result

        result = asyncio.run(_exec())

        # print(result["messages"])

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
        with open(OUTPUT_DUMP_FILE, "w") as f:
            f.write(result_json)

        print_messages_any(json.loads(result_json)["messages"])
    elif mode == "read":
        with open(OUTPUT_DUMP_FILE) as f:
            result = json.load(f)
            print_messages_any(result["messages"])
    else:
        print(f"invalid mode: {mode}, allowed exec|read")
