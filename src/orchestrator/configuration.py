"""Configuration for the graph."""

from dataclasses import dataclass, field

from architect.configuration import (
    Configuration as ArchitectConfiguration,
)
from common.configuration import AgentConfiguration
from orchestrator import prompts
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)


@dataclass(kw_only=True)
class SubAgentConfig:
    """Sub-agent configuration for orchestrator."""

    use_stub: bool = True
    config: AgentConfiguration = field(default_factory=AgentConfiguration)


@dataclass(kw_only=True)
class RequirementsAgentConfig(SubAgentConfig):
    """Requirement-agent configuration for orchestrator."""

    use_stub: bool = True
    config: RequirementsConfiguration = field(default_factory=RequirementsConfiguration)


@dataclass(kw_only=True)
class ArchitectAgentConfig(SubAgentConfig):
    """Architect-agent configuration for orchestrator."""

    use_stub: bool = True
    config: ArchitectConfiguration = field(default_factory=ArchitectConfiguration)


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    system_prompt: str = field(default_factory=prompts.get_prompt)
    requirements_agent: RequirementsAgentConfig = field(
        default_factory=RequirementsAgentConfig
    )
    architect_agent: ArchitectAgentConfig = field(default_factory=ArchitectAgentConfig)
    coder_new_pr_agent: SubAgentConfig = field(default_factory=SubAgentConfig)
    coder_change_request_agent: SubAgentConfig = field(default_factory=SubAgentConfig)
    tester_agent: SubAgentConfig = field(default_factory=SubAgentConfig)
    reviewer_agent: SubAgentConfig = field(default_factory=SubAgentConfig)


__all__ = ["Configuration", "RequirementsAgentConfig", "SubAgentConfig"]
