"""Configuration for the graph."""

from dataclasses import dataclass

from architect import prompts
from common.configuration import AgentConfiguration


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    architect_system_prompt: str = prompts.SYSTEM_PROMPT
    use_human_ai: bool = False


__all__ = ["Configuration"]
