"""Define the configurable parameters for the agent."""

from dataclasses import dataclass

from agent_template import prompts
from common.configuration import AgentConfiguration

AGENT_NAME = "base_agent"


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Configuration class for the agent template."""

    system_prompt: str = prompts.SYSTEM_PROMPT
    """The system prompt to use for the agent."""
