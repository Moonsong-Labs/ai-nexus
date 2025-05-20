"""Stubs for tests."""

# ruff: noqa: D107 D101 D102

from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from architect.state import State as ArchitectState
from code_reviewer.state import State as CodeReviewerState
from coder.state import State as CoderState
from common.configuration import AgentConfiguration
from common.graph import AgentGraph
from requirement_gatherer.state import State as RequirementsState
from tester.state import State as TesterState

T = TypeVar("T")


class StubGraph(AgentGraph, Generic[T]):
    """Base class for stub graphs that follow a simple run pattern."""

    def __init__(
        self,
        *,
        name: str,
        state_type: type[T],
        run_fn: Callable[[T, Optional[RunnableConfig]], Awaitable[Dict[str, Any]]],
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            name=name, agent_config=agent_config, checkpointer=checkpointer, store=store
        )
        self._state_type = state_type
        self._run_fn = run_fn

    def create_builder(self) -> StateGraph:
        builder = StateGraph(self._state_type)
        builder.add_node("run", self._run_fn)
        builder.add_edge(START, "run")
        builder.add_edge("run", END)
        return builder


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
model_architect_messages = MessageWheel(
    [
        """I have created the architecture for the project.""",
    ]
)
model_task_manager_messages = MessageWheel(
    [
        """I have finished creating all the tasks and planning for the project.""",
    ]
)
model_coder_new_pr_messages = MessageWheel(
    [
        """I have finished coding the new PR is #69 and the branch is code-agent-new-pr.""",
    ]
)
model_coder_change_request_messages = MessageWheel(
    [
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
model_code_reviewer_messages = MessageWheel(
    [
        """I found issues with code. Here are the details:
    Add a new line in the end.
    """,
        """Everything looks good.""",
    ]
)


class RequirementsGathererStub(StubGraph[RequirementsState]):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            name="Requirements Gatherer Stub",
            state_type=RequirementsState,
            run_fn=lambda state, config: {
                "messages": state.messages,
                "summary": model_requirements_messages.next(),
            },
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )


class ArchitectStub(StubGraph[ArchitectState]):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            name="Architect Stub",
            state_type=ArchitectState,
            run_fn=lambda state, config: {
                "messages": state.messages,
                "summary": model_architect_messages.next(),
            },
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )


class CoderNewPRStub(StubGraph[CoderState]):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            name="Coder New PR Stub",
            state_type=CoderState,
            run_fn=lambda state, config: {
                "messages": state.messages,
                "summary": model_coder_new_pr_messages.next(),
            },
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )


class CoderChangeRequestStub(StubGraph[CoderState]):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            name="Coder Change Request Stub",
            state_type=CoderState,
            run_fn=lambda state, config: {
                "messages": state.messages,
                "summary": model_coder_change_request_messages.next(),
            },
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )


class TesterStub(StubGraph[TesterState]):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            name="Tester Stub",
            state_type=TesterState,
            run_fn=lambda state, config: {
                "messages": state.messages,
                "summary": model_tester_messages.next(),
            },
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )


class CodeReviewerStub(StubGraph[CodeReviewerState]):
    def __init__(
        self,
        *,
        agent_config: Optional[AgentConfiguration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        super().__init__(
            name="CodeReviewer Stub",
            state_type=CodeReviewerState,
            run_fn=lambda state, config: {
                "messages": state.messages,
                "summary": model_code_reviewer_messages.next(),
            },
            agent_config=agent_config,
            checkpointer=checkpointer,
            store=store,
        )
