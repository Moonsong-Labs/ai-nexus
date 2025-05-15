"""Stubs for tests."""

# ruff: noqa: D107 D101 D102

from typing import Any, List, Optional

from langchain_core.messages import (
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.configuration import AgentConfiguration
from common.graph import AgentGraph
from orchestrator.state import State


class MessageWheel:
    def __init__(self, messages: List[str]):
        self.messages = messages
        self.idx = 0

    def peek(self) -> str:
        return self.messages[self.idx]

    def next(self) -> str:
        msg = self.messages[self.idx]
        self.idx = (self.idx + 1) % len(self.messages)
        return msg


model_requirements_messages = MessageWheel(
    [
        """
        I collected all the details. Here are the requirements:    
            User wants a clean HTML website, with clean design.
            
        Additionally update memory: Always ask me questions starting with "Ola!""",
        """
        I collected all the details. Here are the requirements:
            User wants a clean HTML website, with clean design. It should focus on the mobile market,
            have a light scheme, be fast, responsive and load within 0.3 seconds.
            These are the complete requirements, nothing more is necessary.
        
        Additionally update memory: Always ask me questions starting with "Ola!
        """,
    ]
)
model_coder_messages = MessageWheel(
    [
        """I have finished coding.""",
        """I fixed the required issue.""",
    ]
)
model_tester_messages = MessageWheel(
    [
        """I found issues with code. Here are the details:
    HTML should have <!doctype> tag.
    """,
        """Everything looks good.""",
        """I found issues with code. Here are the details:
    <p> tag missing.
    """,
        """Everything looks good.""",
    ]
)
model_reviewer_messages = MessageWheel(
    [
        """I found issues with code. Here are the details:
    Add a new line in the end.
    """,
        """Everything looks good.""",
    ]
)


class RequirementsGathererStub(AgentGraph):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            "Requirements Gatherer Stub", agent_config, checkpointer, store
        )

    def create_builder(self) -> StateGraph:
        return None

    async def ainvoke(self, state: Any, config: RunnableConfig | None = None):
        """Async invoke."""
        return {
            "messages": state.messages,
            "summary": model_requirements_messages.next(),
        }


def architect(state: State, config: RunnableConfig, store: BaseStore):
    """Call design."""
    tool_call_id = state.messages[-1].tool_calls[0]["id"]
    return {
        "messages": [
            ToolMessage(
                content="""I am finished with the design. Here are the details:
                The design should be simple HTML file with CSS styling.
                """,
                tool_call_id=tool_call_id,
            )
        ]
    }


def coder(state: State, config: RunnableConfig, store: BaseStore):
    """Call code."""
    tool_call_id = state.messages[-1].tool_calls[0]["id"]
    return {
        "messages": [
            ToolMessage(
                content=model_coder_messages.next(),
                tool_call_id=tool_call_id,
            )
        ]
    }


def tester(state: State, config: RunnableConfig, store: BaseStore):
    """Call test."""
    tool_call_id = state.messages[-1].tool_calls[0]["id"]
    return {
        "messages": [
            ToolMessage(
                content=model_tester_messages.next(),
                tool_call_id=tool_call_id,
            )
        ]
    }


def reviewer(state: State, config: RunnableConfig, store: BaseStore):
    """Call review."""
    tool_call_id = state.messages[-1].tool_calls[0]["id"]
    return {
        "messages": [
            ToolMessage(
                content=model_reviewer_messages.next(),
                tool_call_id=tool_call_id,
            )
        ]
    }


def memorizer(state: State, config: RunnableConfig, store: BaseStore):
    """Memorize instructions."""
    message = state.messages[-1]
    tool_call_id = message.tool_calls[0]["id"]
    origin = message.tool_calls[0]["args"]["origin"]
    content = message.tool_calls[0]["args"]["content"]
    # msg = f"[MEMORIZE] for {origin}: {content}"
    # print(msg)  # noqa: T201
    return {
        "messages": [
            ToolMessage(
                content=f"Memorized '{content}' for '{origin}'",
                tool_call_id=tool_call_id,
            )
        ]
    }
