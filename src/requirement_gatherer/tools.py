"""Define he agent's tools."""

import uuid
from typing import Annotated, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState, InjectedStore
from langgraph.store.base import BaseStore
from langgraph.types import Command, interrupt
from termcolor import colored

from requirement_gatherer.configuration import Configuration
from requirement_gatherer.state import State


# ruff: noqa: T201
def create_human_feedback_tool(use_human_ai=False) -> BaseTool:
    """Create a tool that requests feedback from a human or an AI simulating a human.

    If configured to use a human, the tool prompts the user for input and returns their response. If configured to use an AI, it generates a reply using a chat model with specific instructions for concise and consistent answers. The tool returns a Command that updates the agent's state with the received feedback.
    """
    ai_user = init_chat_model() if use_human_ai else None

    @tool("human_feedback", parse_docstring=True)
    async def human_feedback(
        question: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        config: RunnableConfig,
    ) -> Command:
        """Request feedback on a question from either a human user or an AI simulating a human, based on agent configuration.

        If configured for human input, prompts the user and captures their response. If configured for AI, generates a reply using an AI model with specific behavioral instructions and updates the agent's state with the response.

        Args:
            question: The question to present for feedback.

        Returns:
            A Command that updates the agent's state with the feedback response.
        """
        agent_config: Configuration = config["configurable"]["agent_config"]

        # Return prompt if human user is requested
        if not agent_config.use_human_ai:
            content = question
            if state.messages[-1].content:
                content = f"{question}\n\n{state.messages[-1].content}"
            user_input = interrupt({"query": content})
            return {"messages": user_input}

        content = ""
        if state.messages[-1].content:
            content = f"\n\n{colored(state.messages[-1].content, 'light_grey')}"
        print(
            f"\n{'=' * 50} {'QUESTION':^10} {'=' * 50}\n{question}{content}\n{'=' * 112}\n"
        )

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

        reply = await ai_user.ainvoke(
            [
                SystemMessage(content=sys.format(input=state.messages)),
                HumanMessage(content=question),
            ],
            config,
        )

        print(f"\n{'=' * 50} {'ANSWER':^10} {'=' * 50}\n{reply.content}\n{'=' * 112}\n")

        return Command(
            update={
                "messages": [
                    ToolMessage(content=reply.content, tool_call_id=tool_call_id)
                ]
            }
        )

    return human_feedback


@tool("memorize", parse_docstring=True)
async def memorize(
    content: str,
    context: str,
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


# ruff: noqa: T201
@tool("summarize", parse_docstring=True)
async def summarize(
    summary: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Summarize the agent output.

    Args:
        summary: The entire summary.
    """
    print("=== Summary ===")
    print(f"{summary}")
    print("=================")

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
