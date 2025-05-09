"""Graph implementation for the Test Agent workflow."""

import logging
from enum import Enum
from typing import List

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from tester import configuration, utils
from tester.output import (
    TesterAgentFinalOutput,
)
from tester.state import State

logger = logging.getLogger(__name__)

# Initialize with a specific model to avoid errors in tests
llm = init_chat_model("google_genai:gemini-2.0-flash-lite")


class WorkflowStage(str, Enum):
    """Enum to track the current stage of the Test Agent workflow."""

    ANALYZE_REQUIREMENTS = "analyze_requirements"
    GENERATE_TESTS = "generate_tests"


def ensure_messages_format(messages: List[dict]) -> List[BaseMessage]:
    """Ensure messages are in the correct format for LLM input."""
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, BaseMessage):
            formatted_messages.append(msg)
        elif isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                formatted_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                formatted_messages.append(AIMessage(content=content))
            else:  # Default to user/human
                formatted_messages.append(HumanMessage(content=content))
    return formatted_messages


async def analyze_requirements(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Analyze requirements and identify ambiguities.
    Will either ask questions if information is missing or generate tests if requirements are clear.
    """  # noqa: D205
    try:
        configurable = configuration.Configuration.from_runnable_config(config)

        sys_prompt = (
            configurable.system_prompt
            + "\n\nCurrent task: Analyze the requirements and identify any ambiguities or missing information. "
            + "If you find any ambiguities or missing information, ask questions. "
            + "If the requirements are clear enough, generate tests based on them."
        )

        # Ensure messages are in the correct format
        messages = ensure_messages_format(state.messages)

        # Add system message at the beginning if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=sys_prompt))

        # Get model configuration from the configurable
        model_config = {
            "configurable": utils.split_model_and_provider(configurable.model)
        }

        # Invoke the LLM
        output = await llm.with_structured_output(TesterAgentFinalOutput).ainvoke(
            messages, model_config
        )

        # Determine next stage based on whether questions were asked
        next_stage = (
            WorkflowStage.ANALYZE_REQUIREMENTS
            if output.questions
            else WorkflowStage.GENERATE_TESTS
        )

        return {
            "messages": state.messages + [AIMessage(content=str(output))],
            "workflow_stage": next_stage,
        }
    except Exception as e:
        logger.error(f"Error in analyze_requirements: {e}")
        # Return a default response in case of error
        return {
            "messages": state.messages
            + [AIMessage(content="Error analyzing requirements")],
            "workflow_stage": WorkflowStage.ANALYZE_REQUIREMENTS,
        }


async def generate_tests(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """Generate tests based on the requirements.
    If more information is needed, will ask questions instead.
    """  # noqa: D205
    try:
        configurable = configuration.Configuration.from_runnable_config(config)

        sys_prompt = (
            configurable.system_prompt
            + "\n\nCurrent task: Generate comprehensive tests based on the requirements. "
            + "Include traceability information linking each test to its requirement. "
            + "If you still need more information, ask specific questions instead."
        )

        # Ensure messages are in the correct format
        messages = ensure_messages_format(state.messages)

        # Add system message at the beginning if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=sys_prompt))

        # Get model configuration from the configurable
        model_config = {
            "configurable": utils.split_model_and_provider(configurable.model)
        }

        # Invoke the LLM
        output = await llm.with_structured_output(TesterAgentFinalOutput).ainvoke(
            messages, model_config
        )

        # Determine next stage based on whether questions were asked
        next_stage = (
            WorkflowStage.ANALYZE_REQUIREMENTS
            if output.questions
            else WorkflowStage.GENERATE_TESTS
        )

        return {
            "messages": state.messages + [AIMessage(content=str(output))],
            "workflow_stage": next_stage,
        }
    except Exception as e:
        logger.error(f"Error in generate_tests: {e}")
        # Return a default response in case of error
        return {
            "messages": state.messages + [AIMessage(content="Error generating tests")],
            "workflow_stage": WorkflowStage.GENERATE_TESTS,
        }


def route_based_on_workflow_stage(state: State):
    """Route to the appropriate node based on the current workflow stage."""
    # Check if workflow_stage is set
    if not hasattr(state, "workflow_stage"):
        # Default to starting at the beginning
        return WorkflowStage.ANALYZE_REQUIREMENTS

    # Route based on the current workflow stage
    return state.workflow_stage


builder = StateGraph(State, config_schema=configuration.Configuration)

builder.add_node(WorkflowStage.ANALYZE_REQUIREMENTS, analyze_requirements)
builder.add_node(WorkflowStage.GENERATE_TESTS, generate_tests)

builder.add_edge("__start__", WorkflowStage.ANALYZE_REQUIREMENTS)
builder.add_edge(WorkflowStage.ANALYZE_REQUIREMENTS, END)
builder.add_edge(WorkflowStage.GENERATE_TESTS, END)

builder.add_conditional_edges(
    "__start__",
    route_based_on_workflow_stage,
    [WorkflowStage.ANALYZE_REQUIREMENTS, WorkflowStage.GENERATE_TESTS],
)

graph = builder.compile()
graph.name = "Tester"


__all__ = ["graph"]
