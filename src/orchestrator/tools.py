"""Define he agent's tools."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Delegate:
    """Decision on where to delegate."""

    to: Literal[
        "orchestrator", "requirements", "architect", "coder", "tester", "reviewer"
    ]
