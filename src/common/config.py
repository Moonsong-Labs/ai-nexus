"""Define the configurable parameters for the agents."""
import os
from dataclasses import dataclass, field, fields
from typing import Any, Optional

from common.components.memory import MemoryConfiguration
from langchain_core.runnables import RunnableConfig


@dataclass(kw_only=True)
class BaseConfiguration:
    """Base configuration class for the memory graph system."""

    user_id: str = "default"
    model: str = "google_genai:gemini-2.0-flash"
    provider: str | None = None
    memory: MemoryConfiguration = field(default_factory=MemoryConfiguration)


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