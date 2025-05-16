# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is `langmem`, providing semantic search capabilities over stored memories. `AgentGraph` can now automatically initialize and provide `SemanticMemory` and its tools to subclasses based on its configuration.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools provided via `AgentGraph`/`SemanticMemory`, or custom tools like `file_dump`, or agent-specific tools like the Requirement Gatherer's `memorize` and `human_feedback`).
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols. System prompts are now typically part of agent-specific `Configuration` classes (which subclass `AgentConfiguration`) and used by the agent's graph logic (e.g., in custom `call_model` implementations).
6.  **Configuration Management (REVISED):** Agents have configurable parameters, including LLM models, system prompts, and memory settings. This is managed via:
    *   A `MemoryConfiguration` dataclass (`common.components.memory.MemoryConfiguration`) for memory-specific settings like `use_memory`, `load_static_memories`, and `user_id`.
    *   A common `AgentConfiguration` in `src/common/configuration.py` (NEW, replaces `BaseConfiguration`), which includes a `memory: MemoryConfiguration` field. It also includes `user_id`, `model`, and `provider` for LangGraph. Agent-specific system prompts are defined in subclasses.
    *   Agent-specific `Configuration` dataclasses (e.g., in `src/orchestrator/configuration.py`, `src/requirement_gatherer/configuration.py`, `src/agent_template/configuration.py`) that subclass `AgentConfiguration` and can include their own `system_prompt` or other specific settings.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents. `SemanticMemory` (from `src/common/components/memory.py`) is configured using `MemoryConfiguration`. `AgentGraph` can instantiate `SemanticMemory` if `agent_config.memory.use_memory` is true, making memory tools available to the graph.
9.  **`AgentGraph` (REVISED):** A common base class (`src/common/graph.py`) for defining agent graphs.
    *   Its `__init__` method now takes `name: str`, `agent_config: AgentConfiguration`, `checkpointer`, and `store`.
    *   It initializes an internal `_memory: Optional[SemanticMemory]` instance if `agent_config.memory.use_memory` is true, using `agent_config.memory` for the `SemanticMemory` configuration and the passed `name` for the `agent_name` namespace.
    *   Provides an `agent_config` property to access `self._agent_config`.
    *   Provides a `memory` property to access `self._memory`.
    *   The base `_create_call_model` method has been removed; model calling logic (including system prompt handling) is now typically implemented within specific agent graph builders or helper functions.


## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and `AgentGraph` integration):** The project has integrated the `langmem` library to provide a robust and queryable semantic memory system.
*   **`MemoryConfiguration` (`common.components.memory.MemoryConfiguration`):** A dedicated dataclass to hold memory settings:
    *   `use_memory: bool = False`: Enables or disables memory functionality.
    *   `load_static_memories: bool = True`: Controls loading of static memories from JSON files.
    *   `user_id: str = "default"`: Defines the user ID for namespacing memories (e.g., for static memories or store keys).
*   **`AgentConfiguration` (`common.configuration.AgentConfiguration` - NEW, replaces `BaseConfiguration`):** Now embeds a `MemoryConfiguration` instance via a `memory` field.
*   **`SemanticMemory` (`common.components.memory.SemanticMemory` - REVISED):**
    *   Its constructor now accepts `memory_config: Optional[MemoryConfiguration]`.
    *   Initialization (including loading static memories) is driven by the `memory_config` object (which defaults to `MemoryConfiguration()` if not provided).
*   **`AgentGraph` (`common.graph.AgentGraph` - REVISED):**
    *   Can automatically initialize a `SemanticMemory` instance if `agent_config.memory.use_memory` is true.
    *   The initialized `SemanticMemory` uses `self._name` (passed during `AgentGraph` instantiation) as the `agent_name` for memory namespacing, and `agent_config.memory` for its configuration (including `user_id`).
*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`).
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`, where `user_id` comes from `MemoryConfiguration.user_id`. The `agent_name` (from `AgentGraph._name`) is used by `SemanticMemory` internally, potentially for further namespacing or identification.
*   **Tools:**
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools (`manage_memory`, `search_memory`) from the `AgentGraph`-managed `SemanticMemory` instance (via `self.memory.get_tools()`).
    *   Requirement Gatherer: Uses a custom `memorize` tool.
*   **Static Memories:** JSON files in `.langgraph/static_memories/` can be loaded into the `BaseStore` under a static namespace if `memory_config.load_static_memories` is enabled in the `MemoryConfiguration` used by `SemanticMemory`.
*   **Shift:** The core principle of externalized memory remains, with `langmem` as the backend, now more seamlessly integrated via `AgentGraph` and configured through `AgentConfiguration` and `MemoryConfiguration`.


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
    *   **Local Demo Script (NEW):** `uv run --env-file .env -- python ./src/demo/orchestrate.py exec ai`
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
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default model inherited from `AgentConfiguration` if not overridden, `AgentConfiguration` defaults to `gemini-2.0-flash`).
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning.


## 4. General Agent Architecture

AI Nexus employs a few architectural patterns for its agents:

**4.1. `agent_template` based Architecture (e.g., Code Reviewer, Grumpy) - REVISED**

This pattern is now embodied by `AgentTemplateGraph` which subclasses `AgentGraph`.

*   **`configuration.py` (`src/agent_template/configuration.py` - REVISED):**
    *   `Configuration` class now subclasses `common.configuration.AgentConfiguration`.
    *   Inherits `model`, `user_id` (from `AgentConfiguration`), and `memory` (type `MemoryConfiguration`, which contains its own `memory.user_id` for namespacing) from `AgentConfiguration`.
    *   Retains its own `system_prompt` (defaulting to `prompts.SYSTEM_PROMPT`), which is used by its local `_create_call_model` helper.
    *   The `use_static_mem` field is removed (functionality now handled by `AgentConfiguration.memory.load_static_memories`).
*   **`state.py` (`src/agent_template/state.py`):** (As previously described, with `user_id`)
*   **`agent.py` (`src/agent_template/agent.py`):** DELETED. Logic is superseded by `AgentTemplateGraph` and `AgentGraph`.
*   **`graph.py` (`src/agent_template/graph.py` - REVISED):**
    *   Defines `AgentTemplateGraph(AgentGraph)`.
    *   In its `__init__`, it instantiates its `Configuration` (which is an `AgentConfiguration` subclass) if `agent_config` is not provided.
    *   It sets `agent_config.memory.use_memory = True` by default, enabling semantic memory via the parent `AgentGraph`.
    *   It sets `agent_config.system_prompt` to the template's specific system prompt (`prompts.SYSTEM_PROMPT`) if not already set.
    *   Calls `super().__init__(name="Agent Template", agent_config=this_config, ...)` to initialize the `AgentGraph`. The `AgentGraph` will then set up `SemanticMemory` using `self._name` ("Agent Template") as the `agent_name` for the memory namespace.
    *   `create_builder()`:
        *   Initializes an LLM.
        *   Retrieves tools from `self.memory.get_tools()` (provided by `AgentGraph` if memory is enabled) and potentially other tools.
        *   Binds tools to the LLM.
        *   Adds a `call_model` node (using a local helper `_create_call_model` which uses the system prompt from the `agent_config`) and a `ToolNode` (if tools exist).
        *   Sets up standard routing: `START` -> `call_model` -> (conditional) `tools` -> `call_model` or `END`.
    *   A global `graph` instance is created: `graph = AgentTemplateGraph().compiled_graph`.
*   **`tools.py` (`src/agent_template/tools.py`):** (As previously described, `file_dump` tool; memory tools are now primarily accessed via `AgentGraph`'s `memory` component).
*   **`memory.py` (`src/agent_template/memory.py`):** DELETED.
*   **`src/common/components/memory.py` (REVISED):**
    *   Defines `MemoryConfiguration` dataclass (`use_memory`, `load_static_memories`, `user_id`).
    *   `SemanticMemory` class now takes `memory_config: Optional[MemoryConfiguration]` in its constructor and uses it for initialization. The `ConfigurationProtocol` is removed.
*   **`prompts.py` (`src/agent_template/prompts.py`):** (As previously described, instruction to mention memory retrieval).

**4.2. `AgentGraph` based Architecture (REVISED - e.g., Orchestrator, Requirement Gatherer, Coder, AgentTemplateGraph)**

A common base class for modular graph definitions.

*   **`src/common/configuration.py` (NEW, replaces `src/common/config.py`):**
    ```python
    from dataclasses import dataclass, field
    from typing import Any # Added
    from common.components.memory import MemoryConfiguration

    @dataclass(kw_only=True)
    class AgentConfiguration:
        user_id: str = "default"
        model: str = "google_genai:gemini-2.0-flash"
        provider: str | None = None
        # system_prompt: Optional[str] = None # REMOVED from base AgentConfiguration
        memory: MemoryConfiguration = field(default_factory=MemoryConfiguration)
        # Agent-specific prompts or other configs are added in subclasses

        @property
        def langgraph_configurables(self) -> dict[str, Any]: # NEW property
            # ...
            pass
    ```
*   **`src/common/graph.py` (REVISED):**
    *   Defines an abstract base class `AgentGraph(ABC)`.
    *   `__init__(self, *, name: str, agent_config: AgentConfiguration, checkpointer: Optional[Checkpointer] = None, store: Optional[BaseStore] = None)`:
        *   Stores `agent_config` as `self._agent_config`.
        *   Sets `self._name = name`.
        *   If `agent_config.memory.use_memory` is true, initializes `self._memory = SemanticMemory(agent_name=self._name, store=store, memory_config=agent_config.memory)`.
    *   `agent_config` (property): Returns `self._agent_config`.
    *   `memory` (property): Returns `self._memory`.
    *   `create_builder() -> StateGraph` (abstract method): To be implemented by subclasses.
    *   `_create_call_model` base method REMOVED.
    *   `compiled_graph`: Property to get or compile the graph.
    *   `ainvoke(state, config)`: Invokes the compiled graph, merging instance config with call-time config using an updated `_merge_config` method.

Agents like Orchestrator, Requirement Gatherer, Coder, and `AgentTemplateGraph` subclass `AgentGraph`.


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`) (REVISED)
*   **Architecture:** Uses the `AgentGraph` pattern. `OrchestratorGraph` in `src/orchestrator/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/orchestrator/configuration.py` - REVISED):**
    *   `Configuration` class subclasses `common.configuration.AgentConfiguration`.
    *   Defines `SubAgentConfig` and `RequirementsAgentConfig` (which includes `use_stub: bool` and `config: requirement_gatherer.configuration.Configuration`).
    *   `Configuration` now holds fields like `requirements_agent: RequirementsAgentConfig`.
*   **Graph (`src/orchestrator/graph.py` - REVISED):**
    *   `OrchestratorGraph.__init__` now takes `agent_config: Optional[orchestrator.configuration.Configuration]`.
    *   Uses `self._agent_config` for its settings and for configuring sub-agents/stubs.
    *   `RequirementsGathererGraph` is now referred to as `RequirementsGraph`.
    *   `AgentsConfig` dataclass removed.
*   **Stubs (`src/orchestrator/stubs/__init__.py` - REVISED):**
    *   `RequirementsGathererStub.__init__` now takes `agent_config`.

#### 5.2. Architect (`src/architect/`)
*   (No changes mentioned in PR - likely still follows its previous custom structure. The `agent_template.agent.Agent` class it might have implicitly relied on for examples is now DELETED. Still uses its own `upsert_memory`.)
*   (Other details as previously described)

#### 5.3. Coder (`src/coder/`)
*   **Architecture:** Uses the `AgentGraph` pattern. Its configuration (likely `src/coder/configuration.py`, though not explicitly detailed in PR#81 diffs) would need to subclass `common.configuration.AgentConfiguration` to be compatible with the revised `AgentGraph`.

#### 5.4. Code Reviewer (`src/code_reviewer/`)
*   (Likely follows `agent_template` pattern, so it will now use `AgentTemplateGraph` and its revised memory/config handling.)

#### 5.5. Tester (`src/tester/`)
*   (No changes mentioned in PR - assumed same as previous state)

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`) (REVISED)
*   **Architecture:** Uses the `AgentGraph` pattern. `RequirementsGraph` (renamed from `RequirementsGathererGraph`) in `src/requirement_gatherer/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/requirement_gatherer/configuration.py` - REVISED):**
    *   `Configuration` class subclasses `common.configuration.AgentConfiguration`.
    *   Adds `use_human_ai: bool = False` field, used by its `human_feedback` tool.
*   **Graph (`src/requirement_gatherer/graph.py` - REVISED):**
    *   `RequirementsGraph.__init__` now takes `agent_config: Optional[requirement_gatherer.configuration.Configuration]`.
    *   Uses `self._agent_config` for its settings (e.g., `gatherer_system_prompt`, `model`).
*   **Tools (`src/requirement_gatherer/tools.py` - REVISED):**
    *   `create_human_feedback_tool` now accesses `use_human_ai` from `agent_config` (passed via `RunnableConfig`).

#### 5.7. Grumpy (`src/grumpy/`)
*   (Likely follows `agent_template` pattern, so it will now use `AgentTemplateGraph` and its revised memory/config handling.)

#### 5.8. Task Manager (`src/task_manager/`) (REVISED)
*   **Architecture:** Uses the `AgentGraph` pattern. `TaskManagerGraph` in `src/task_manager/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/task_manager/configuration.py` - REVISED):**
    *   `Configuration` class subclasses `common.configuration.AgentConfiguration`.
*   **Graph (`src/task_manager/graph.py` - REVISED):**
    *   `TaskManagerGraph.__init__` now takes `agent_config: Optional[task_manager.configuration.Configuration]`.
    *   Uses `self._agent_config` for its settings (e.g., `task_manager_system_prompt`, `model`).


## 6. Testing Framework (`tests/`)

*   **`tests/integration_tests/test_graph.py` (UPDATED):**
    *   Updated to use `AgentTemplateGraph(agent_config=config).compiled_graph` for testing the agent template's graph.
*   **`tests/integration_tests/test_requirement_gatherer.py` (UPDATED):**
    *   Updated to use `RequirementsGraph` (renamed from `RequirementsGathererGraph`).
*   **`tests/datasets/task_manager_dataset.py` (UPDATED):**
    *   Corrected a typographical error in an output message.
*   (Other test files as previously described)


## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`)

*   **README.md (UPDATED):**
    *   Expanded with new examples demonstrating semantic memory integration using the revised configuration system.
    *   Shows two ways:
        1.  Creating a custom agent by extending `AgentGraph`:
            ```python
            from common.configuration import AgentConfiguration
            # ...
            agent_config = agent_config or AgentConfiguration() # Or your custom subclass
            agent_config.memory.use_memory = True
            agent_config.memory.user_id = "user123"
            super().__init__(name="My Custom Agent", agent_config=agent_config, ...)
            ```
        2.  Enabling memory in an existing agent's configuration (e.g., for `AgentTemplateGraph`):
            ```python
            import agent_template
            # ...
            config = agent_template.Configuration() # This is already an AgentConfiguration subclass
            config.memory.use_memory = True
            config.memory.load_static_memories = True
            config.memory.user_id = "user123"
            agent = agent_template.AgentTemplateGraph(agent_config=config)
            ```
    *   **Local Demo (NEW):** Added section with command: `uv run --env-file .env -- python ./src/demo/orchestrate.py exec ai`.
*   **`.gitignore` (UPDATED):** Added `dump.json`.
*   (Other workflow details as previously described)


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/
│   └── rules/
│       └── read-project-memories.mdc
├── .env.example
├── .gitignore                    # UPDATED: Added dump.json
├── .vscode/
│   └── launch.json
├── .github/
│   └── workflows/
│       └── checks.yml
│       └── update_project_memory.yml
├── Makefile
├── README.md                     # UPDATED: Examples for semantic memory, new config, local demo
├── agent_memories/
│   └── grumpy/
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml                # UPDATED: Lint ignores for src/demo
├── scripts/
│   └── generate_project_memory.sh
│   └── update_project_memory_from_pr.sh
├── src/
│   ├── agent_template/
│   │   ├── __init__.py           # UPDATED: Exports AgentTemplateGraph, Configuration, State
│   │   ├── agent.py              # DELETED
│   │   ├── configuration.py      # UPDATED: Subclasses common.configuration.AgentConfiguration
│   │   ├── graph.py              # UPDATED: Uses AgentConfiguration, new AgentGraph init, local _create_call_model
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
│   │   ├── config.py             # DELETED (Replaced by common/configuration.py)
│   │   ├── configuration.py      # ADDED: Defines AgentConfiguration (base for all agent configs)
│   │   ├── graph.py              # REVISED: AgentGraph __init__ takes name & AgentConfiguration, inits SemanticMemory, _create_call_model removed
│   │   └── utils/
│   ├── demo/                     # NEW directory
│   │   └── orchestrate.py        # MOVED & RENAMED from src/orchestrator/test.py
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration, new sub-agent configs
│   │   ├── graph.py              # UPDATED: Uses new AgentConfiguration, new AgentGraph init, refers to RequirementsGraph
│   │   ├── memory/
│   │   │   └── team.md
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── stubs/
│   │   │   └── __init__.py       # UPDATED: Stub uses AgentConfiguration
│   │   └── tools.py
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration, adds use_human_ai
│   │   ├── graph.py              # UPDATED: Renamed to RequirementsGraph, uses AgentConfiguration, new AgentGraph init
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── tools.py              # UPDATED: human_feedback tool uses agent_config.use_human_ai
│   │   └── utils.py              # DELETED
│   ├── task_manager/
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration
│   │   └── graph.py              # UPDATED: Uses AgentConfiguration, new AgentGraph init
│   └── tester/
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py # UPDATED: Typo fix
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py
    │   ├── eval_coder.py
    │   ├── test_graph.py           # UPDATED: Uses AgentTemplateGraph(agent_config=config).compiled_graph
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py
    │   ├── test_requirement_gatherer.py # UPDATED: Uses RequirementsGraph
    │   ├── test_task_manager.py
    │   └── test_tester_agent.py
    ├── testing/
    │   ├── __init__.py
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py
```
