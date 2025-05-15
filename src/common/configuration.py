"""Define the configurable parameters for the agents."""

from dataclasses import dataclass, field
from typing import Any

from common.components.memory import MemoryConfiguration

_LANGGRAPH_CONFIGURABLES = ["user_idmodelprovider"]


@dataclass(kw_only=True)
class AgentConfiguration:
    """Base agent configuration class for the memory graph system."""

    # langgraph config
    user_id: str = "default"
    model: str = "google_genai:gemini-2.0-flash"
    provider: str | None = None

    # extended config
    memory: MemoryConfiguration = field(default_factory=MemoryConfiguration)

    @property
    def langgraph_configurables(self) -> dict[str, Any]:
        """Return langgraph configurables."""
        return {
            k: v for k, v in self.__dict__.items() if k not in _LANGGRAPH_CONFIGURABLES
        }
