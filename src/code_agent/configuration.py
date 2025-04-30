"""Configuration for the code agent."""

from typing import Optional

from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """Configuration for the code agent."""

    user_id: str = Field(..., description="User ID")
    model: str = Field(..., description="Model to use")
    system_prompt: str = Field(..., description="System prompt")

    @classmethod
    def from_runnable_config(cls, config: dict) -> "Configuration":
        """Create a configuration from a runnable config."""
        return cls(
            user_id=config["configurable"]["user_id"],
            model=config["configurable"]["model"],
            system_prompt=config["configurable"]["system_prompt"],
        ) 