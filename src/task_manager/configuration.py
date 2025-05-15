"""Define the configurable parameters for the agent."""

from dataclasses import dataclass

from common.configuration import AgentConfiguration
from task_manager import prompts

TASK_MANAGER_MODEL = "google_genai:gemini-2.5-flash-preview-04-17"


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    task_manager_system_prompt: str = prompts.SYSTEM_PROMPT
    model: str = TASK_MANAGER_MODEL


__all__ = ["Configuration"]
