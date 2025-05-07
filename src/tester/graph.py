"""Graph implementation for the Test Agent workflow."""

import asyncio
import logging
from datetime import datetime
from enum import Enum

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from tester import configuration, tools, utils
from tester.output import TesterAgentFinalOutput
from tester.state import State

logger = logging.getLogger(__name__)

llm = init_chat_model()

class WorkflowStage(str, Enum):
    """Enum to track the current stage of the Test Agent workflow."""
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    GENERATE_QUESTIONS = "generate_questions"
    PROCESS_ANSWERS = "process_answers"
    GROUP_REQUIREMENTS = "group_requirements"
    GENERATE_TESTS = "generate_tests"
    COMPLETE = "complete"

async def analyze_requirements(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Analyze requirements and identify ambiguities."""
    configurable = configuration.Configuration.from_runnable_config(config)
    
    sys_prompt = configurable.system_prompt + "\n\nCurrent task: Analyze the requirements and identify any ambiguities or missing information."
    
    output = await llm.ainvoke(
        [{"role": "system", "content": sys_prompt}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    
    # Update state to move to the next stage
    return {
        "messages": [{"role": "assistant", "content": output.content}],
        "workflow_stage": WorkflowStage.GENERATE_QUESTIONS
    }

async def generate_questions(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Generate questions about unclear or missing aspects of the requirements."""
    configurable = configuration.Configuration.from_runnable_config(config)
    
    sys_prompt = configurable.system_prompt + "\n\nCurrent task: Generate questions about unclear or missing aspects of the requirements."
    
    output = await llm.ainvoke(
        [{"role": "system", "content": sys_prompt}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    
    # Update state to wait for user answers
    return {
        "messages": [{"role": "assistant", "content": output.content}],
        "workflow_stage": WorkflowStage.PROCESS_ANSWERS
    }

async def process_answers(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Process user's answers to questions."""
    configurable = configuration.Configuration.from_runnable_config(config)
    
    sys_prompt = configurable.system_prompt + "\n\nCurrent task: Process the answers to your questions and prepare to group requirements."
    
    output = await llm.ainvoke(
        [{"role": "system", "content": sys_prompt}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    
    # Move to grouping requirements
    return {
        "messages": [{"role": "assistant", "content": output.content}],
        "workflow_stage": WorkflowStage.GROUP_REQUIREMENTS
    }

async def group_requirements(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Group requirements by category/functionality."""
    configurable = configuration.Configuration.from_runnable_config(config)
    
    sys_prompt = configurable.system_prompt + "\n\nCurrent task: Group requirements by category/functionality."
    
    output = await llm.ainvoke(
        [{"role": "system", "content": sys_prompt}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    
    # Move to generating tests
    return {
        "messages": [{"role": "assistant", "content": output.content}],
        "workflow_stage": WorkflowStage.GENERATE_TESTS,
        "categories": [],  # This would be populated with actual categories
        "current_category_index": 0
    }

async def generate_tests(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Generate tests for the current category."""
    configurable = configuration.Configuration.from_runnable_config(config)
    
    # Get the current category (in a real implementation, this would come from state.categories)
    current_category = f"Category {state.current_category_index + 1}"
    
    sys_prompt = (
        configurable.system_prompt + 
        f"\n\nCurrent task: Generate tests for the category: {current_category}. " +
        "Include traceability information linking each test to its requirement."
    )
    
    output = await llm.ainvoke(
        [{"role": "system", "content": sys_prompt}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    
    # Update state to possibly move to the next category
    next_category_index = state.current_category_index + 1
    
    # In a real implementation, check if we've processed all categories
    has_more_categories = next_category_index < len(state.categories) if hasattr(state, 'categories') and state.categories else False
    
    return {
        "messages": [{"role": "assistant", "content": output.content}],
        "current_category_index": next_category_index,
        "workflow_stage": WorkflowStage.GENERATE_TESTS if has_more_categories else WorkflowStage.COMPLETE
    }

def route_based_on_workflow_stage(state: State):
    """Route to the appropriate node based on the current workflow stage."""
    # Check if workflow_stage is set
    if not hasattr(state, "workflow_stage"):
        # Default to starting at the beginning
        return "analyze_requirements"
    
    # Route based on the current workflow stage
    return state.workflow_stage

# Create the graph with the workflow stages
builder = StateGraph(State, config_schema=configuration.Configuration)

# Add nodes for each stage of the workflow
builder.add_node("analyze_requirements", analyze_requirements)
builder.add_node("generate_questions", generate_questions)
builder.add_node("process_answers", process_answers)
builder.add_node("group_requirements", group_requirements)
builder.add_node("generate_tests", generate_tests)

# Define the initial flow
builder.add_edge("__start__", "analyze_requirements")
builder.add_edge("analyze_requirements", "generate_questions")
builder.add_edge("generate_questions", END)  # Wait for user to answer questions

# Add conditional routing for continuing the workflow after user inputs
builder.add_conditional_edges(
    "__start__",  # Start node
    route_based_on_workflow_stage,
    ["analyze_requirements", "generate_questions", "process_answers", "group_requirements", "generate_tests"]
)

# Define the rest of the workflow
builder.add_edge("process_answers", "group_requirements")
builder.add_edge("group_requirements", "generate_tests")
builder.add_edge("generate_tests", END)  # End or wait for user input before next category

graph = builder.compile()
graph.name = "Tester"

__all__ = ["graph"]
