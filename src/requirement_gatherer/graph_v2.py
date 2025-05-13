"""Graphs that extract memories on a schedule."""
import asyncio
import logging
import pprint
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, InjectedToolCallId, tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import InjectedState, InjectedStore, ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer, Command, interrupt
from pydantic import BaseModel, Field
from termcolor import colored
from typing_extensions import Annotated

from common import config
from common.graph import AgentGraph
from requirement_gatherer import prompts, tools, utils
from requirement_gatherer.state import State

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Configuration(config.Configuration):
    """Main configuration class for the memory graph system."""

    gatherer_system_prompt: str = prompts.SYSTEM_PROMPT
    evaluator_system_prompt: str = prompts.EVALUATOR_SYSTEM_PROMPT


demo_user = init_chat_model()


@tool("human_feedback", parse_docstring=True)
async def human_feedback(
    question: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[State, InjectedState],
    config: RunnableConfig,
) -> Command:
    """Request feedback from a human.

    Args:
        question: The question to ask.

    Returns:
        A Command to update the state with the human response.
    """
    content = ""
    if state.messages[-1].content: 
        content = f"\n\n{colored(state.messages[-1].content, "light_grey")}"
    print(f"\n{'=' * 50} {'QUESTION':^10} {'=' * 50}\n{question}{content}\n{'=' * 112}\n")

    sys = """You are an end-user that wants to create a software product. Your requirements are simple but specific.
You will be reply to any questions as per the following rubric:

<Rubric>
  - You MUST always reply with an answer
  - You must NEVER reply with a question

  A correct reply:
  - Provides accurate and complete information
  - Contains no factual errors
  - Addresses all parts of the question
  - Is logically consistent
  - Is less that 2 sentences

  When replying, you should:
  - Be consistent with the earlier messages
  - If a new information is asked, create a simple situation
  - Do NOT let the user know you made a guess
  - If the conversation is getting long, do NOT add more requirements, if avoidable
</Rubric>

<Instructions>
  - Carefully read the input
  - Based on the input, reply to the question in a simple and consistent way 
  - If a new information is asked for, reply with the simplest guess but do not inform that it is a guess
</Instructions>

<Reminder>
You MUST always reply with an answer
</Reminder>

<input>
{input}
</input>
    """

    reply = await demo_user.ainvoke(
        [
            SystemMessage(content=sys.format(input=state.messages)),
            HumanMessage(content=question),
        ],
        config,
    )

    print(f"\n{'=' * 50} {'ANSWER':^10} {'=' * 50}\n{reply.content}\n{'=' * 112}\n")

    # user_input = interrupt({"query": msg})
    # return {"messages": user_input}

    return Command(
        update={
            "messages": [ToolMessage(content=reply.content, tool_call_id=tool_call_id)]
        }
    )


@tool("memorize", parse_docstring=True)
async def memorize(
    content: str,
    context: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    store: Annotated[BaseStore, InjectedStore],
    config: Annotated[RunnableConfig, InjectedToolArg],
    memory_id: Optional[uuid.UUID] = None,
):
    """Upsert a memory in the database.

    If a memory conflicts with an existing one, then just UPDATE the
    existing one by passing in memory_id - don't create two memories
    that are the same. If the user corrects a memory, UPDATE it.

    Args:
        content: The main content of the memory. For example:
            "User expressed interest in learning about French."
        context: Additional context for the memory. For example:
            "This was mentioned while discussing career options in Europe."
        memory_id: ONLY PROVIDE IF UPDATING AN EXISTING MEMORY.
        The memory to overwrite.
    """
    mem_id = memory_id or uuid.uuid4()
    from agent_template.configuration import Configuration

    user_id = Configuration.from_runnable_config(config).user_id
    await store.aput(
        ("memories", user_id),
        key=str(mem_id),
        value={"content": content, "context": context},
    )
    return f"Stored memory {mem_id}"


@tool("summarize", parse_docstring=True)
async def summarize(
    summary: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Summarize the agent output.

    Args:
        summary: The entire summary.
    """
    print(f"=== Summary ===")
    print(f"{summary}")
    print(f"=================")

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=summary,
                    tool_call_id=tool_call_id,
                )
            ],
            "summary": summary,
        }
    )


# Initialize the language model and the tools
all_tools = [human_feedback, memorize, summarize]

llm = init_chat_model()
llm_with_tools = llm.bind_tools(all_tools)
tool_node = ToolNode(all_tools, name="tools")


async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    # configurable = configuration.Configuration.from_runnable_config(config)

    user_id = config["configurable"]["user_id"]
    # Retrieve the most recent memories for context
    memories = await store.asearch(
        ("memories", user_id),
        query=str([m.content for m in state.messages[-3:]]),
        limit=10,
    )

    # Format memories for inclusion in the prompt
    formatted = "\n".join(
        f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories
    )
    if formatted:
        formatted = f"""
<memories>
{formatted}
</memories>"""

    # Prepare the system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys_prompt = config["configurable"]["gatherer_system_prompt"].format(
        user_info=formatted, time=datetime.now().isoformat()
    )

    # Invoke the language model with the prepared prompt and tools
    msg = await llm_with_tools.ainvoke(
        [SystemMessage(content=sys_prompt), *state.messages],
        config=config,
    )

    # print(f"CALL_MODEL_REUSULT:\n{msg}")

    return {"messages": [msg]}


async def gather_requirements(state: State, config: RunnableConfig):
    if state.messages[-1].tool_calls:
        return tool_node.name
    elif state.summary:
        return END
    else:
        return call_model.__name__


memory = MemorySaver()


builder = StateGraph(State, config_schema=Configuration)

# Define the flow of the memory extraction process
builder.add_node(call_model)
builder.add_node(tool_node.name, tool_node)

builder.add_edge(START, call_model.__name__)
builder.add_conditional_edges(
    call_model.__name__,
    gather_requirements,
    [tool_node.name, call_model.__name__, END],
)
builder.add_edge(tool_node.name, call_model.__name__)

graph = builder.compile(name="Requirements Gatherer")

__all__ = ["graph"]


class RequirementsGathererGraph(AgentGraph):
    def __init__(
        self,
        base_config: config.Configuration,
        checkpointer: Checkpointer = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(config, checkpointer, store)
        self._name = "Requirements Gatherer"
        self._config = Configuration(**asdict(base_config))

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        builder = StateGraph(State, config_schema=Configuration)
        builder.add_node(call_model)
        builder.add_node(tool_node.name, tool_node)

        builder.add_edge(START, call_model.__name__)
        builder.add_conditional_edges(
            call_model.__name__,
            gather_requirements,
            [tool_node.name, call_model.__name__, END],
        )
        builder.add_edge(tool_node.name, call_model.__name__)

        return builder
