"""Define the shared values."""

from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated

from common.state import Project


class WorkflowStage(str, Enum):
    """Enum to track the current stage of the Test Agent workflow."""

    ANALYZE_REQUIREMENTS = "analyze_requirements"
    TESTING = "testing"
    COMPLETE = "complete"


@dataclass(kw_only=True)
class State:
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages]
    """The messages in the conversation."""

    workflow_stage: WorkflowStage = WorkflowStage.TESTING
    """The current stage of the workflow."""

    project: Project
    """The active project."""

    summary: str = ""
    """The testing summary."""


__all__ = [
    "State",
    "WorkflowStage",
]
