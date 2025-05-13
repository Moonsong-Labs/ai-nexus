"""Common agent graph."""

from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.config import Configuration


class AgentGraph(ABC):
    """Agent graph."""

    def __init__(
        self,
        config: Configuration,
        checkpointer: Checkpointer = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize."""
        self._name = "Orchestrator"
        self._config = config
        self._checkpointer = checkpointer
        self._store = store
        self._compiled_graph = None
        self._builder = self.create_builder()

    @property
    def builder(self):
        """Return the builder."""
        return self._builder

    def _merge_config(self, config: RunnableConfig | None = None):
        if config is not None:
            new_config = RunnableConfig(**config)
            for k, v in asdict(self._config).items():
                if k not in new_config["configurable"]:
                    new_config["configurable"][k] = v
        return new_config

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
            self._compiled_graph = self._builder.compile(
                name=self._name, checkpointer=self._checkpointer, store=self._store
            )
        return self._compiled_graph

    async def ainvoke(self, state: Any, config: RunnableConfig | None = None):
        """Async invoke."""
        return await self.compiled_graph.ainvoke(state, self._merge_config(config))
