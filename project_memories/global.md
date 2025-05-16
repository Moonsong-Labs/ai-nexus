# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is `langmem`, providing semantic search capabilities over stored memories. `AgentGraph` can now automatically initialize and provide `SemanticMemory` and its tools to subclasses based on its configuration.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools provided via `AgentGraph`/`SemanticMemory`, or custom tools like `file_dump`, or agent-specific tools like the Requirement Gatherer's `memorize` and `human_feedback`).
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols. System prompts can now be part of `BaseConfiguration` and used by `AgentGraph`.
6.  **Configuration Management:** Agents have configurable parameters, including LLM models, system prompts, and memory settings. This is managed via:
    *   A new `MemoryConfiguration` dataclass (`common.components.memory.MemoryConfiguration`) for memory-specific settings like `use_memory`, `load_static_memories`, and `user_id`.
    *   A common `BaseConfiguration` in `src/common/config.py`, which now includes a `memory: MemoryConfiguration` field and an optional `system_prompt: str`.
    *   Agent-specific `Configuration` dataclasses (e.g., in `src/orchestrator/configuration.py`, `src/requirement_gatherer/configuration.py`, `src/agent_template/configuration.py`) that subclass `BaseConfiguration`.
    *   An `AgentConfiguration` from `src/common/configuration.py` (implied) used by the Coder agent.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents. `SemanticMemory` (from `src/common/components/memory.py`) is now configured using `MemoryConfiguration`. `AgentGraph` can instantiate `SemanticMemory` if `base_config.memory.use_memory` is true, making memory tools available to the graph.
9.  **`AgentGraph` (REVISED):** A common base class (`src/common/graph.py`) for defining agent graphs.
    *   Its `__init__` method now primarily takes `base_config: Optional[BaseConfiguration]`, `checkpointer`, and `store`.
    *   It initializes an internal `_memory: Optional[SemanticMemory]` instance if `base_config.memory.use_memory` is true, using `base_config.memory` for the `SemanticMemory` configuration and `self._name` (default "BaseAgent", can be overridden by subclasses by setting `self._name` *before* calling `super().__init__`) for the `agent_name` namespace.
    *   Provides a `memory` property to access `self._memory`.
    *   Provides a `_create_call_model` base method that constructs a system message from `base_config.system_prompt` (if provided, otherwise a default prompt) and invokes the LLM.


## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and `AgentGraph` integration):** The project has integrated the `langmem` library to provide a robust and queryable semantic memory system.
*   **`MemoryConfiguration` (`common.components.memory.MemoryConfiguration` - NEW):** A dedicated dataclass to hold memory settings:
    *   `use_memory: bool = False`: Enables or disables memory functionality.
    *   `load_static_memories: bool = True`: Controls loading of static memories from JSON files.
    *   `user_id: str = "default"`: Defines the user ID for namespacing memories (e.g., for static memories or store keys).
*   **`BaseConfiguration` (`common.config.BaseConfiguration` - REVISED):** Now embeds a `MemoryConfiguration` instance via a `memory` field.
*   **`SemanticMemory` (`common.components.memory.SemanticMemory` - REVISED):**
    *   Its constructor now accepts `memory_config: Optional[MemoryConfiguration]`.
    *   Initialization (including loading static memories) is driven by the `memory_config` object (which defaults to `MemoryConfiguration()` if not provided).
*   **`AgentGraph` (`common.graph.AgentGraph` - REVISED):**
    *   Can automatically initialize a `SemanticMemory` instance if `base_config.memory.use_memory` is true.
    *   The initialized `SemanticMemory` uses `self._name` (default "BaseAgent", can be overridden by subclasses by setting `self._name` before `super().__init__`) as the `agent_name` for memory namespacing, and `base_config.memory` for its configuration (including `user_id`).
*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`).
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`, where `user_id` comes from `MemoryConfiguration.user_id`. The `agent_name` (from `AgentGraph._name`) is used by `SemanticMemory` internally, potentially for further namespacing or identification.
*   **Tools:**
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools (`manage_memory`, `search_memory`) from the `AgentGraph`-managed `SemanticMemory` instance (via `self.memory.get_tools()`).
    *   Requirement Gatherer: Uses a custom `memorize` tool.
*   **Static Memories:** JSON files in `.langgraph/static_memories/` can be loaded into the `BaseStore` under a static namespace if `memory_config.load_static_memories` is enabled in the `MemoryConfiguration` used by `SemanticMemory`.
*   **Shift:** The core principle of externalized memory remains, with `langmem` as the backend, now more seamlessly integrated via `AgentGraph` and configured through `BaseConfiguration` and `MemoryConfiguration`.


## 3. Project-Level Standards & Goals (`project_memories/PRD.md`)

This file outlines the overarching standards and technological choices for the AI Nexus project.

*   **Language:** English
*   **Goal:** Create a fully functional team of AI agents to design, develop, and maintain technical projects.
*   **Core Technologies & Frameworks:**
    *   **Python:** >= 3.12 (Primary programming language).
    *   **LangGraph:** Core framework for building AI agents.
    *   **`langmem`:** >= 0.0.25 (Provides semantic memory capabilities).
*   **Operation Details:**
    *   **OS:** Linux/Mac.
    *   **Provider:** Google Cloud (for deployment).
*   **Environment & Package Management:**
    *   **uv:** Used for managing Python virtual environments and installing packages.
    *   **python-dotenv:** Manages environment variables from `.env` files.
*   **Development Workflow & Build:**
    *   **Make:** Used as a task runner to automate common commands.
    *   **gcloud:** Deployment of services.
*   **Testing & Code Quality:**
    *   **pytest:** The main framework for running tests.
    *   **pytest-asyncio:** Enables testing of asynchronous code.
    *   **pytest-dotenv:** Loads environment variables specifically for tests.
    *   **pytest-watch (ptw):** Runs tests automatically when files change.
    *   **Ruff:** Performs code linting and formatting.
    *   **Mypy:** Conducts static type checking (currently not enforced in CI/default linting pass).
    *   **codespell:** Checks for spelling mistakes.
    *   **openevals:** Used for custom evaluation logic, particularly for the Coder agent.
    *   **debugpy:** Development dependency for remote debugging support.
    *   **CI Pipeline (`.github/workflows/checks.yml`):** Runs linting (Ruff, codespell), unit tests (`make test_unit`), and Coder integration tests (`make test_coder`). The Coder tests job requires `GOOGLE_API_KEY` as a secret.
*   **Version Control:** Git.
*   **LLM Models:**
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default model inherited from `BaseConfiguration` if not overridden, `BaseConfiguration` defaults to `gemini-2.0-flash`).
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning.


## 4. General Agent Architecture

AI Nexus employs a few architectural patterns for its agents:

**4.1. `agent_template` based Architecture (e.g., Code Reviewer, Grumpy) - REVISED**

This pattern is now embodied by `AgentTemplateGraph` which subclasses `AgentGraph`.

*   **`configuration.py` (`src/agent_template/configuration.py` - REVISED):**
    *   `Configuration` class now subclasses `common.config.BaseConfiguration`.
    *   Inherits `model`, `user_id` (the top-level field from `BaseConfiguration`), and `memory` (type `MemoryConfiguration`, which contains its own `memory.user_id` for namespacing) from `BaseConfiguration`.
    *   Retains its own `system_prompt` (defaulting to `prompts.SYSTEM_PROMPT`), which will be used by `AgentGraph`'s `_create_call_model` if set.
    *   The `use_static_mem` field is removed (functionality now handled by `BaseConfiguration.memory.load_static_memories`).
*   **`state.py` (`src/agent_template/state.py`):** (As previously described, with `user_id`)
*   **`agent.py` (`src/agent_template/agent.py`):** DELETED. Logic is superseded by `AgentTemplateGraph` and `AgentGraph`.
*   **`graph.py` (`src/agent_template/graph.py` - REVISED):**
    *   Defines `AgentTemplateGraph(AgentGraph)`.
    *   In its `__init__`, it instantiates its `Configuration` (which is a `BaseConfiguration` subclass).
    *   It sets `config.memory.use_memory = True` by default, enabling semantic memory via the parent `AgentGraph`.
    *   It sets `config.system_prompt` to the template's specific system prompt (`prompts.SYSTEM_PROMPT`).
    *   Calls `super().__init__(config, ...)` to initialize the `AgentGraph` with this configuration. The `AgentGraph` will then set up `SemanticMemory` using `self._name` (which defaults to "BaseAgent" as `AgentTemplateGraph` does not override it before `super().__init__`) as the `agent_name` for the memory namespace.
    *   `create_builder()`:
        *   Initializes an LLM.
        *   Retrieves tools from `self.memory.get_tools()` (provided by `AgentGraph` if memory is enabled) and potentially other tools (though current implementation only adds memory tools).
        *   Binds tools to the LLM.
        *   Adds a `call_model` node (using `self._create_call_model` from `AgentGraph`, which uses the system prompt from the config) and a `ToolNode` (if tools exist).
        *   Sets up standard routing: `__start__` -> `call_model` -> (conditional) `tools` -> `call_model` or `END`.
    *   A global `graph` instance is created: `graph = AgentTemplateGraph().compiled_graph`.
*   **`tools.py` (`src/agent_template/tools.py`):** (As previously described, `file_dump` tool; memory tools are now primarily accessed via `AgentGraph`'s `memory` component).
*   **`memory.py` (`src/agent_template/memory.py`):** DELETED.
*   **`src/common/components/memory.py` (REVISED):**
    *   Defines `MemoryConfiguration` dataclass (`use_memory`, `load_static_memories`, `user_id`).
    *   `SemanticMemory` class now takes `memory_config: Optional[MemoryConfiguration]` in its constructor and uses it for initialization. The `ConfigurationProtocol` is removed.
*   **`prompts.py` (`src/agent_template/prompts.py`):** (As previously described, instruction to mention memory retrieval).

**4.2. `AgentGraph` based Architecture (NEW - e.g., Orchestrator, Requirement Gatherer, Coder, AgentTemplateGraph)**

A common base class for modular graph definitions.

*   **`src/common/config.py` (REVISED):**
    ```python
    from dataclasses import dataclass, field
    from typing import Optional # Added for system_prompt
    from common.components.memory import MemoryConfiguration # NEW import

    @dataclass(kw_only=True)
    class BaseConfiguration:
        user_id: str = "default" # Note: user_id for memory is now in MemoryConfiguration.memory.user_id
        model: str = "google_genai:gemini-2.0-flash"
        provider: str | None = None
        system_prompt: Optional[str] = None # NEW
        memory: MemoryConfiguration = field(default_factory=MemoryConfiguration) # NEW
        # Agent-specific prompts or other configs are added in subclasses
    ```
*   **`src/common/configuration.py`:** (Existing module, not changed by this PR. Used by Coder agent. Its specific structure and relationship to `BaseConfiguration` are not detailed in PR#65, but it would need to be compatible with `AgentGraph`'s expectation of a `BaseConfiguration` for its `super().__init__`.)
*   **`src/common/graph.py` (REVISED):**
    *   Defines an abstract base class `AgentGraph(ABC)`.
    *   `__init__(self, base_config: Optional[BaseConfiguration] = None, checkpointer: Optional[Checkpointer] = None, store: Optional[BaseStore] = None)`:
        *   Stores `base_config`.
        *   Sets `self._name = "BaseAgent"` (subclasses can override this by setting `self._name` *before* calling `super().__init__` to change the `agent_name` for memory).
        *   If `base_config.memory.use_memory` is true, initializes `self._memory = SemanticMemory(agent_name=self._name, store=store, memory_config=base_config.memory)`.
    *   `memory` (property): Returns `self._memory`.
    *   `create_builder() -> StateGraph` (abstract method): To be implemented by subclasses.
    *   `_create_call_model(self, llm)` (NEW base method): Returns an async function that takes `state` and `config`. This function prepares a `SystemMessage` using `self._base_config.system_prompt` (if set, else a default "You are a helpful AI assistant." prompt) and invokes the LLM.
    *   `compiled_graph`: Property to get or compile the graph.
    *   `ainvoke(state, config)`: Invokes the compiled graph, merging instance config with call-time config.

Agents like Orchestrator, Requirement Gatherer, Coder, and now `AgentTemplateGraph` subclass `AgentGraph`.


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`)
*   **Architecture:** Uses the `AgentGraph` pattern. `OrchestratorGraph` in `src/orchestrator/graph.py` subclasses `common.graph.AgentGraph`. (Benefits from `AgentGraph` updates if its `Configuration` subclasses `BaseConfiguration` and leverages `BaseConfiguration.memory` and `BaseConfiguration.system_prompt`).
*   (Other details as previously described, no direct changes from this PR)

#### 5.2. Architect (`src/architect/`)
*   (No changes mentioned in PR - likely still follows its previous custom structure. The `agent_template.agent.Agent` class it might have implicitly relied on for examples is now DELETED. Still uses its own `upsert_memory`.)
*   (Other details as previously described)

#### 5.3. Coder (`src/coder/`)
*   **Architecture:** Uses the `AgentGraph` pattern. (Benefits from `AgentGraph` updates if its `AgentConfiguration` is compatible with `BaseConfiguration` and leverages `memory` and `system_prompt` fields for `super().__init__`).
*   (Other details as previously described, no direct changes from this PR)

#### 5.4. Code Reviewer (`src/code_reviewer/`)
*   (Likely follows `agent_template` pattern, so it will now use `AgentTemplateGraph` and its revised memory/config handling.)

#### 5.5. Tester (`src/tester/`)
*   (No changes mentioned in PR - assumed same as previous state)

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`)
*   **Architecture:** Uses the `AgentGraph` pattern. (Benefits from `AgentGraph` updates if its `Configuration` subclasses `BaseConfiguration` and leverages `BaseConfiguration.memory` and `BaseConfiguration.system_prompt`).
*   (Other details as previously described, no direct changes from this PR)

#### 5.7. Grumpy (`src/grumpy/`)
*   (Likely follows `agent_template` pattern, so it will now use `AgentTemplateGraph` and its revised memory/config handling.)

#### 5.8. Task Manager (`src/task_manager/`)
*   (No changes mentioned in PR - assumed same as previous state)


## 6. Testing Framework (`tests/`)

*   **`tests/integration_tests/test_graph.py` (UPDATED):**
    *   Updated to use `AgentTemplateGraph(base_config=config).compiled_graph` for testing the agent template's graph, reflecting the refactor from a `graph_builder` function to the `AgentTemplateGraph` class.
*   (Other test files as previously described)


## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`)

*   **README.md (UPDATED):**
    *   Expanded with new examples demonstrating semantic memory integration.
    *   Shows two ways:
        1.  Creating a custom agent by extending `AgentGraph` and enabling memory in its `BaseConfiguration` (e.g., `config = BaseConfiguration()`, `config.memory.use_memory = True`, `config.memory.user_id = "user123"`). The custom agent then calls `super().__init__(config, ...)`.
        2.  Enabling memory in an existing agent's configuration (e.g., for `AgentTemplateGraph`) by creating its specific `Configuration` object (e.g., `config = agent_template.Configuration()`), then setting `config.memory.use_memory = True`, `config.memory.load_static_memories = True`, `config.memory.user_id = "user123"`, and passing this `config` to the agent's constructor (e.g., `AgentTemplateGraph(base_config=config)`).
*   (Other workflow details as previously described)


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/
│   └── rules/
│       └── read-project-memories.mdc
├── .env.example
├── .gitignore
├── .vscode/
│   └── launch.json
├── .github/
│   └── workflows/
│       └── checks.yml
│       └── update_project_memory.yml
├── Makefile
├── README.md                     # UPDATED: Examples for semantic memory integration
├── agent_memories/
│   └── grumpy/
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml
├── scripts/
│   └── generate_project_memory.sh
│   └── update_project_memory_from_pr.sh
├── src/
│   ├── agent_template/
│   │   ├── __init__.py           # UPDATED: Exports AgentTemplateGraph, Configuration, State
│   │   ├── agent.py              # DELETED
│   │   ├── configuration.py      # UPDATED: Subclasses BaseConfiguration, memory fields inherited/managed via BaseConfiguration.memory
│   │   ├── graph.py              # UPDATED: Defines AgentTemplateGraph(AgentGraph), new graph init and structure
│   │   ├── memory.py             # DELETED
│   │   ├── prompts.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── architect/
│   │   ├── output.py
│   │   └── prompts/v0.1.md
│   ├── code_reviewer/
│   │   └── system_prompt.md
│   ├── coder/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── lg_server.py
│   │   ├── mocks.py
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── tools.py
│   │   └── README.md
│   ├── common/
│   │   ├── components/
│   │   │   ├── github_mocks.py
│   │   │   ├── github_tools.py
│   │   │   └── memory.py         # UPDATED: Defines MemoryConfiguration, SemanticMemory uses it, ConfigurationProtocol removed
│   │   ├── config.py             # REVISED: BaseConfiguration includes 'memory: MemoryConfiguration' and 'system_prompt: Optional[str]'
│   │   ├── configuration.py      # (Existing file, not changed by this PR)
│   │   ├── graph.py              # REVISED: AgentGraph __init__ takes BaseConfiguration, inits SemanticMemory, new _create_call_model, memory property
│   │   └── utils/
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py
│   │   ├── graph.py
│   │   ├── memory/
│   │   │   └── team.md
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── stubs/
│   │   │   └── __init__.py
│   │   ├── test.py
│   │   └── tools.py
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py
│   │   ├── graph.py
│   │   ├── prompts.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── task_manager/
│   └── tester/
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py
    │   ├── eval_coder.py
    │   ├── test_graph.py           # UPDATED: Uses AgentTemplateGraph(base_config=config).compiled_graph
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py
    │   ├── test_requirement_gatherer.py
    │   ├── test_task_manager.py
    │   └── test_tester_agent.py
    ├── testing/
    │   ├── __init__.py
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py
```
