"""Configuration for the graph."""

from dataclasses import dataclass

from common.config import BaseConfiguration
from tester import prompts


@dataclass(kw_only=True)
class Configuration(BaseConfiguration):
    """Main configuration class for the memory graph system."""

    system_prompt: str = prompts.SYSTEM_PROMPT


__all__ = ["Configuration"]
