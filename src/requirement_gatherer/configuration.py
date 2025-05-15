"""Configuration for the graph."""

from dataclasses import dataclass

from common.configuration import AgentConfiguration
from requirement_gatherer import prompts


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    gatherer_system_prompt: str = prompts.SYSTEM_PROMPT
    use_human_ai: bool = False


__all__ = ["Configuration"]
