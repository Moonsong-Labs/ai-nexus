"""Common agent graph."""

import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, Callable, Coroutine, Dict, List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import Tool
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from common.components.memory import SemanticMemory
from common.config import BaseConfiguration

logger = logging.getLogger(__name__)


class AgentGraph(ABC):
    """Agent graph."""

    def __init__(
        self,
        base_config: BaseConfiguration,
        checkpointer: Checkpointer = None,
        store: Optional[BaseStore] = None,
    ):
        """Initialize."""
        self._name = "BaseAgent"
        self._base_config = base_config or BaseConfiguration()
        self._checkpointer = checkpointer
        self._store = store
        self._builder = None
        self._compiled_graph = None

        # Initialize llm
        self._llm = init_chat_model(self._base_config.model)

        # Initialize semantic memory only if use_memory is True
        self._memory = None
        if self._base_config.memory.use_memory:
            self._memory = SemanticMemory(
                agent_name=self._name,
                store=store,
                memory_config=self._base_config.memory,
            )
            if self._memory:
                self.bind_tools(self._memory.get_tools())

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

    def _merge_config(self, config: RunnableConfig | None = None):
        if config is not None:
            new_config = RunnableConfig(**config)
            for k, v in asdict(self._base_config).items():
                if k not in new_config["configurable"]:
                    new_config["configurable"][k] = v
        return new_config

    @abstractmethod
    def create_builder(self) -> StateGraph:
        """Create a graph builder."""
        pass

    def bind_tools(self, tools: List[Tool]) -> None:
        """Bind a list of tools to the language model.

        Args:
            tools: List of tools to bind to the language model
        """
        if tools and self._llm:
            self._llm = self._llm.bind_tools(tools)

    def _create_call_model(
        self, llm: Runnable[LanguageModelInput, BaseMessage]
    ) -> Callable[..., Coroutine[Any, Any, Dict]]:
        """Create a function that calls the model.

        This is a basic implementation that derived classes can override.

        Args:
            llm_with_tools: A runnable language model with tools bound to it

        Returns:
            A coroutine function that processes the state and invokes the model
        """

        async def call_model(
            state: Any, config: RunnableConfig, *, store: BaseStore = None
        ) -> Dict:
            """Call the model with the current state."""
            # Get system prompt from config
            # After _merge_config, "system_prompt" should always be a key in configurable,
            # potentially with a value of None if explicitly set.
            system_prompt = self._base_config.system_prompt

            if system_prompt is None:
                logger.info(
                    "system_prompt was None in the configuration. Using default prompt."
                )
                system_prompt = "You are a helpful AI assistant."

            msg = await llm.ainvoke(
                [{"role": "system", "content": system_prompt}, *state.messages],
            )
            return {"messages": [msg]}

        return call_model

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

    async def ainvoke(self, state: Any, config: RunnableConfig | None = None):
        """Async invoke."""
        return await self.compiled_graph.ainvoke(state, self._merge_config(config))
