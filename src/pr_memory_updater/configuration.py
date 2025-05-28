"""Define the configurable parameters for the agent."""

from dataclasses import dataclass

from pr_memory_updater import prompts
from common.configuration import AgentConfiguration

AGENT_NAME = "pr_memory_updater"

@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Configuration class for the pr memory updater agent."""

    system_prompt: str = prompts.SCRIPT_SYSTEM_PROMPT
    """The system prompt to use for the agent."""
