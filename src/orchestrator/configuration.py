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
    model_code_reviewer_messages,
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
from tester.configuration import (
    Configuration as TesterConfiguration,
)


@dataclass(kw_only=True)
class SubAgentConfig:
    """Sub-agent configuration for orchestrator.

    Attributes:
        use_stub: Whether to use a stub for the sub-agent. A stub is a simplified
            implementation of the agent that is used for testing purposes.
        stub_messages: The messages to use for the stub.
        config: The configuration for the sub-agent.
    """

    """Whether to use a stub for the sub-agent."""
    use_stub: bool = True
    """The messages to use for the stub."""
    stub_messages: MessageWheel = MessageWheel(["I finished the task."])
    """The configuration for the sub-agent."""
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
class TesterAgentConfig(SubAgentConfig):
    """Tester-agent configuration for orchestrator."""

    use_stub: bool = True
    config: TesterConfiguration = field(default_factory=TesterConfiguration)


@dataclass(kw_only=True)
class CodeReviewerAgentConfig(SubAgentConfig):
    """Code reviewer configuration for orchestrator."""

    use_stub: bool = True
    stub_messages: MessageWheel = model_code_reviewer_messages
    config: AgentConfiguration = field(default_factory=AgentConfiguration)


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
    tester_agent: TesterAgentConfig = field(default_factory=TesterAgentConfig)
    reviewer_agent: CodeReviewerAgentConfig = field(
        default_factory=SubAgentConfig(stub_messages=model_code_reviewer_messages)
    )
    github_base_branch: str = "main"


__all__ = ["Configuration", "RequirementsAgentConfig", "SubAgentConfig"]
