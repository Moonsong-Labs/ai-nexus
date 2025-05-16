"""Configuration for the graph."""

from dataclasses import dataclass, field

from common import config
from architect import prompts


@dataclass(kw_only=True)
class Configuration(config.BaseConfiguration):
    """Main configuration class for the memory graph system."""

    system_prompt: str = prompts.SYSTEM_PROMPT


__all__ = ["Configuration"]
