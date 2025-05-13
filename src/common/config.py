"""Define the configurable parameters for the agents."""

from dataclasses import dataclass


@dataclass(kw_only=True)
class Configuration:
    """Main configuration class for the memory graph system."""
    user_id: str = "default"
    model: str = "google_genai:gemini-2.0-flash"
    provider: str | None = None