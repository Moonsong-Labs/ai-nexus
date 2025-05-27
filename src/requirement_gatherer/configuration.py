"""Configuration for the graph."""

from dataclasses import dataclass
from typing import Optional

from common.configuration import AgentConfiguration
from requirement_gatherer import prompts


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    gatherer_system_prompt: str = prompts.SYSTEM_PROMPT
    use_human_ai: bool = True
    human_ai_product: Optional[str] = None

    def __post_init__(self):
        """Initialize human_ai_product based on use_human_ai.

        If use_human_ai is True and human_ai_product is not provided,
        it defaults to prompts.HUMAN_AI_PRODUCT.
        Raises ValueError if use_human_ai is False and human_ai_product is set.
        """
        if self.use_human_ai:
            if self.human_ai_product is None:
                self.human_ai_product = prompts.HUMAN_AI_PRODUCT
        elif self.human_ai_product is not None:
            raise ValueError(
                "human_ai_product cannot be set when use_human_ai is False"
            )


__all__ = ["Configuration"]
