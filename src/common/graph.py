"""Common agent graph."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.components.memory import SemanticMemory
from common.configuration import AgentConfiguration

logger = logging.getLogger(__name__)


class AgentGraph(ABC):
    """Agent graph."""

    def __init__(
        self,
        *,
        name: str,
        agent_config: AgentConfiguration,
        checkpointer: Checkpointer = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize the AgentGraph with the given name, configuration, and optional persistence.

        Args:
            name: The unique name of the agent.
            agent_config: The configuration object specifying agent behavior and memory settings.
            checkpointer: Optional checkpointing mechanism for graph state persistence.
            store: Optional persistent storage for agent data.

        If memory is enabled in the agent configuration, initializes the semantic memory component.
        """
        self._name = name
        self._agent_config = agent_config or AgentConfiguration()
        self._checkpointer = checkpointer
        self._store = store
        self._builder = None
        self._compiled_graph = None

        # Initialize semantic memory only if use_memory is True
        self._memory = None
        if self._agent_config.memory.use_memory:
            self._memory = SemanticMemory(
                agent_name=self._name,
                store=store,
                memory_config=self._agent_config.memory,
            )

    @property
    def agent_config(self) -> AgentConfiguration:
        """Returns the agent's configuration object.

        Returns:
            AgentConfiguration: The configuration settings for this agent.
        """
        return self._agent_config

    def create_runnable_config(
        self, config: RunnableConfig | None = None
    ) -> AgentConfiguration:
        """Return the runnable configuration object.

        Returns:
            AgentConfiguration: The configuration settings for this agent.
        """
        config = config or RunnableConfig()
        config["configurable"] = {
            **self._agent_config.langgraph_configurables,
            **config.get("configurable", {}),
        }
        return config

    @property
    def memory(self) -> Optional[SemanticMemory]:
        """Returns the semantic memory component if initialized, otherwise None."""
        return self._memory

    @property
    def builder(self):
        """Returns the graph builder instance, creating it if it does not already exist."""
        if self._builder is None:
            self._builder = self.create_builder()
        return self._builder

    @abstractmethod
    def create_builder(self) -> StateGraph:
        """Create and returns a new StateGraph builder for constructing the agent's state graph.

        This method must be implemented by subclasses to provide the specific StateGraph
        builder appropriate for the agent's configuration and requirements.

        Returns:
            StateGraph: A builder instance for the agent's state graph.
        """
        pass

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Return the compiled state graph for the agent, creating it if not already compiled.

        The graph is compiled using the agent's name, checkpointer, and store, and the result is cached for future calls.

        Returns:
            CompiledStateGraph: The compiled state graph instance.
        """
        if self._compiled_graph is None:
            self._compiled_graph = self.builder.compile(
                name=self._name, checkpointer=self._checkpointer, store=self._store
            )
        return self._compiled_graph

    async def ainvoke(self, state: Any, config: RunnableConfig | None = None):
        """Asynchronously invokes the compiled agent graph with the given state and merged configuration.
        Args:
            state: The initial state to pass to the agent graph.
            config: Optional runtime configuration to merge with the agent's configuration.
        Returns:
            The result of the agent graph execution.
        """
        return await self.compiled_graph.ainvoke(state, self.create_runnable_config(config))   