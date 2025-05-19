"""Configuration for the graph."""

from dataclasses import dataclass

from common.configuration import AgentConfiguration
from tester import prompts


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    system_prompt: str = prompts.SYSTEM_PROMPT


__all__ = ["Configuration"]
