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
        """Initialize."""
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
        """Return the agent config."""
        return self._agent_config

    @property
    def memory(self) -> Optional[SemanticMemory]:
        """Return the semantic memory component."""
        return self._memory

    @property
    def builder(self):
        """Return the builder."""
        if self._builder is None:
            self._builder = self.create_builder()
        return self._builder

    @abstractmethod
    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        pass

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Compile the graph.

        Args:
            use_store: Whether to use checkpointer and store
        """
        if self._compiled_graph is None:
            self._compiled_graph = self.builder.compile(
                name=self._name, checkpointer=self._checkpointer, store=self._store
            )
        return self._compiled_graph

    def _merge_config(self, config: RunnableConfig) -> RunnableConfig:
        """Merge user provided config with the agent config and populate well-known langgraph configurables."""
        new_config = RunnableConfig(**config)
        new_config["configurable"] = {
            **self._agent_config.langgraph_configurables,
            **config.get("configurable", {}),
            **{"agent_config": self._agent_config},
        }
        return new_config

    async def ainvoke(self, state: Any, config: RunnableConfig | None = None):
        """Async invoke."""
        return await self.compiled_graph.ainvoke(state, self._merge_config(config))
