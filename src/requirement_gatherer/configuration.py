"""Configuration for the graph."""

import os
from dataclasses import dataclass, fields
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig

from common.configuration import AgentConfiguration
from requirement_gatherer import prompts


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    gatherer_system_prompt: str = prompts.SYSTEM_PROMPT
    use_human_ai: bool = False 

__all__ = ["Configuration"]
