"""Test Agent Graph Implementation."""

import logging
from datetime import datetime
from typing import Any, Coroutine, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.graph import AgentGraph
from tester.configuration import Configuration
from tester.prompts import get_stage_prompt
from tester.state import State, WorkflowStage

logger = logging.getLogger(__name__)


def _create_call_model(
    agent_config: Configuration,
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    async def call_model(
        state: State, config: RunnableConfig, *, store: Optional[BaseStore] = None
    ) -> dict:
        """Process the conversation based on the current workflow stage."""
        try:
            formatted = ""

            # Only try to retrieve memories if store is not None
            if store is not None:
                try:
                    user_id = config["configurable"]["user_id"]
                    # Retrieve the most recent memories for context
                    memories = await store.asearch(
                        ("memories", user_id),
                        query=str([m.content for m in state.messages[-3:]]),
                        limit=10,
                    )

                    # Format memories for inclusion in the prompt
                    formatted = "\n".join(
                        f"[{mem.key}]: {mem.value} (similarity: {mem.score})"
                        for mem in memories
                    )
                    if formatted:
                        formatted = f"""
            <memories>
            {formatted}
            </memories>"""
                except Exception as e:
                    logger.warning(f"Error retrieving memories: {e}")
                    formatted = ""

            # Get the current workflow stage
            current_stage = state.workflow_stage.value

            # Get the stage-specific prompt
            stage_prompt = get_stage_prompt(current_stage)

            # Prepare the system prompt with workflow stage, memories, and current time
            sys_prompt = agent_config.system_prompt.format(
                workflow_stage=stage_prompt,
                user_info=formatted,
                time=datetime.now().isoformat(),
            )

            # Invoke the language model with the prepared prompt and tools
            msg = await llm_with_tools.ainvoke(
                [SystemMessage(content=sys_prompt), *state.messages],
                config=config,
            )

            # Determine if we should move to the next stage based on the response
            next_stage = state.workflow_stage

            # Check for keywords indicating stage completion
            if current_stage == WorkflowStage.TESTING.value:
                if (
                    "tests are complete" in msg.content.lower()
                    or "testing complete" in msg.content.lower()
                ):
                    next_stage = WorkflowStage.COMPLETE

            return {"messages": [msg], "workflow_stage": next_stage}
        except Exception as e:
            logger.error(f"Error in call_model: {str(e)}")
            # Return a error message instead of failing completely
            return {
                "messages": [
                    SystemMessage(
                        content=f"There was an error processing your request: {str(e)}. Please try a different approach."
                    )
                ]
            }

    return call_model


def _create_workflow(call_model_name: str, tool_node_name: str):
    async def workflow(state: State, config: RunnableConfig):
        # If the last message has tool calls, route to the tool node
        if (
            state.messages
            and hasattr(state.messages[-1], "tool_calls")
            and state.messages[-1].tool_calls
        ):
            return tool_node_name

        return END

    return workflow


class TesterAgentGraph(AgentGraph):
    """Test agent graph."""

    _config: Configuration

    def __init__(
        self,
        *,
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize TesterAgentGraph.

        Args:
            use_human_ai: Whether to use human-AI interaction.
            agent_config: Optional Configuration instance.
            checkpointer: Optional Checkpointer instance.
            store: Optional BaseStore instance.
        """
        super().__init__(
            name="tester",
            agent_config=agent_config or Configuration(),
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        # Initialize the language model and the tools
        all_tools = []

        # Define node names explicitly to avoid confusion
        call_model_name = "call_model"
        tool_node_name = "tools"

        llm = init_chat_model(self._agent_config.model).bind_tools(all_tools)
        tool_node = ToolNode(all_tools, name=tool_node_name)
        call_model = _create_call_model(self._agent_config, llm)
        workflow = _create_workflow(call_model_name, tool_node_name)

        # Create the graph
        builder = StateGraph(State, config_schema=Configuration)
        builder.add_node(call_model_name, call_model)
        builder.add_node(tool_node_name, tool_node)

        # Define the graph flow
        builder.add_edge(START, call_model_name)
        builder.add_conditional_edges(
            call_model_name,
            workflow,
            [tool_node_name, call_model_name, END],
        )
        builder.add_edge(tool_node_name, call_model_name)

        return builder


# For langsmith
graph = TesterAgentGraph().compiled_graph

__all__ = [TesterAgentGraph.__name__, "graph"]
