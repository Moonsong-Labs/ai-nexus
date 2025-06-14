"""Define the configurable parameters for the agent."""

from dataclasses import dataclass

from common.configuration import AgentConfiguration
from task_manager import prompts

TASK_MANAGER_MODEL = "google_genai:gemini-2.5-flash-preview-04-17"


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    use_stub: bool = True
    use_human_ai: bool = False
    task_manager_system_prompt: str = prompts.SYSTEM_PROMPT


__all__ = ["Configuration"]
