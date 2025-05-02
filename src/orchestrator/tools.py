"""Define he agent's tools."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Delegate:
    """Decision on where to delegate a task.

    - If requirements, then "requirements".
    - If architecture and design, then "architect".
    - If coding and implementation, then "coder".
    - If code needs testing, then "tester".
    - If code needs review, then "reviewer".
    - If something is to be memorized, then "memorizer".
    """

    to: Literal[
        "orchestrator", "requirements", "architect", "coder", "tester", "reviewer", "memorizer"
    ]
    origin: Literal[
        "user", "requirements", "architect", "coder", "tester", "reviewer"
    ]
    content: str

@dataclass
class Memory:
    """Tool to update memory."""
    memory: str
