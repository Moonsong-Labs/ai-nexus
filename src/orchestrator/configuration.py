"""Configuration for the graph."""

from dataclasses import dataclass, field

from architect.configuration import (
    Configuration as ArchitectConfiguration,
)
from common.configuration import AgentConfiguration
from orchestrator import prompts
from orchestrator.stubs import (
    MessageWheel,
    model_architect_messages,
    model_coder_change_request_messages,
    model_coder_new_pr_messages,
    model_requirements_messages,
    model_task_manager_messages,
)
from requirement_gatherer.configuration import (
    Configuration as RequirementsConfiguration,
)
from task_manager.configuration import (
    Configuration as TaskManagerConfiguration,
)


@dataclass(kw_only=True)
class SubAgentConfig:
    """Sub-agent configuration for orchestrator."""

    use_stub: bool = True
    stub_messages: MessageWheel = MessageWheel(["I finished the task."])
    config: AgentConfiguration = field(default_factory=AgentConfiguration)


@dataclass(kw_only=True)
class RequirementsAgentConfig(SubAgentConfig):
    """Requirement-agent configuration for orchestrator."""

    use_stub: bool = True
    stub_messages: MessageWheel = model_requirements_messages
    config: RequirementsConfiguration = field(default_factory=RequirementsConfiguration)


@dataclass(kw_only=True)
class ArchitectAgentConfig(SubAgentConfig):
    """Architect-agent configuration for orchestrator."""

    use_stub: bool = True
    stub_messages: MessageWheel = model_architect_messages
    config: ArchitectConfiguration = field(default_factory=ArchitectConfiguration)


@dataclass(kw_only=True)
class TaskManagerAgentConfig(SubAgentConfig):
    """Task-manager-agent configuration for orchestrator."""

    use_stub: bool = True
    stub_messages: MessageWheel = model_task_manager_messages
    config: TaskManagerConfiguration = field(default_factory=TaskManagerConfiguration)


@dataclass(kw_only=True)
class Configuration(AgentConfiguration):
    """Main configuration class for the memory graph system."""

    system_prompt: str = field(default_factory=prompts.get_prompt)
    requirements_agent: RequirementsAgentConfig = field(
        default_factory=RequirementsAgentConfig
    )
    architect_agent: ArchitectAgentConfig = field(default_factory=ArchitectAgentConfig)
    task_manager_agent: TaskManagerAgentConfig = field(
        default_factory=TaskManagerAgentConfig
    )
    coder_new_pr_agent: SubAgentConfig = field(
        default_factory=SubAgentConfig(stub_messages=model_coder_new_pr_messages)
    )
    coder_change_request_agent: SubAgentConfig = field(
        default_factory=SubAgentConfig(
            stub_messages=model_coder_change_request_messages
        )
    )
    tester_agent: SubAgentConfig = field(default_factory=SubAgentConfig)
    reviewer_agent: SubAgentConfig = field(default_factory=SubAgentConfig)


__all__ = ["Configuration", "RequirementsAgentConfig", "SubAgentConfig"]
