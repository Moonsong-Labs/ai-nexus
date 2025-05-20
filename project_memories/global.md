# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect (NEW), Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is `langmem`, providing semantic search capabilities over stored memories. `AgentGraph` can now automatically initialize and provide `SemanticMemory` and its tools to subclasses based on its configuration. The Tester agent, for instance, now includes logic to read from a `BaseStore` for contextual memories.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools provided via `AgentGraph`/`SemanticMemory`, or custom tools like `file_dump`, or agent-specific tools like the Requirement Gatherer's `memorize` and `human_feedback`, or Task Manager's file system tools, or the Architect agent's `memorize`, `recall`, `read_file`, `create_file`, `list_files` tools). The Tester agent's previous custom `upsert_memory` tool has been removed. The Architect agent's previous custom `upsert_memory` tool has been removed. The Code Reviewer agent can now use GitHub tools like `get_pull_request_diff` and `create_pull_request_review` to interact with pull requests.
5.  **System Prompts (REVISED):** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols. System prompts are now typically part of agent-specific `Configuration` classes (which subclass `AgentConfiguration` or, in the case of the Tester agent, `common.configuration.AgentConfiguration`). These configurations (and thus the prompts) are accessed by the agent's graph logic (e.g., in custom `call_model` implementations, which now often receive the agent's full `Configuration` object directly as a parameter, or access it via `RunnableConfig`). The Tester agent features enhanced prompt management with workflow stage-specific prompts and dynamic prompt formatting. The Code Reviewer agent has a specific `PR_REVIEW_PROMPT` for GitHub interactions. The Architect agent has a detailed `architect_system_prompt`.
6.  **Configuration Management (REVISED):** Agents have configurable parameters, including LLM models, system prompts, and memory settings. This is managed via:
    *   A `MemoryConfiguration` dataclass (`common.components.memory.MemoryConfiguration`) for memory-specific settings like `use_memory`, `load_static_memories`, and `user_id`.
    *   A common `AgentConfiguration` in `src/common/configuration.py` (NEW, replaces `BaseConfiguration`), which includes a `memory: MemoryConfiguration` field. It also includes `user_id`, `model`, and `provider` for LangGraph. Agent-specific system prompts are defined in subclasses.
    *   Agent-specific `Configuration` dataclasses (e.g., in `src/orchestrator/configuration.py`, `src/requirement_gatherer/configuration.py`, `src/agent_template/configuration.py`, `src/task_manager/configuration.py`, `src/architect/configuration.py` (NEW)) that subclass `AgentConfiguration` and can include their own `system_prompt` (or equivalent like `architect_system_prompt`) or other specific settings.
    *   The Tester agent's configuration (`src/tester/configuration.py`) now subclasses `common.configuration.AgentConfiguration` (aligning it with other refactored agents) and defines its `system_prompt`. Model and other common settings are inherited from `AgentConfiguration`.
    *   The Code Reviewer agent's configuration is managed via a `CodeReviewerInstanceConfig` dataclass within its `graph.py` module, which holds `name`, `system_prompt`, and `github_tools`. Its previous dedicated `configuration.py` file has been removed.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents. `SemanticMemory` (from `src/common/components/memory.py`) is configured using `MemoryConfiguration`. `AgentGraph` can instantiate `SemanticMemory` if `agent_config.memory.use_memory` is true, making memory tools available to the graph.
9.  **`AgentGraph` (REVISED):** A common base class (`src/common/graph.py`) for defining agent graphs.
    *   Its `__init__` method now takes `name: str`, `agent_config: AgentConfiguration`, `checkpointer`, and `store`.
    *   It initializes an internal `_memory: Optional[SemanticMemory]` instance if `agent_config.memory.use_memory` is true, using `agent_config.memory` for the `SemanticMemory` configuration and the passed `name` for the `agent_name` namespace.
    *   Provides an `agent_config` property to access `self._agent_config`.
    *   Provides a `memory` property to access `self._memory`.
    *   The base `_create_call_model` method has been removed; model calling logic (including system prompt handling) is now typically implemented within specific agent graph builders or helper functions (these helpers now often receive the `agent_config` directly).
    *   The `_merge_config` and `ainvoke` methods have been removed from `AgentGraph`.
    *   A new `create_runnable_config(self, config: RunnableConfig | None = None) -> RunnableConfig` method is added. It prepares the `RunnableConfig` for graph invocation by merging the agent's `langgraph_configurables` (from `self._agent_config`) with any provided call-time configurables. It does *not* inject the full `agent_config` object into the `configurable` dictionary.
    *   Graph invocation is now typically performed by getting the `compiled_graph` and calling its `ainvoke` method directly, e.g., `await agent_instance.compiled_graph.ainvoke(state, agent_instance.create_runnable_config(call_time_config))`.


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
*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`). The Tester agent's graph logic includes reading from such a store.
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`, where `user_id` comes from `MemoryConfiguration.user_id` (or equivalent `user_id` in `RunnableConfig` for agents like Tester or Architect). The `agent_name` (from `AgentGraph._name`) is used by `SemanticMemory` internally, potentially for further namespacing or identification.
*   **Tools:**
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools (`manage_memory`, `search_memory`) from the `AgentGraph`-managed `SemanticMemory` instance (via `self.memory.get_tools()`).
    *   Requirement Gatherer: Uses a custom `memorize` tool (now created by a factory function `create_memorize_tool` that receives the agent's `Configuration`, from which `user_id` is accessed for namespacing memories) and `human_feedback` tool.
    *   Tester: Its custom `upsert_memory` tool has been removed. It currently reads memories directly via `BaseStore` in its `call_model` logic.
    *   Code Reviewer: Can use GitHub tools such as `get_pull_request_diff`, `create_pull_request_review`, `get_files_from_a_directory`, and `read_file`.
    *   Architect (NEW): Uses `create_memorize_tool` and `create_recall_tool` (accessing `user_id` from its `Configuration` for namespacing) for memory operations, and file system tools (`read_file`, `create_file`, `list_files`). Its previous `upsert_memory` tool has been removed.
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
    *   **Make:** Used as a task runner to automate common commands (e.g., `deps`, `lint`, `test`, `ci-build-check` (NEW)).
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
    *   **CI Pipeline:**
        *   **`checks.yml`:** Runs linting (Ruff, codespell), unit tests (`make test_unit`), and Coder integration tests (`make test_coder`). The Coder tests job requires `GOOGLE_API_KEY` as a secret.
        *   **`compile-check.yml` (NEW):** Runs a graph compilation check (`make ci-build-check`) on pushes and PRs to `main`. This job requires `GEMINI_API_KEY` as a secret.
*   **Version Control:** Git.
*   **LLM Models:**
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default model inherited from `AgentConfiguration` if not overridden, `AgentConfiguration` defaults to `gemini-2.0-flash`). The Code Reviewer agent uses `gemini-2.0-flash`.
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning.


## 4. General Agent Architecture

AI Nexus employs a few architectural patterns for its agents:

**4.1. `agent_template` based Architecture (e.g., Grumpy) - REVISED**

This pattern is now embodied by `AgentTemplateGraph` which subclasses `AgentGraph`. (Code Reviewer no longer follows this pattern).

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
        *   Adds a `call_model` node (using a local helper `_create_call_model` which now receives `self._agent_config` as an argument and uses the system prompt from it; the inner `call_model` function no longer extracts `agent_config` from the `RunnableConfig`) and a `ToolNode` (if tools exist).
        *   Sets up standard routing: `START` -> `call_model` -> (conditional) `tools` -> `call_model` or `END`.
    *   A global `graph` instance is created: `graph = AgentTemplateGraph().compiled_graph`.
*   **`tools.py` (`src/agent_template/tools.py`):** (As previously described, `file_dump` tool; memory tools are now primarily accessed via `AgentGraph`'s `memory` component).
*   **`memory.py` (`src/agent_template/memory.py`):** DELETED.
*   **`src/common/components/memory.py` (REVISED):**
    *   Defines `MemoryConfiguration` dataclass (`use_memory`, `load_static_memories`, `user_id`).
    *   `SemanticMemory` class now takes `memory_config: Optional[MemoryConfiguration]` in its constructor and uses it for initialization. The `ConfigurationProtocol` is removed.
*   **`prompts.py` (`src/agent_template/prompts.py`):** (As previously described, instruction to mention memory retrieval).

**4.2. `AgentGraph` based Architecture (REVISED - e.g., Orchestrator, Requirement Gatherer, Coder, Task Manager, AgentTemplateGraph, Tester, Architect (NEW))**

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
    *   `_merge_config` method REMOVED.
    *   `ainvoke(state, config)`: Method REMOVED.
    *   `create_runnable_config(self, config: RunnableConfig | None = None) -> RunnableConfig` (NEW): Method to prepare `RunnableConfig` for graph invocation. It takes an optional `RunnableConfig`, merges `self._agent_config.langgraph_configurables` into its `configurable` field, and returns the modified `RunnableConfig`. This notably does *not* inject the full `agent_config` object into the `configurable` dictionary.
    *   `compiled_graph`: Property to get or compile the graph. Invocation is now typically done via `self.compiled_graph.ainvoke(state, self.create_runnable_config(config))`.

Agents like Orchestrator, Requirement Gatherer, Coder, Task Manager, `AgentTemplateGraph`, Tester, and Architect (NEW) subclass `AgentGraph`. The Tester agent has been updated to align its configuration and graph initialization more closely with this pattern (see 5.5).

**4.3. Custom `StateGraph` Architecture (e.g., Code Reviewer - NEW)**

Some agents, like the Code Reviewer, may use LangGraph's `StateGraph` directly for more specialized workflows, without necessarily subclassing `AgentGraph`.
*   Configuration is often managed via custom dataclasses (e.g., `CodeReviewerInstanceConfig` in `src/code_reviewer/graph.py`) and passed during graph construction or to specific nodes.
*   Model invocation and tool binding are handled within the custom graph definition.


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`) (REVISED)
*   **Architecture:** Uses the `AgentGraph` pattern. `OrchestratorGraph` in `src/orchestrator/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/orchestrator/configuration.py` - REVISED):**
    *   `Configuration` class subclasses `common.configuration.AgentConfiguration`.
    *   Defines `SubAgentConfig`, `RequirementsAgentConfig` (which includes `use_stub: bool` and `config: requirement_gatherer.configuration.Configuration`), and `ArchitectAgentConfig` (NEW, which includes `use_stub: bool` and `config: architect.configuration.Configuration`).
    *   `Configuration` now holds fields like `requirements_agent: RequirementsAgentConfig` and `architect_agent: ArchitectAgentConfig` (NEW).
*   **Graph (`src/orchestrator/graph.py` - REVISED):**
    *   `OrchestratorGraph.__init__` now takes `agent_config: Optional[orchestrator.configuration.Configuration]`.
    *   Uses `self._agent_config` for its settings and for configuring sub-agents/stubs.
    *   Helper functions like `_create_orchestrate`, `_create_delegate_to`, `_create_requirements_node`, and `_create_architect_node` (NEW) now receive `self._agent_config` as a direct argument.
    *   Inner functions (e.g., `orchestrate`) no longer extract `agent_config` from `RunnableConfig` but use the `agent_config` passed to their factory/creator function.
    *   `RequirementsGathererGraph` is now referred to as `RequirementsGraph`.
    *   Invocation of sub-graphs (e.g., `requirements_graph`, `architect_graph`) now uses `compiled_graph.ainvoke` (e.g., `await requirements_graph.compiled_graph.ainvoke(...)`).
    *   `_create_delegate_to` now routes to `"architect"` for the Architect agent.
    *   In `create_builder()`, an `architect_graph` (either `ArchitectStub` or `ArchitectGraph`) is instantiated and an `architect` node is added to the graph.
    *   `AgentsConfig` dataclass removed.
*   **Stubs (`src/orchestrator/stubs/__init__.py` - REVISED):**
    *   `RequirementsGathererStub` (subclasses `AgentGraph`):
        *   `__init__` now takes `agent_config` and explicitly passes `name="Requirements Gatherer Stub"` to `super().__init__`.
        *   `create_builder()` method now returns a simple `StateGraph` (using `requirement_gatherer.state.State as RequirementsState`) with a single "run" node that provides the stubbed summary. This allows the stub to have a `compiled_graph`.
        *   The custom `ainvoke` method has been removed (its logic is now within the graph created by `create_builder`).
    *   `ArchitectStub` (NEW, subclasses `StubGraph[ArchitectState]`): Provides stubbed responses for the Architect agent.
    *   Old `architect` stub function removed.

#### 5.2. Architect (`src/architect/`) (REWORKED)
*   **Architecture:** Uses the `AgentGraph` pattern. `ArchitectGraph` in `src/architect/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/architect/configuration.py` - REVISED):**
    *   `Configuration` class subclasses `common.configuration.AgentConfiguration`.
    *   Defines `architect_system_prompt: str` (defaulting to `prompts.SYSTEM_PROMPT`).
    *   Defines `use_human_ai: bool = False`.
    *   Inherits `model`, `user_id`, `memory` from `AgentConfiguration`.
    *   Previous specific `user_id`, `model`, `system_prompt` fields are removed (now inherited or replaced by `architect_system_prompt`).
    *   The `from_runnable_config` method has been removed.
*   **State (`src/architect/state.py`):** Defines `State` for the Architect agent's graph (used by `ArchitectGraph`).
*   **Graph (`src/architect/graph.py` - REVISED):**
    *   Defines `ArchitectGraph(AgentGraph)`.
    *   `__init__` takes `agent_config: Optional[architect.configuration.Configuration]`. It calls `super().__init__(name="Architect", agent_config=agent_config or architect.configuration.Configuration(), ...)`.
    *   `create_builder()`:
        *   Initializes an LLM using `self._agent_config.model`.
        *   Tools: `create_memorize_tool(self._agent_config)`, `create_recall_tool(self._agent_config)`, `read_file`, `create_file`, `list_files`.
        *   Binds these tools to the LLM.
        *   A helper function `_create_call_model(agent_config: Configuration, llm_with_tools)` is defined.
            *   Its inner `call_model(state: State, config: RunnableConfig, store: BaseStore)` function:
                *   Retrieves `user_id` from `config["configurable"]["user_id"]`.
                *   Searches memories from `store` using this `user_id`.
                *   Formats the `agent_config.architect_system_prompt` with `user_info` (formatted memories) and current `time`.
                *   Invokes the `llm_with_tools` with the system prompt and current messages.
        *   Sets up graph nodes: `call_model` (using the helper) and a `ToolNode` (named "tools").
        *   Defines graph flow: `START` -> `call_model`. Then, based on `tools_condition` (checks for tool calls in the last message), it routes to `tools` (if tool calls exist), back to `call_model`, or to `END`.
    *   A global `graph` instance is created for LangSmith: `graph = ArchitectGraph().compiled_graph`.
*   **Prompts (`src/architect/prompts.py` - REVISED):**
    *   `SYSTEM_PROMPT` (which `Configuration.architect_system_prompt` defaults to) is a new, detailed prompt. It defines the Architect's role (expert software engineer for project architecture, not coding), core values (Research Driven, Technology Selection, Task Definition, Validation and Adjustment, Transparency and Traceability, Focus and Clearness), understanding of requirements documentation structure (Mermaid diagram), project documentation structure (Mermaid diagram, core files: `projectbrief.md`, `systemPatterns.md`, `techPatterns.md`, `progress.md`; specific files: `codingContext.md`, `testingContext.md`), and a detailed workflow (1. Read Requirements Documentation, 2. Read Existing Project Documentation, 3. Read Project Files, 4. Write Documentation, 5. Persist with Memory, 6. Completion Gate, 7. Finalize). Includes `{user_info}` and `{time}` placeholders.
*   **Tools (`src/architect/tools.py` - REVISED):**
    *   The previous `upsert_memory` tool has been removed.
    *   `create_memorize_tool(agent_config: Configuration)`: A factory function that creates a `memorize` tool. The inner tool uses `agent_config.user_id` for namespacing memories and `store.aput` for storage.
    *   `create_recall_tool(agent_config: Configuration)`: A factory function that creates a `recall` tool. The inner tool uses `agent_config.user_id` for namespacing and `store.asearch` for retrieval.
    *   `read_file(file_path: str)`: New tool to read the content of a file.
    *   `create_file(file_path: str, content: str)`: New tool to create a file with specified content, including parent directories.
    *   `list_files(directory_path: str = ".")`: New tool to list files and directories in a specified path, with details like size.

#### 5.3. Coder (`src/coder/`)
*   **Architecture:** Uses the `AgentGraph` pattern. Its configuration (likely `src/coder/configuration.py`, though not explicitly detailed in PR#81 diffs) would need to subclass `common.configuration.AgentConfiguration` to be compatible with the revised `AgentGraph`.

#### 5.4. Code Reviewer (`src/code_reviewer/`) (REVISED)
*   **Architecture:** Uses a custom `StateGraph` implementation (from `langgraph.graph`). It does not subclass `AgentGraph` or `AgentTemplateGraph`.
*   **Configuration (`src/code_reviewer/configuration.py` - DELETED):** The dedicated configuration file has been removed.
    *   Configuration parameters like system prompt and tool selection are managed by the `CodeReviewerInstanceConfig` dataclass defined in `src/code_reviewer/graph.py`.
    *   Two configurations are provided: `non_github_code_reviewer_config()` and `github_code_reviewer_config()`.
*   **State (`src/code_reviewer/state.py`):** Defines the `State` for the graph, including `messages` and `diff_feedback` (though `diff_feedback` is no longer directly populated by the model call in the graph).
*   **Graph (`src/code_reviewer/graph.py` - REVISED):**
    *   Defines `CodeReviewerInstanceConfig` dataclass to hold `name`, `system_prompt`, and `github_tools`.
    *   The `graph_builder(github_toolset: list[Tool], system_prompt: str) -> StateGraph` function constructs the agent's graph using `StateGraph(State)`.
    *   The `CodeReviewerModel` class handles LLM calls. Its `__call__` method now binds tools and invokes the LLM, returning the raw LLM response (including potential tool calls) in the `messages` field of the state. The structured `DiffFeedback` output from the model call itself has been removed.
    *   The LLM is initialized with `gemini-2.0-flash`.
*   **Server Entry Points (`src/code_reviewer/lg_server.py` - REVISED):**
    *   Provides two compiled graph instances:
        *   `graph_with_github_tools`: Uses `github_code_reviewer_config()` which includes GitHub interaction tools and the `PR_REVIEW_PROMPT`.
        *   `graph_no_github_tools`: Uses `non_github_code_reviewer_config()` with a standard system prompt and no GitHub tools.
*   **Prompts (`src/code_reviewer/prompts.py` - REVISED):**
    *   `SYSTEM_PROMPT`: Standard system prompt.
    *   `PR_REVIEW_PROMPT` (NEW): A specific prompt for reviewing GitHub pull requests, instructing the agent to use GitHub tools to fetch PR details, read files, analyze the diff, and provide feedback directly on the PR.
*   **Tools (REVISED):**
    *   When configured for GitHub interaction, it uses tools from `common.components.github_tools` such as:
        *   `get_files_from_a_directory`
        *   `read_file`
        *   `get_pull_request`
        *   `get_pull_request_diff` (NEW)
        *   `create_pull_request_review` (NEW) - This tool allows commenting on PRs, requesting changes, or approving. It uses `PRReviewComment` and `CreatePRReview` Pydantic models for its arguments.

#### 5.5. Tester (`src/tester/`) (REWORKED)
*   **Overall:** The Tester agent has been significantly reworked to streamline its workflow, improve prompt management, and refine configuration and state.
*   **Architecture:** Uses the `AgentGraph` pattern. `TesterAgentGraph` in `src/tester/graph.py` subclasses `common.graph.AgentGraph`.
*   **Documentation:**
    *   `src/tester/README.md` has been deleted.
    *   Old prompt examples (`src/tester/test-prompts/`) have been deleted.
    *   Some older prompt files have been moved to `src/tester/deprecated/`.
    *   New documentation outlining the Test Agent's role, workflow, and requirements for generating tests is primarily in its system prompt.
*   **Configuration (`src/tester/configuration.py` - REVISED):**
    *   `Configuration` class now subclasses `common.configuration.AgentConfiguration`.
    *   It defines a `system_prompt` (defaulting to `prompts.SYSTEM_PROMPT`). Model and other common settings are inherited from `AgentConfiguration`.
    *   The `from_runnable_config` method has been removed.
*   **State (`src/tester/state.py` - REVISED):**
    *   `WorkflowStage` enum updated to: `ANALYZE_REQUIREMENTS`, `TESTING`, `COMPLETE`.
    *   The `State` class now includes `workflow_stage: WorkflowStage`, which defaults to `WorkflowStage.TESTING`.
*   **Graph (`src/tester/graph.py` - REVISED):**
    *   Defines `TesterAgentGraph(AgentGraph)`.
    *   `__init__(self, *, agent_config: Optional[tester.configuration.Configuration] = None, checkpointer: Optional[Checkpointer] = None, store: Optional[BaseStore] = None)`:
        *   Calls `super().__init__(name="tester", agent_config=agent_config or tester.configuration.Configuration(), checkpointer=checkpointer, store=store)`. This aligns its initialization with the `AgentGraph` base class, which sets `self._agent_config`.
        *   It now uses `self._agent_config` (an instance of `tester.configuration.Configuration`, set by the `AgentGraph` superclass) for its settings (e.g., `self._agent_config.model`). The local `self._config` attribute and `self._use_human_ai` attribute (previously set in `__init__`) are removed.
    *   `create_builder()`:
        *   Initializes an LLM using `self._agent_config.model`.
        *   Tools are currently not bound to the LLM (`all_tools = []`).
        *   Sets up graph nodes: `call_model` (for LLM interaction) and `tools` (a `ToolNode`, though no tools are currently provided).
        *   Defines graph flow: `START` -> `call_model`. Then, based on `_create_workflow`'s logic (which checks for tool calls in the last message), it routes to `tools` (if tool calls exist), back to `call_model`, or to `END`.
    *   `_create_call_model(llm_with_tools)` helper function:
        *   Its inner `call_model(state: State, config: RunnableConfig, store: Optional[BaseStore])` function:
            *   If `store` is provided, attempts to retrieve memories using `store.asearch` with `user_id` from `config["configurable"]["user_id"]`.
            *   Retrieves a stage-specific prompt using `prompts.get_stage_prompt(state.workflow_stage.value)`.
            *   Formats the main `system_prompt` (from `config["configurable"]["system_prompt"]`) using the stage prompt, retrieved memories (`user_info`), and current `time`.
            *   Invokes the LLM.
            *   Determines the `next_stage` for the workflow (e.g., transitions to `WorkflowStage.COMPLETE` if the LLM response contains "tests are complete").
    *   A global `graph` instance is created for LangSmith: `graph = TesterAgentGraph().compiled_graph` (this will instantiate `TesterAgentGraph` with a default `tester.configuration.Configuration()`).
*   **Prompts (`src/tester/prompts.py`, `src/tester/test-agent-system-prompt.md`, `src/tester/test-agent-testing-workflow-stage.md` - REVISED/NEW):**
    *   The main system prompt (`test-agent-system-prompt.md`) has been updated to focus on requirements for generating complete, executable test files, test structure, and overall completeness.
    *   `src/tester/prompts.py`:
        *   Loads the main system prompt and workflow stage-specific prompts (e.g., `test-agent-testing-workflow-stage.md` for the "testing" stage).
        *   The `SYSTEM_PROMPT` string template is formatted with placeholders: `{workflow_stage}`, `{user_info}` (for memories), and `{time}`.
        *   A `get_stage_prompt(stage_name)` function is introduced to provide specific instructions for the current workflow stage.
        *   Error handling for missing or empty prompt files has been improved.
*   **Tools (`src/tester/tools.py`):** DELETED. The previous `upsert_memory` tool has been removed. The agent currently does not have any custom tools bound in its graph.
*   **Output (`src/tester/output.py`):** DELETED. The agent's output is now directly the LLM messages within the `State`.

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`) (REVISED)
*   **Architecture:** Uses the `AgentGraph` pattern. `RequirementsGraph` (renamed from `RequirementsGathererGraph`) in `src/requirement_gatherer/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/requirement_gatherer/configuration.py` - REVISED):**
    *   `Configuration` class subclasses `common.configuration.AgentConfiguration`.
    *   Adds `use_human_ai: bool = False` field, used by its `human_feedback` tool.
*   **Graph (`src/requirement_gatherer/graph.py` - REVISED):**
    *   `RequirementsGraph.__init__` now takes `agent_config: Optional[requirement_gatherer.configuration.Configuration]`.
    *   Uses `self._agent_config` for its settings (e.g., `gatherer_system_prompt`, `model`).
    *   Helper functions like `_create_call_model` and `_create_gather_requirements` now receive `self._agent_config` as a direct argument.
    *   Inner functions (e.g., `call_model`) no longer extract `agent_config` from `RunnableConfig` but use the `agent_config` passed to their factory/creator function.
    *   In `create_builder()`, the `memorize` tool is now instantiated via `tools.create_memorize_tool(self._agent_config)`.
*   **Tools (`src/requirement_gatherer/tools.py` - REVISED):**
    *   `create_human_feedback_tool` now accepts the full `agent_config: requirement_gatherer.configuration.Configuration` object as an argument (instead of just `use_human_ai`).
    *   The inner `human_feedback` tool function no longer extracts `agent_config` from `RunnableConfig` but uses the `agent_config.use_human_ai` field from the configuration object passed to `create_human_feedback_tool`.
    *   The standalone `memorize` tool function has been replaced by a factory function `create_memorize_tool(agent_config: requirement_gatherer.configuration.Configuration)`.
    *   The inner `memorize` tool, created by this factory, now accesses `user_id` directly from the `agent_config.user_id` (provided via the factory) for namespacing memories, instead of attempting to extract configuration from `RunnableConfig`.

#### 5.7. Grumpy (`src/grumpy/`)
*   (Likely follows `agent_template` pattern, so it will now use `AgentTemplateGraph` and its revised memory/config handling, including how `agent_config` is passed to its internal `_create_call_model` helper.)

#### 5.8. Task Manager (`src/task_manager/`) (REVISED)
*   **Architecture:** Uses the `AgentGraph` pattern. `TaskManagerGraph` in `src/task_manager/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/task_manager/configuration.py` - REVISED):**
    *   `Configuration` class subclasses `common.configuration.AgentConfiguration`.
    *   Its `task_manager_system_prompt` (defined in `prompts.py`) is used by the agent.
*   **Graph (`src/task_manager/graph.py` - REVISED):**
    *   `TaskManagerGraph.__init__` now takes `agent_config: Optional[task_manager.configuration.Configuration]`.
    *   Uses `self._agent_config` for its settings (e.g., `task_manager_system_prompt`, `model`).
    *   The helper function `_create_call_model` now receives `self._agent_config` as a direct argument.
    *   The inner `call_model` function no longer extracts `agent_config` from `RunnableConfig` but uses the `agent_config` passed to `_create_call_model`. The system prompt it formats now includes a `project_context` placeholder (e.g., `agent_config.task_manager_system_prompt.format(..., project_context="")`).
*   **Prompts (`src/task_manager/prompts.py` - REVISED):**
    *   The `SYSTEM_PROMPT` now includes a `{project_context}` placeholder.
    *   User input is now expected to be a `project_name` and the complete `path to the project`.
    *   Project directory validation and file operations (e.g., checking for required files, creating task files, creating `roadmap.md`) are performed relative to the user-provided project path, not a fixed "volume" or "planning" directory.
    *   Task files are to be created in `[provided_project_path]/planning/task-##-short-title.md`.
    *   `roadmap.md` is to be created in `[provided_project_path]/planning/roadmap.md`.
    *   Validation error messages now include the specific path if a directory is not found.
*   **Tools (`src/task_manager/tools.py` - REVISED):**
    *   The `get_volume_path` helper function has been removed.
    *   `read_file(file_path: str)`: Reads a file from the given `file_path`. No longer restricted to a "volume" directory.
    *   `create_file(file_path: str, content: str)`: Creates a file at the specified `file_path` with the given `content`. Parent directories are created if they don't exist. No longer uses `subfolder` or restricted to a "volume" directory.
    *   `list_files(directory_path: str = ".")`: Lists files in the given `directory_path`. No longer restricted to a "volume" directory.
*   **File System Interaction (REVISED):** The agent now operates on file paths provided by the user, allowing it to work in any user-specified directory. It no longer uses a hardcoded `src/task_manager/volume/` directory for its operations or example data.


## 6. Testing Framework (`tests/`)

*   **`tests/integration_tests/test_graph.py` (UPDATED):**
    *   Updated to use `AgentTemplateGraph(agent_config=config).compiled_graph` for testing the agent template's graph.
*   **`tests/integration_tests/test_requirement_gatherer.py` (UPDATED):**
    *   Updated to use `RequirementsGraph` (renamed from `RequirementsGathererGraph`).
    *   The graph instance for LangSmith evaluation is now obtained via `RequirementsGraph(...).compiled_graph`.
*   **`tests/integration_tests/test_orchestrator.py` (UPDATED):**
    *   Updated to use `OrchestratorGraph().compiled_graph` for testing the orchestrator's graph.
*   **`tests/integration_tests/test_task_manager.py` (UPDATED):**
    *   A new test `test_task_manager_with_project_path` is added to verify the agent's ability to work with user-specified project paths, checking for the creation of a `planning` folder and `roadmap.md` within that path, and the generation of multiple task files.
    *   The `call_model` mock/helper within `test_task_manager_langsmith` now includes `task_manager_system_prompt: prompts.SYSTEM_PROMPT` in its configuration, ensuring the test uses the updated system prompt, and correctly uses `graph.compiled_graph.ainvoke` for graph invocation.
    *   Example files for testing (e.g., `api_rust` project files) are now located in `tests/integration_tests/inputs/api_rust/` (moved from `src/task_manager/volume/api_rust/`).
*   **`tests/integration_tests/test_tester_agent.py` (UPDATED):**
    *   Updated to use the new `TesterAgentGraph` instantiation method, e.g., `graph_compiled = TesterAgentGraph(checkpointer=MemorySaver()).compiled_graph` (now directly uses the compiled graph).
*   **`tests/datasets/task_manager_dataset.py` (UPDATED):**
    *   Corrected a typographical error in an output message.
*   **`tests/testing/__init__.py` (UPDATED):**
    *   The `create_async_graph_caller` utility function (used for LangSmith evaluations) has been simplified. It now directly passes the `inputs` dictionary to `graph.ainvoke` as the state and expects the graph's result to be a dictionary containing a "messages" list, from which it extracts the content of the last message.
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
    *   **Local Demo (NEW & UPDATED):** Added section with command: `uv run --env-file .env -- python ./src/demo/orchestrate.py exec ai`. The `orchestrate.py` script now uses `orchestrator.create_runnable_config()` and `orchestrator.compiled_graph.ainvoke()` for execution.
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
│       ├── checks.yml
│       ├── compile-check.yml     # ADDED
│       └── update_project_memory.yml
├── Makefile                      # UPDATED: Added ci-build-check target
├── README.md                     # UPDATED: Examples for semantic memory, new config, local demo
├── agent_memories/
│   └── grumpy/
├── langgraph.json                # UPDATED: New Code Reviewer graph entry points, Architect graph entry point
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
│   │   ├── graph.py              # UPDATED: Uses AgentConfiguration, new AgentGraph init, local _create_call_model receives agent_config
│   │   ├── memory.py             # DELETED
│   │   ├── prompts.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── architect/                # REWORKED
│   │   ├── __init__.py           # (Assumed to export ArchitectGraph, Configuration, State)
│   │   ├── configuration.py      # UPDATED: Subclasses common.configuration.AgentConfiguration, defines architect_system_prompt
│   │   ├── graph.py              # UPDATED: Implements ArchitectGraph(AgentGraph), new tool usage, memory/prompt handling
│   │   ├── prompts.py            # UPDATED: New detailed SYSTEM_PROMPT for Architect
│   │   ├── prompts/
│   │   │   ├── v0.1.md           # DELETED
│   │   │   └── v0.md             # DELETED
│   │   ├── state.py              # (Assumed to exist, defines State for ArchitectGraph)
│   │   └── tools.py              # UPDATED: New memorize, recall, read_file, create_file, list_files tools; upsert_memory removed
│   ├── code_reviewer/            # REVISED
│   │   ├── __init__.py           # UPDATED: Exports graph_no_github_tools, graph_with_github_tools
│   │   ├── configuration.py      # DELETED
│   │   ├── graph.py              # UPDATED: Uses StateGraph directly, CodeReviewerInstanceConfig, CodeReviewerModel, new GitHub tool integration logic
│   │   ├── lg_server.py          # UPDATED: Defines graph_with_github_tools and graph_no_github_tools
│   │   ├── prompts.py            # UPDATED: Added PR_REVIEW_PROMPT
│   │   ├── state.py
│   │   └── system_prompt.md      # (Content likely reflected in prompts.py constants)
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
│   │   │   ├── github_mocks.py   # UPDATED: Added stubs for get_pull_request_diff, create_pull_request_review
│   │   │   ├── github_tools.py   # UPDATED: Added GetPullRequestDiff, CreatePullRequestReviewComment tools, PRReviewComment, CreatePRReview schemas
│   │   │   └── memory.py         # UPDATED: Defines MemoryConfiguration, SemanticMemory uses it, ConfigurationProtocol removed
│   │   ├── config.py             # DELETED (Replaced by common/configuration.py) - Note: Tester agent's configuration.py refers to this path.
│   │   ├── configuration.py      # ADDED: Defines AgentConfiguration (base for all agent configs)
│   │   ├── graph.py              # REVISED: AgentGraph __init__ takes name & AgentConfiguration, inits SemanticMemory, _create_call_model, _merge_config, ainvoke removed; create_runnable_config added
│   │   └── utils/
│   ├── demo/                     # NEW directory
│   │   └── orchestrate.py        # MOVED & RENAMED from src/orchestrator/test.py; UPDATED to use create_runnable_config and compiled_graph.ainvoke, includes Architect agent config
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration, new sub-agent configs (ArchitectAgentConfig)
│   │   ├── graph.py              # UPDATED: Uses new AgentConfiguration, new AgentGraph init, refers to RequirementsGraph, ArchitectGraph; helpers receive agent_config; sub-graph invocation via compiled_graph.ainvoke; integrates Architect agent/stub
│   │   ├── memory/
│   │   │   └── team.md
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── stubs/
│   │   │   └── __init__.py       # UPDATED: Stub uses AgentConfiguration, RequirementsGathererStub now builds a simple graph, ArchitectStub added, old architect stub function removed
│   │   └── tools.py
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration, adds use_human_ai
│   │   ├── graph.py              # UPDATED: Renamed to RequirementsGraph, uses AgentConfiguration, new AgentGraph init; helpers receive agent_config; memorize tool now created via create_memorize_tool(self._agent_config)
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── tools.py              # UPDATED: human_feedback tool factory takes agent_config; memorize tool now created by create_memorize_tool factory that takes agent_config for user_id
│   │   └── utils.py              # DELETED
│   ├── task_manager/
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration
│   │   ├── graph.py              # UPDATED: Uses AgentConfiguration, new AgentGraph init; _create_call_model helper receives agent_config; system prompt formatting includes project_context
│   │   ├── prompts.py            # UPDATED: System prompt expects project_name and path, includes {project_context} placeholder, file operations relative to provided path
│   │   ├── tools.py              # UPDATED: File tools (read_file, create_file, list_files) operate on direct paths, get_volume_path removed
│   │   └── volume/               # DELETED (Contents moved to tests/integration_tests/inputs/)
│   └── tester/                   # REWORKED
│       ├── __init__.py           # (Assumed to exist, exports TesterAgentGraph)
│       ├── README.md             # DELETED
│       ├── configuration.py      # UPDATED: Subclasses common.configuration.AgentConfiguration
│       ├── deprecated/           # NEW directory
│       │   ├── deprecated-test-agent-system-prompt.md                # NEW
│       │   └── test-agent-analyze-requirements-workflow-stage.md     # NEW
│       ├── graph.py              # UPDATED: Implements TesterAgentGraph(AgentGraph), __init__ signature changed to use agent_config (tester.configuration.Configuration), calls super with name and agent_config, uses self._agent_config for settings, new workflow, memory reading
│       ├── output.py             # DELETED
│       ├── prompts.py            # UPDATED: Loads new prompts, get_stage_prompt function
│       ├── state.py              # UPDATED: New WorkflowStage enum, State includes workflow_stage
│       ├── test-agent-system-prompt.md           # UPDATED content
│       ├── test-agent-testing-workflow-stage.md  # NEW file
│       ├── test-prompts/         # DELETED directory
│       └── tools.py              # DELETED
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
    │   ├── test_orchestrator.py    # UPDATED: Uses OrchestratorGraph().compiled_graph
    │   ├── test_requirement_gatherer.py # UPDATED: Uses RequirementsGraph; graph instance for LangSmith eval now .compiled_graph
    │   ├── test_task_manager.py    # UPDATED: New test for project path, config includes task_manager_system_prompt, call_model helper uses graph.compiled_graph.ainvoke
    │   ├── test_tester_agent.py    # UPDATED: Uses TesterAgentGraph(...).compiled_graph for tests
    │   └── inputs/                 # NEW directory
    │       └── api_rust/           # NEW directory (Contains files moved from src/task_manager/volume/api_rust)
    │           ├── featuresContext.md
    │           ├── progress.md
    │           ├── projectRequirements.md
    │           ├── projectbrief.md
    │           ├── securityContext.md
    │           ├── systemPatterns.md
    │           ├── techContext.md
    │           └── testingContext.md
    ├── testing/
    │   ├── __init__.py             # UPDATED: create_async_graph_caller simplified
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py
```
