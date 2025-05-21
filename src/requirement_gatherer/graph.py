"""Graphs that extract memories on a schedule."""

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
from requirement_gatherer import tools
from requirement_gatherer.configuration import Configuration
from requirement_gatherer.state import State

logger = logging.getLogger(__name__)


def _create_call_model(
    agent_config: Configuration,
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
) -> Coroutine[Any, Any, dict]:
    """Create an asynchronous function that queries recent user memories and invokes a language model with contextual prompts.

    The returned coroutine retrieves the user's recent memories from the store, formats them for context, constructs a system prompt including these memories and the current timestamp, and asynchronously calls the language model with the prompt and conversation history. Returns a dictionary containing the model's response message.
    """

    async def call_model(
        state: State, config: RunnableConfig, *, store: BaseStore
    ) -> dict:
        """Extract the user's state from the conversation and update the memory."""
        user_id = config["configurable"]["user_id"]
        # Retrieve the most recent memories for context
        memories = await store.asearch(
            ("memories", user_id),
            query=str([m.content for m in state.messages[-3:]]),
            limit=10,
        )

        # Format memories for inclusion in the prompt
        formatted = "\n".join(
            f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories
        )
        if formatted:
            formatted = f"""
    <memories>
    {formatted}
    </memories>"""

        # Prepare the system prompt with user memories and current time
        # This helps the model understand the context and temporal relevance
        sys_prompt = agent_config.gatherer_system_prompt.format(
            user_info=formatted, time=datetime.now().isoformat()
        )

        # Invoke the language model with the prepared prompt and tools
        msg = await llm_with_tools.ainvoke(
            [SystemMessage(content=sys_prompt), *state.messages],
            config=config,
        )

        # print(f"CALL_MODEL_REUSULT:\n{msg}")

        return {"messages": [msg]}

    return call_model


def _create_gather_requirements(
    agent_config: Configuration,
    call_model: Coroutine[Any, Any, dict],
    tool_node: ToolNode,
):
    """Create an asynchronous function to determine the next step in the requirements gathering graph.

    The returned function inspects the conversation state to decide whether to route to a tool node, end the process, or continue the conversation with the model.
    """

    async def gather_requirements(state: State, config: RunnableConfig):
        if state.messages and state.messages[-1].tool_calls:
            return tool_node.name
        elif state.summary:
            return END
        else:
            return call_model.__name__

    return gather_requirements


class RequirementsGraph(AgentGraph):
    """Requirements gatherer graph."""

    _agent_config: Configuration

    def __init__(
        self,
        *,
        agent_config: Optional[Configuration] = None,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize a RequirementsGraph instance with optional configuration, checkpointer, and store.

        If no configuration is provided, a default Configuration is used.
        """
        super().__init__(
            name="Requirements Gatherer",
            agent_config=agent_config or Configuration(),
            checkpointer=checkpointer,
            store=store,
        )

    def create_builder(self) -> StateGraph:
        """Construct and returns the requirements gathering agent's state graph.

        Initializes the language model and associated tools, creates the necessary graph nodes and edges, and defines the flow for gathering requirements through conversational interactions.
        """
        # Initialize the language model and the tools
        all_tools = [
            tools.create_human_feedback_tool(
                self._agent_config,
            ),
            tools.set_project,
            tools.create_memorize_tool(self._agent_config),
            tools.summarize,
        ]

        llm = init_chat_model(self._agent_config.model).bind_tools(all_tools)
        tool_node = ToolNode(all_tools, name="tools")
        call_model = _create_call_model(self._agent_config, llm)
        gather_requirements = _create_gather_requirements(
            self._agent_config, call_model, tool_node
        )

        builder = StateGraph(State, config_schema=Configuration)
        builder.add_node(call_model)
        builder.add_node(tool_node.name, tool_node)

        builder.add_edge(START, call_model.__name__)
        builder.add_conditional_edges(
            call_model.__name__,
            gather_requirements,
            [tool_node.name, call_model.__name__, END],
        )
        builder.add_edge(tool_node.name, call_model.__name__)

        return builder


# For langsmith
graph = RequirementsGraph().compiled_graph

__all__ = [RequirementsGraph.__name__, "graph"]
