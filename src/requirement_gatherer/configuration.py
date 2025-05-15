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
    use_human_ai: bool = True

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }

        return cls(**{k: v for k, v in values.items() if v})


__all__ = ["Configuration"]
