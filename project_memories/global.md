# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is now `langmem`, providing semantic search capabilities over stored memories, replacing the previous conceptual Markdown-based "Memory Bank" and direct `upsert_memory` tool usage for agents based on the template. `SemanticMemory` is configured via `MemoryConfiguration` (part of `BaseConfiguration`).
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools or custom tools like `file_dump`, or agent-specific tools like the Requirement Gatherer's `memorize` and `human_feedback`).
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols.
6.  **Configuration Management:** Agents have configurable parameters, including LLM models, system prompts, and memory settings. This is managed via:
    *   `Configuration` dataclasses from `agent_template`.
    *   A common `BaseConfiguration` in `src/common/config.py`. `BaseConfiguration` now includes `system_prompt: Optional[str]` and `memory: MemoryConfiguration` (a new dataclass defining memory behavior like `use_memory`, `load_static_memories`, `user_id`).
    *   Agent-specific `Configuration` dataclasses (e.g., in `src/orchestrator/configuration.py`, `src/requirement_gatherer/configuration.py`) that subclass `BaseConfiguration`.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents. The `SemanticMemory` component (from `src/common/components/memory.py`) is now configured using `MemoryConfiguration` (nested in `BaseConfiguration`) instead of direct config attributes like `use_static_mem`.
9.  **`AgentGraph` (NEW):** A common base class (`src/common/graph.py`) for defining agent graphs, promoting modularity. Used by Orchestrator and Requirement Gatherer. Its `__init__` method now takes `base_config: BaseConfiguration` and also initializes an internal `SemanticMemory` instance (accessible via a `memory` property) if `base_config.memory.use_memory` is true. It also has a new `_create_call_model` base method for LLM invocation.


## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence, particularly for the "Cursor" idea. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and custom tools):** The project has integrated the `langmem` library to provide a more robust and queryable semantic memory system.
*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`). `SemanticMemory` initialization and static memory loading are now driven by `MemoryConfiguration` (e.g., `memory_config.use_memory`, `memory_config.load_static_memories`). This `MemoryConfiguration` is typically part of an agent's main `Configuration` (which subclasses `BaseConfiguration`).
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`. The `user_id` for namespacing is sourced from `MemoryConfiguration`.
*   **Tools:**
    *   `agent_template` based agents (now using `AgentTemplateGraph`): Use `langmem`-provided tools (`manage_memory`, `search_memory`) via the `SemanticMemory` instance initialized within `AgentGraph` if memory is enabled. A custom `memory_dump` tool is also available.
    *   Requirement Gatherer: Uses a custom `memorize` tool (defined in `src/requirement_gatherer/tools.py`) for storing memories.
*   **Static Memories:** The concept of static, pre-loaded knowledge persists. JSON files in `.langgraph/static_memories/` can be loaded into the `BaseStore` under a static namespace if `load_static_memories` is enabled in the agent's `MemoryConfiguration`. The previous `use_static_mem` boolean directly in agent configurations is replaced by this nested structure.
*   **Shift:** The shift moves from human-readable Markdown files as the primary memory source to a database/store queried semantically via tools. The core principle of externalized memory remains, but the implementation mechanism has evolved. The specific file structure (`projectbrief.md`, `productContext.md`, etc.) described previously is not directly implemented by the `langmem` system, although the *types* of information they represent might be stored as individual memories.


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
    *   **CI Pipeline (`.github/workflows/checks.yml`):** Runs linting (Ruff, codespell), unit tests (`make test_unit`), and Coder integration tests (`make test_coder`). The Coder tests job requires `GOOGLE_API_KEY` as a secret.
*   **Version Control:** Git.
*   **LLM Models:**
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default updated to `gemini-2.5-flash-preview-04-17` via `BaseConfiguration`). Orchestrator and Requirement Gatherer default to `google_genai:gemini-2.0-flash` via `BaseConfiguration`.
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning.


## 4. General Agent Architecture

AI Nexus employs a few architectural patterns for its agents:

**4.1. `agent_template` based Architecture (e.g., Code Reviewer, Grumpy)**

This architecture has been significantly refactored. It no longer uses a standalone `Agent` class. Instead, it's based on `AgentTemplateGraph` (`src/agent_template/graph.py`) which subclasses `AgentGraph`.

*   **Typical Agent Directory Structure:** (As previously described, but `agent.py` is GONE from `src/agent_template/`)
*   **`configuration.py` (`src/agent_template/configuration.py`):**
    *   Now subclasses `common.config.BaseConfiguration`.
    *   Fields like `user_id`, `model` are inherited from `BaseConfiguration`.
    *   Memory-specific settings are now managed via `BaseConfiguration.memory` (an instance of `MemoryConfiguration`). The `agent_template.Configuration` sets `config.memory.use_memory = True` by default.
    *   Retains `system_prompt` (defaulting to `prompts.SYSTEM_PROMPT`).
*   **`state.py` (Typical Structure - `src/agent_template/state.py`):** (As previously described, with `user_id`)
*   **`agent.py` (`src/agent_template/agent.py`):** **DELETED**. Logic is now part of `AgentTemplateGraph` and `AgentGraph`.
*   **`graph.py` (Core Logic - `src/agent_template/graph.py`):**
    *   Defines `AgentTemplateGraph(AgentGraph)`.
    *   `__init__` configures its `Configuration` (subclassing `BaseConfiguration`), enabling memory by default (`config.memory.use_memory = True`) and setting its system prompt.
    *   `create_builder` method initializes the LLM, retrieves tools from its internal `_memory` component (if memory is enabled via `AgentGraph`), binds tools to the LLM, and constructs the graph with `call_model` and `ToolNode`.
    *   The `call_model` node uses the `_create_call_model` method (can be from `AgentGraph` or overridden).
    *   The old `graph_builder` function is removed.
    *   A default `graph` instance is exported, compiled from `AgentTemplateGraph()`.
*   **`tools.py` (Utility Tools - `src/agent_template/tools.py`):** `file_dump` tool remains. Memory tools (`manage_memory`, `search_memory`) are now provided by the `SemanticMemory` instance within `AgentTemplateGraph` (initialized by `AgentGraph` if memory is enabled).
*   **`memory.py` (`src/agent_template/memory.py`):** DELETED.
*   **`src/common/components/memory.py` (NEW):**
    *   `SemanticMemory` class now takes `memory_config: MemoryConfiguration` for its settings.
    *   A new `MemoryConfiguration` dataclass is defined here (`use_memory`, `load_static_memories`, `user_id`).
    *   `ConfigurationProtocol` is removed.
    *   Static memory loading logic updated to use `MemoryConfiguration`.
    *   `langmem` tool creation (`get_tools`) remains.
*   **`prompts.py` (`src/agent_template/prompts.py`):** (As previously described, instruction to mention memory retrieval)

**4.2. `AgentGraph` based Architecture (NEW - e.g., Orchestrator, Requirement Gatherer)**

A newer pattern utilizes a common base class for more modular graph definitions.

*   **`src/common/config.py` (NEW):**
    ```python
    from dataclasses import dataclass, field
    from common.components.memory import MemoryConfiguration # ADDED

    @dataclass(kw_only=True)
    class BaseConfiguration:
        user_id: str = "default" # Note: user_id also in MemoryConfiguration for memory namespacing
        model: str = "google_genai:gemini-2.0-flash"
        provider: str | None = None
        system_prompt: Optional[str] = None # ADDED
        memory: MemoryConfiguration = field(default_factory=MemoryConfiguration) # ADDED
        # Agent-specific prompts or other configs are added in subclasses
        # from_runnable_config method ADDED
    ```
*   **`src/common/graph.py` (NEW):**
    *   Defines an abstract base class `AgentGraph(ABC)`.
    *   `__init__(base_config: BaseConfiguration, checkpointer, store)`:
        *   Initializes with common config.
        *   Now also initializes an internal `SemanticMemory` instance (accessible via a `self.memory` property) if `base_config.memory.use_memory` is true. The `store` passed to `__init__` is used for this `SemanticMemory` instance.
    *   `create_builder() -> StateGraph` (abstract method): To be implemented by subclasses to define the graph.
    *   `_create_call_model(self, llm)` (NEW method): Provides a basic node function for invoking the LLM with messages from state and the `system_prompt` from `base_config`. This can be overridden by subclasses.
    *   `compiled_graph`: Property to get or compile the graph.
    *   `ainvoke(state, config)`: Invokes the compiled graph, merging instance config with call-time config.

Agents like Orchestrator and Requirement Gatherer now subclass `AgentGraph` and define their specific `Configuration` (subclassing `common.config.BaseConfiguration` in their respective new `configuration.py` files) and graph structure. Graph construction is more modular, often using factory functions to create nodes and tools.


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`)
*   **Architecture:** Uses the `AgentGraph` pattern. `OrchestratorGraph` in `src/orchestrator/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/orchestrator/configuration.py` - NEW FILE, REPLACING INLINE CONFIG):**
    *   Defines its own `Configuration` dataclass in `src/orchestrator/configuration.py`, subclassing `common.config.BaseConfiguration`. (Impacted by `BaseConfiguration` changes, e.g., `memory` field).
    *   `system_prompt: str = prompts.get_prompt()` (which now formats current `time` into the prompt).
    *   **`src/orchestrator/graph.py` now defines `AgentsConfig` dataclass** to manage agent stubs (e.g., `requirements.use_stub`) and agent-specific features (e.g., `requirements.use_human_ai`).
*   **Graph Logic (`src/orchestrator/graph.py`):**
    *   The `orchestrate` node (created by `_create_orchestrate` factory) uses the system prompt from the config (including current time). LLM is initialized within `create_builder`.
    *   The `delegate_to` routing function (created by `_create_delegate_to` factory) is updated.
    *   Integrates other agent graphs/stubs; for example, it can instantiate and use `RequirementsGathererGraph` (or `RequirementsGathererStub`) based on `AgentsConfig`. The `requirements` node is created by `_create_requirements_node` factory.
*   **Prompts (`src/orchestrator/prompts.py`):**
    *   `ORCHESTRATOR_SYSTEM_PROMPT` (and the one constructed by `get_prompt()`) now includes a `{time}` placeholder, formatted with the current time during graph execution.
    *   `src/orchestrator/memory/team.md`: Updated to specify that the `Delegate` tool usage MUST include the `content` field for the delegated task.
*   **Tools (`src/orchestrator/tools.py`):**
    *   The `Delegate` tool's Pydantic model now includes a mandatory `content: str` field.
    *   The `store_memory` tool is still bound to the LLM used by the `orchestrate` node. The `delegate_to` logic can route to a memorizer stub if `store_memory` tool is called.
*   **Stubs (`src/orchestrator/stubs/__init__.py`):**
    *   `RequirementsGathererStub` now subclasses `common.graph.AgentGraph` and its `__init__` takes `config: Optional[BaseConfiguration]`.
*   **State (`src/orchestrator/state.py`):** Docstring updated.

#### 5.2. Architect (`src/architect/`)

*   **Role:** Expert software engineer responsible for architecting a project, not writing code. Receives project needs, coordinates other AI agents. Manages project documentation and defines tasks for other agents.
*   **Key Prompt (`src/architect/prompts/v0.1.md`):** (As previously described)
*   **`prompts.py` (`src/architect/prompts.py`):** (As previously described)
*   **`output.py` (`src/architect/output.py`):** (As previously described)
*   **Structure:** Follows the `agent_template` pattern with modifications.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`.
    *   `graph.py`: Standard `call_model`, `store_memory`, `route_message` flow. Uses `tools.upsert_memory`. *The `agent_template` it was based on has been significantly refactored (removal of `Agent` class, introduction of `AgentTemplateGraph`). If Architect still relies on the old `agent_template` structure, it will require updates to align with `AgentTemplateGraph` or a more custom `AgentGraph` implementation to integrate memory and tools correctly. Its `tools.upsert_memory` is not compatible with the new `SemanticMemory` toolset provided by `AgentGraph` or `AgentTemplateGraph`.*
    *   `state.py`: Standard `State` with `messages`.
    *   `tools.py`: Defines the standard `upsert_memory` tool.
    *   `utils.py`: Standard `split_model_and_provider`, `init_chat_model`.

#### 5.3. Coder (`src/coder/`)
*   **Role:** Software developer agent responsible for writing and modifying code in a GitHub repository. It can create new pull requests or implement changes on existing ones.
*   **Graph Logic (`src/coder/graph.py`):**
    *   Defines configurations for different coding tasks, e.g., `coder_new_pr_config()` for new PRs and `coder_change_request_config()` for modifying existing PRs.
    *   The `coder_change_request_config()` now allows the agent to use the `get_pull_request_head_branch` tool among its available GitHub tools.
*   **Prompts (`src/coder/prompts.py`):**
    *   `CHANGE_REQUEST_SYSTEM_PROMPT`: Updated to instruct the agent that when implementing changes on an existing pull request, it will be given the PR number and needs to work on the PR's head branch. It should sync with the latest changes on the PR's head branch and submit changes there.
*   **Tools:**
    *   Utilizes a suite of GitHub tools provided by `src/common/components/github_tools.py`. This suite is configured via the `GITHUB_TOOLS` list in the same file.
    *   A new tool `get_pull_request_head_branch` (implemented as `GetPullRequestHeadBranch` class) has been added to this suite. This tool allows the agent to fetch the head branch name of a pull request given its number. It is available in both live (via `GitHubAPIWrapper`) and mock (via `MockGithubApi`) environments.
    *   The mock GitHub API (`src/common/components/github_mocks.py`) has been updated:
        *   The `get_pull_request` method now returns a simplified dictionary containing essential PR details (title, number, body, comments, commits).
        *   A `get_pull_request_head_branch` method was added to support mocking the new tool.
*   (Other files like `__init__.py`, `lg_server.py`, `mocks.py`, `state.py`, `tools.py` specific to the coder, and `README.md` are as previously described in the project structure, if detailed.)

#### 5.4. Code Reviewer (`src/code_reviewer/`)
*   Follows the `agent_template` pattern. It will now use the refactored `AgentTemplateGraph`, inheriting its memory capabilities from `AgentGraph` and `SemanticMemory` if configured.

#### 5.5. Tester (`src/tester/`)
*   (No changes mentioned in PR - assumed same as previous state, custom graph, revised prompt)

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`)
*   **Architecture:** Major refactor. Uses the `AgentGraph` pattern. `RequirementsGathererGraph` in `src/requirement_gatherer/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/requirement_gatherer/configuration.py` - NEW FILE, REPLACING INLINE CONFIG):**
    *   Defines its own `Configuration` dataclass in `src/requirement_gatherer/configuration.py`, subclassing `common.config.BaseConfiguration`. (Impacted by `BaseConfiguration` changes, e.g., `memory` field).
    *   `gatherer_system_prompt: str = prompts.SYSTEM_PROMPT`.
    *   `RequirementsGathererGraph.__init__` now accepts `use_human_ai` parameter to control human feedback simulation.
*   **Graph Logic (`src/requirement_gatherer/graph.py`):**
    *   The graph consists of a `call_model` node (created by `_create_call_model` factory) and a `ToolNode` ("tools"). LLM and tools are initialized within `create_builder`.
    *   `call_model`: Retrieves memories, formats them into the system prompt (which includes current time), and invokes an LLM bound with new tools.
    *   `ToolNode`: Executes tools like `human_feedback`, `memorize`, `summarize`.
    *   Routing: `START` -> `call_model`. `call_model` routes to `tools` if tool calls are present, or back to `call_model` or `END` if a summary is generated. `tools` routes back to `call_model`. This logic is encapsulated in a route function created by `_create_gather_requirements` factory.
    *   The previous `call_evaluator_model` and `Veredict`-based flow is REMOVED.
*   **State (`src/requirement_gatherer/state.py`):**
    *   `State` dataclass now has `messages: Annotated[list[AnyMessage], add_messages]` and `summary: str = ""`. Docstring updated.
    *   The `veredict` field has been REMOVED.
*   **Tools (`src/requirement_gatherer/tools.py`):**
    *   Tools are now more modular and defined in `tools.py`:
        *   `human_feedback`: Tool created by `create_human_feedback_tool(use_human_ai=False)` factory. Can request feedback from a human (via `interrupt`) or simulate human responses using an AI if `use_human_ai` is true. Prints interaction to console.
        *   `memorize(content: str, context: str, ...)`: Tool to upsert a memory. Uses `store.aput` with `("memories", user_id)`. This `user_id` would come from its `Configuration` (which inherits `user_id` via `BaseConfiguration.memory.user_id`). This tool is a refactoring of the previous `upsert_memory` function from this file.
        *   `summarize(summary: str, ...)`: Tool to indicate the agent has produced a final summary. Updates state with the summary and prints to console.
    *   The `upsert_memory` function in `src/requirement_gatherer/tools.py` has been refactored and renamed to the `memorize` tool.
    *   A `finalize` tool is no longer present.
*   **Prompts (`src/requirement_gatherer/prompts.py`):**
    *   `SYSTEM_PROMPT` has been significantly REVISED:
        *   Emphasizes using the `human_feedback` tool for asking questions ("MUST NEVER directly ask a question to the user").
        *   Instructs to use the `memorize` tool for documentation.
        *   Instructs to use the `summarize` tool when no questions are pending and a report is generated.
        *   Details a new workflow involving these tools.
        *   The `EVALUATOR_SYSTEM_PROMPT` has been REMOVED.

#### 5.7. Grumpy (`src/grumpy/`)
*   Follows the `agent_template` pattern. It will now use the refactored `AgentTemplateGraph`, inheriting its memory capabilities from `AgentGraph` and `SemanticMemory` if configured.

#### 5.8. Task Manager (`src/task_manager/`)
*   (No changes mentioned in PR - assumed same as previous state, older agent structure)


## 6. Testing Framework (`tests/`)

*   **`tests/integration_tests/test_orchestrator.py`:**
    *   Updated to use the new `OrchestratorGraph` for testing.
*   **`tests/integration_tests/test_requirement_gatherer.py`:**
    *   Updated to use the new `RequirementsGathererGraph`.
    *   Still uses `create_async_graph_caller` and `LLMJudge` for evaluation against LangSmith datasets.
*   **`tests/integration_tests/test_coder.py`:**
    *   Added a new test `test_coder_changes_server_port_on_existing_pr`. This test verifies that the Coder agent, using `coder_change_request_config`, correctly applies changes to the head branch of an existing pull request. It utilizes the `MockGithubApi` for setting up the test scenario.
    *   These tests are now executed as part of the CI pipeline in a dedicated "Coder Tests" job (defined in `.github/workflows/checks.yml`), requiring the `GOOGLE_API_KEY` secret.
*   **`tests/integration_tests/test_graph.py`:**
    *   Updated to use `AgentTemplateGraph` and its `base_config` for initialization when testing memory functionalities.
*   **`tests/unit_tests/test_configuration.py`:**
    *   The previous test `test_configuration_from_none()` related to `orchestrator.configuration.Configuration` is removed as that file is deleted. A dummy test `test_foo()` might be present.
*   **`src/orchestrator/test.py` (Local test script):**
    *   Updated to instantiate `OrchestratorGraph` using `AgentsConfig` and `BaseConfiguration`.
    *   Demonstrates setting `agents_config.requirements.use_stub = False` and `agents_config.requirements.use_human_ai = True`.


## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`)

*   **Make:** Used as a task runner to automate common commands. New targets include:
    *   `make test_coder`: Runs Coder integration tests (`tests/integration_tests/test_coder.py`).
*   **CI (`.github/workflows/checks.yml`):**
    *   The CI pipeline includes jobs for:
        *   Linting (Ruff, codespell)
        *   Unit tests (`make test_unit`)
        *   Coder integration tests (`make test_coder`), which requires the `GOOGLE_API_KEY` secret.
*   **Ruff Linting:** `pyproject.toml` updated with per-file ignores for `T201` (print statements) in `src/orchestrator/{graph,test}.py` and `src/requirement_gatherer/graph.py` and `src/requirement_gatherer/tools.py`.


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/                      # NEW: Cursor specific rules
│   └── rules/                    # NEW
│       └── read-project-memories.mdc # NEW: Rule to always read project_memories
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── checks.yml            # UPDATED: Added Coder Tests job
├── Makefile                      # UPDATED: Added test_coder target
├── README.md                     # UPDATED: Reflects new memory integration methods
├── agent_memories/
│   └── grumpy/
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml                # UPDATED: Ruff per-file ignores
├── scripts/
│   └── generate_project_memory.sh
├── src/
│   ├── agent_template/
│   │   ├── __init__.py           # UPDATED: Exports AgentTemplateGraph, Configuration, State, graph
│   │   ├── agent.py              # DELETED
│   │   ├── configuration.py      # UPDATED: Subclasses BaseConfiguration, fields managed by BaseConfiguration.memory
│   │   ├── graph.py              # UPDATED: Defines AgentTemplateGraph, uses AgentGraph features
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
│   │   ├── graph.py              # UPDATED: coder_change_request_config includes new tool
│   │   ├── lg_server.py
│   │   ├── mocks.py
│   │   ├── prompts.py            # UPDATED: CHANGE_REQUEST_SYSTEM_PROMPT modified
│   │   ├── state.py
│   │   ├── tools.py
│   │   └── README.md
│   ├── common/
│   │   ├── components/
│   │   │   ├── github_mocks.py   # UPDATED: Mock API updated for new tool and PR info
│   │   │   ├── github_tools.py   # UPDATED: Added GetPullRequestHeadBranch tool
│   │   │   └── memory.py         # UPDATED: SemanticMemory uses MemoryConfiguration, MemoryConfiguration dataclass added
│   │   ├── config.py             # UPDATED: BaseConfiguration includes system_prompt and memory: MemoryConfiguration
│   │   ├── graph.py              # UPDATED: AgentGraph initializes SemanticMemory, has memory property and _create_call_model
│   │   └── utils/
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py      # NEW (re-added with new structure): Specific Configuration subclassing BaseConfiguration
│   │   ├── graph.py              # REVISED: Uses new Configuration, AgentsConfig, factory functions for nodes
│   │   ├── memory/
│   │   │   └── team.md           # UPDATED: Delegate tool must include content
│   │   ├── prompts.py            # UPDATED: System prompt includes {time}
│   │   ├── state.py              # REVISED: Docstring
│   │   ├── stubs/
│   │   │   └── __init__.py       # UPDATED: RequirementsGathererStub __init__ takes BaseConfiguration
│   │   ├── test.py               # REVISED: Uses AgentsConfig, BaseConfiguration
│   │   └── tools.py              # UPDATED: Delegate tool requires 'content'
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py      # NEW (re-added with new structure): Specific Configuration subclassing BaseConfiguration
│   │   ├── graph.py              # REVISED: Uses new Configuration, factory functions for nodes, new tool usage
│   │   ├── prompts.py            # REVISED: System prompt updated for new tools/workflow, evaluator prompt removed
│   │   ├── state.py              # REVISED: 'veredict' removed, 'summary' added, docstring
│   │   └── tools.py              # REVISED: Defines create_human_feedback_tool, memorize (refactored from upsert_memory), summarize
│   ├── task_manager/
│   └── tester/
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py           # UPDATED: New test added for PR head branch changes; now run in CI
    │   ├── eval_coder.py
    │   ├── test_graph.py           # UPDATED: Uses AgentTemplateGraph
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py    # UPDATED: Uses new OrchestratorGraph
    │   ├── test_requirement_gatherer.py # UPDATED: Uses new RequirementsGathererGraph
    │   ├── test_task_manager.py
    │   └── test_tester_agent.py
    ├── testing/
    │   ├── __init__.py
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py   # REVISED: Old test removed, may contain dummy test
```
