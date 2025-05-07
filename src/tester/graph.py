"""Graph implementation for the Test Agent workflow."""

import logging
from enum import Enum

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from tester import configuration, tools, utils
from tester.output import TesterAgentFinalOutput, TesterAgentQuestionOutput, TesterAgentTestOutput
from tester.state import State

logger = logging.getLogger(__name__)

llm = init_chat_model()


class WorkflowStage(str, Enum):
    """Enum to track the current stage of the Test Agent workflow."""
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    GENERATE_TESTS = "generate_tests"


async def analyze_requirements(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """
    Analyze requirements and identify ambiguities.
    Will either ask questions if information is missing or generate tests if requirements are clear.
    """
    configurable = configuration.Configuration.from_runnable_config(config)

    sys_prompt = (
        configurable.system_prompt
        + "\n\nCurrent task: Analyze the requirements and identify any ambiguities or missing information. "
        + "If you find any ambiguities or missing information, ask questions. "
        + "If the requirements are clear enough, generate tests based on them."
    )

    output = await llm.with_structured_output(TesterAgentFinalOutput).ainvoke(
        [{"role": "system", "content": sys_prompt}, *state.messages]
    )
    
    # Determine next stage based on whether questions were asked
    next_stage = WorkflowStage.ANALYZE_REQUIREMENTS if output.questions else WorkflowStage.GENERATE_TESTS
    
    return {
        "messages": [{"role": "assistant", "content": str(output)}],
        "workflow_stage": next_stage,
    }


async def generate_tests(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """
    Generate tests based on the requirements.
    If more information is needed, will ask questions instead.
    """
    configurable = configuration.Configuration.from_runnable_config(config)

    sys_prompt = (
        configurable.system_prompt
        + "\n\nCurrent task: Generate comprehensive tests based on the requirements. "
        + "Include traceability information linking each test to its requirement. "
        + "If you still need more information, ask specific questions instead."
    )

    output = await llm.with_structured_output(TesterAgentFinalOutput).ainvoke(
        [{"role": "system", "content": sys_prompt}, *state.messages]
    )
    
    # Determine next stage based on whether questions were asked
    next_stage = WorkflowStage.ANALYZE_REQUIREMENTS if output.questions else WorkflowStage.GENERATE_TESTS

    return {
        "messages": [{"role": "assistant", "content": str(output)}],
        "workflow_stage": next_stage,
    }


def route_based_on_workflow_stage(state: State):
    """Route to the appropriate node based on the current workflow stage."""
    # Check if workflow_stage is set
    if not hasattr(state, "workflow_stage"):
        # Default to starting at the beginning
        return WorkflowStage.ANALYZE_REQUIREMENTS

    # Route based on the current workflow stage
    return state.workflow_stage


# Create the graph with the workflow stages
builder = StateGraph(State, config_schema=configuration.Configuration)

# Add nodes for the simplified workflow
builder.add_node(WorkflowStage.ANALYZE_REQUIREMENTS, analyze_requirements)
builder.add_node(WorkflowStage.GENERATE_TESTS, generate_tests)

# Define the initial flow
builder.add_edge("__start__", WorkflowStage.ANALYZE_REQUIREMENTS)
builder.add_edge(WorkflowStage.ANALYZE_REQUIREMENTS, END)  # End and wait for user response
builder.add_edge(WorkflowStage.GENERATE_TESTS, END)  # End and wait for user response

# Add conditional routing for continuing the workflow after user inputs
builder.add_conditional_edges(
    "__start__",  # Start node
    route_based_on_workflow_stage,
    [WorkflowStage.ANALYZE_REQUIREMENTS, WorkflowStage.GENERATE_TESTS],
)

graph = builder.compile()
graph.name = "Tester"

__all__ = ["graph"]
