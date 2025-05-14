"""Configuration for the graph."""

from dataclasses import dataclass

from common import config
from orchestrator import prompts


@dataclass(kw_only=True)
class Configuration(config.BaseConfiguration):
    """Main configuration class for the memory graph system."""

    system_prompt: str = prompts.get_prompt()


__all__ = ["Configuration"]
