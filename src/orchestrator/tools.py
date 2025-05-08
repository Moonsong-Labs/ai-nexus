"""Define he agent's tools."""

from dataclasses import dataclass
from typing import Literal

from langchain_core.tools import tool


@dataclass
class Delegate:
    """Decision on where to delegate a task.

    - If requirements, then "requirements".
    - If architecture and design, then "architect".
    - If coding and implementation, then "coder".
    - If code needs testing, then "tester".
    - If code needs review, then "reviewer".
    """

    to: Literal[
        "orchestrator", "requirements", "architect", "coder", "tester", "reviewer"
    ]


@tool
def store_memory(
    origin: Literal["user", "requirements", "architect", "coder", "tester", "reviewer"],
    content: str,
):
    """Use this to memorize, store or remember  instructions."""
    msg = f"[MEMORIZE] for {origin}: {content}"
    # print(msg)  # noqa: T201
    return "Memorized '{content}' for '{origin}'"


@dataclass
class Memory:
    """Tool to update memory."""

    origin: Literal["user", "requirements", "architect", "coder", "tester", "reviewer"]
    content: str
