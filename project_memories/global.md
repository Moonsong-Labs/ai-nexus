# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is now `langmem`, providing semantic search capabilities over stored memories, replacing the previous conceptual Markdown-based "Memory Bank" and direct `upsert_memory` tool usage for agents based on the template.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools or custom tools like `file_dump`, or agent-specific tools like the Requirement Gatherer's `memorize` and `human_feedback`).
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols.
6.  **Configuration Management (REVISED):** Agents have configurable parameters, including LLM models, system prompts, and memory settings (e.g., `use_static_mem`). This is managed via:
    *   `AgentConfiguration` dataclass from `src/common/configuration.py` (NEW, REPLACING `BaseConfiguration` from `src/common/config.py`).
    *   Agent-specific `Configuration` dataclasses (e.g., in `src/orchestrator/configuration.py`, `src/requirement_gatherer/configuration.py`) that subclass `AgentConfiguration`.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents, typically managed via the `Agent` class and `SemanticMemory` component for agents following the `agent_template`. Other agents like Requirement Gatherer might implement memory tools differently. Memory configuration is part of `AgentConfiguration` via its `memory: MemoryConfiguration` field.
9.  **`AgentGraph` (REVISED):** A common base class (`src/common/graph.py`) for defining agent graphs, promoting modularity. Used by Orchestrator and Requirement Gatherer (now `RequirementsGraph`). Its `__init__` method now takes `name: str` and `agent_config: AgentConfiguration`. It no longer provides a `_create_call_model` method.


## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence, particularly for the "Cursor" idea. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and custom tools):** The project has integrated the `langmem` library to provide a more robust and queryable semantic memory system for agents based on the `agent_template`. These agents utilize `langmem` tools for storing and retrieving memories.
Other agents, like the Requirement Gatherer, now use custom tools (e.g., `memorize`) that might interact with the same underlying storage mechanism but are defined and invoked differently within their specific graph structure.

*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`).
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`. The `user_id` is part of `AgentConfiguration`.
*   **Tools:**
    *   `agent_template` based agents: Use `langmem`-provided tools (`manage_memory`, `search_memory`) via `SemanticMemory`. A custom `memory_dump` tool is also available.
    *   Requirement Gatherer: Uses a custom `memorize` tool (defined in `src/requirement_gatherer/tools.py`, refactored from a previous `upsert_memory` function in the same file) for storing memories.
*   **Static Memories:** The concept of static, pre-loaded knowledge persists. JSON files in `.langgraph/static_memories/` can be loaded into the `BaseStore` under a static namespace if `use_static_mem` is enabled in the agent's `AgentConfiguration.memory` settings.
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
    *   **Local Demo Script (NEW):** `src/demo/orchestrate.py` can be run using `uv run --env-file .env -- python ./src/demo/orchestrate.py exec ai` (see README).
*   **Testing & Code Quality:**
    *   **pytest:** The main framework for running tests.
    *   **pytest-asyncio:** Enables testing of asynchronous code.
    *   **pytest-dotenv:** Loads environment variables specifically for tests.
    *   **pytest-watch (ptw):** Runs tests automatically when files change.
    *   **Ruff:** Performs code linting and formatting. `pyproject.toml` updated for `src/demo/*` ignores.
    *   **Mypy:** Conducts static type checking (currently not enforced in CI/default linting pass).
    *   **codespell:** Checks for spelling mistakes.
    *   **openevals:** Used for custom evaluation logic, particularly for the Coder agent.
    *   **CI Pipeline (`.github/workflows/checks.yml`):** Runs linting (Ruff, codespell), unit tests (`make test_unit`), and Coder integration tests (`make test_coder`). The Coder tests job requires `GOOGLE_API_KEY` as a secret.
*   **Version Control:** Git.
*   **LLM Models:**
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default updated to `gemini-2.5-flash-preview-04-17`). Orchestrator and Requirement Gatherer default to `google_genai:gemini-2.0-flash` via `AgentConfiguration`.
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning.


## 4. General Agent Architecture

AI Nexus employs a few architectural patterns for its agents:

**4.1. `agent_template` based Architecture (e.g., Code Reviewer, Grumpy) (REVISED)**

Most agents in AI Nexus follow a common structural and operational pattern, largely derived from `src/agent_template/`. *Note: Some agents, like the Tester, Coder, or Task Manager, may deviate significantly from this template's graph logic or tool usage.*

*   **Typical Agent Directory Structure:** (As previously described)
*   **`configuration.py` (Typical Structure - `src/agent_template/configuration.py`):** Now subclasses `common.configuration.AgentConfiguration`. Default model is `gemini-2.5-flash-preview-04-17`.
*   **`state.py` (Typical Structure - `src/agent_template/state.py`):** (As previously described, with `user_id`)
*   **`agent.py` (`src/agent_template/agent.py`):** The `Agent` class defined here (which previously handled LLM interaction, memory formatting, and provided `call_model_with_tools`) is NO LONGER directly used by `AgentTemplateGraph` to create the main model calling node. Its role in the standard template flow is diminished.
*   **`graph.py` (Core Logic - `src/agent_template/graph.py`) (REVISED):**
    *   `AgentTemplateGraph.__init__` now takes `agent_config: Optional[Configuration]` (its specific `Configuration` subclassing `AgentConfiguration`) and sets a `name` ("Agent Template").
    *   `create_builder()`:
        *   Initializes LLM directly: `llm = init_chat_model(self._agent_config.model)`.
        *   Binds tools (including memory tools from `SemanticMemory` if enabled) to this LLM.
        *   The main model calling node (`call_model`) is created using a local helper function `_create_call_model(llm)`. This function:
            *   Retrieves `agent_config` from the runtime `config["configurable"]["agent_config"]`.
            *   Uses `agent_config.system_prompt`.
            *   Invokes the LLM with the system prompt and current messages.
            *   It does *not* automatically retrieve and inject memories into the system prompt like the former `Agent.call_model_with_tools` did. Memory interaction relies on the agent using tools like `search_memory`.
        *   Adds nodes and edges: `START` -> `call_model`, `call_model` -> `tools` (if tools called) / `END`, `tools` -> `call_model`.
*   **`tools.py` (Utility Tools - `src/agent_template/tools.py`):** (As previously described, `file_dump` tool, `upsert_memory` removed)
*   **`memory.py` (`src/agent_template/memory.py`):** DELETED.
*   **`src/common/components/memory.py` (NEW):** (As previously described, `SemanticMemory` class, static memory loading, `langmem` tool creation)
*   **`prompts.py` (`src/agent_template/prompts.py`):** (As previously described, instruction to mention memory retrieval)

**4.2. `AgentGraph` based Architecture (REVISED - e.g., Orchestrator, Requirement Gatherer)**

A newer pattern utilizes a common base class for more modular graph definitions.

*   **`src/common/config.py`:** DELETED.
*   **`src/common/configuration.py` (NEW):**
    ```python
    from dataclasses import dataclass, field
    from common.components.memory import MemoryConfiguration # Assuming this path

    @dataclass(kw_only=True)
    class AgentConfiguration:
        # langgraph config
        user_id: str = "default"
        model: str = "google_genai:gemini-2.0-flash"
        provider: str | None = None
        # extended config
        memory: MemoryConfiguration = field(default_factory=MemoryConfiguration)

        @property
        def langgraph_configurables(self) -> dict[str, Any]:
            # Returns user_id, model, provider for langgraph's config system
            ...
    ```
*   **`src/common/graph.py` (REVISED):**
    *   Defines an abstract base class `AgentGraph(ABC)`.
    *   `__init__(self, *, name: str, agent_config: AgentConfiguration, checkpointer, store)`: Initializes with agent name, `AgentConfiguration` (replacing `BaseConfiguration`), optional checkpointer and store. Stores `agent_config` as `self._agent_config`.
    *   No longer contains a `_create_call_model` method.
    *   `create_builder() -> StateGraph` (abstract method): To be implemented by subclasses to define the graph.
    *   `compiled_graph`: Property to get or compile the graph.
    *   `ainvoke(state, config)`: Invokes the compiled graph, merging instance `agent_config` (via `_merge_config`) with call-time config. `_merge_config` now places the full `agent_config` into `new_config["configurable"]["agent_config"]`.

Agents like Orchestrator and Requirement Gatherer (now `RequirementsGraph`) subclass `AgentGraph` and define their specific `Configuration` (subclassing `common.configuration.AgentConfiguration` in their respective `configuration.py` files) and graph structure. Graph construction is more modular, often using factory functions to create nodes and tools.


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`)
*   **Architecture:** Uses the `AgentGraph` pattern. `OrchestratorGraph.__init__` now takes `agent_config: Optional[Configuration]` (its own `Configuration` subclassing `AgentConfiguration`).
*   **Configuration (`src/orchestrator/configuration.py` - REVISED):**
    *   Defines its own `Configuration` dataclass, subclassing `common.configuration.AgentConfiguration`.
    *   `system_prompt: str = prompts.get_prompt()` (which now formats current `time` into the prompt).
    *   Integrates sub-agent configurations:
        *   Defines `SubAgentConfig` and `RequirementsAgentConfig` dataclasses.
        *   `Configuration` has fields like `requirements_agent: RequirementsAgentConfig`.
        *   `RequirementsAgentConfig` includes `use_stub: bool` and `config: RequirementsConfiguration` (the config for the requirements agent itself).
    *   The old `AgentsConfig` dataclass (previously in `orchestrator/graph.py`) is effectively replaced by this new structure within `orchestrator.configuration.Configuration`.
*   **Graph Logic (`src/orchestrator/graph.py`):**
    *   The `orchestrate` node (created by `_create_orchestrate` factory) uses the system prompt from `self._agent_config.system_prompt`. LLM is initialized with `self._agent_config.model`.
    *   The `delegate_to` routing function (created by `_create_delegate_to` factory) is updated.
    *   Integrates other agent graphs/stubs; for example, it can instantiate `RequirementsGraph` (or `RequirementsGathererStub`) based on `self._agent_config.requirements_agent`. The `requirements` node is created by `_create_requirements_node` factory.
*   **Prompts (`src/orchestrator/prompts.py`):**
    *   `ORCHESTRATOR_SYSTEM_PROMPT` (and the one constructed by `get_prompt()`) now includes a `{time}` placeholder, formatted with the current time during graph execution.
    *   `src/orchestrator/memory/team.md`: Updated to specify that the `Delegate` tool usage MUST include the `content` field for the delegated task.
*   **Tools (`src/orchestrator/tools.py`):**
    *   The `Delegate` tool's Pydantic model now includes a mandatory `content: str` field.
    *   The `store_memory` tool is still bound to the LLM used by the `orchestrate` node. The `delegate_to` logic can route to a memorizer stub if `store_memory` tool is called.
*   **Stubs (`src/orchestrator/stubs/__init__.py`):**
    *   `RequirementsGathererStub` now subclasses `common.graph.AgentGraph` and its `__init__` takes `agent_config: Optional[AgentConfiguration]`.
*   **State (`src/orchestrator/state.py`):** Docstring updated.

#### 5.2. Architect (`src/architect/`)

*   (No changes mentioned in PR - likely still follows its previous custom structure. If it were to be updated to use `AgentGraph` or `AgentTemplateGraph`, its configuration would need to change to `AgentConfiguration`.)
*   **Role:** Expert software engineer responsible for architecting a project, not writing code. Receives project needs, coordinates other AI agents. Manages project documentation and defines tasks for other agents.
*   **Key Prompt (`src/architect/prompts/v0.1.md`):** (As previously described)
*   **`prompts.py` (`src/architect/prompts.py`):** (As previously described)
*   **`output.py` (`src/architect/output.py`):** (As previously described)
*   **Structure:** Follows the `agent_template` pattern with modifications.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`. *If updated, would use `AgentConfiguration`.*
    *   `graph.py`: Standard `call_model`, `store_memory`, `route_message` flow. Uses `tools.upsert_memory`. *This agent has not been updated to the new `Agent` class / `langmem` tools pattern yet, nor the new `AgentGraph` config system.*
    *   `state.py`: Standard `State` with `messages`.
    *   `tools.py`: Defines the standard `upsert_memory` tool.
    *   `utils.py`: Standard `split_model_and_provider`, `init_chat_model`.

#### 5.3. Coder (`src/coder/`)
*   (No changes related to the configuration system overhaul in this PR.)
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
*   (No changes mentioned in PR - assumed same as previous state. If it follows `agent_template`, its configuration and graph instantiation would be updated as per section 4.1.)

#### 5.5. Tester (`src/tester/`)
*   (No changes mentioned in PR - assumed same as previous state, custom graph, revised prompt. If it uses `AgentGraph`, its configuration would be updated.)

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`) (REVISED)
*   **Architecture:** Major refactor. Uses the `AgentGraph` pattern. `RequirementsGathererGraph` RENAMED to `RequirementsGraph`. `RequirementsGraph.__init__` now takes `agent_config: Optional[Configuration]` (its own `Configuration` subclassing `AgentConfiguration`).
*   **Configuration (`src/requirement_gatherer/configuration.py` - REVISED):**
    *   Defines its own `Configuration` dataclass, subclassing `common.configuration.AgentConfiguration`.
    *   `gatherer_system_prompt: str = prompts.SYSTEM_PROMPT`.
    *   Adds `use_human_ai: bool = False` field (defaulting to False). This controls the behavior of the `human_feedback` tool.
*   **Graph Logic (`src/requirement_gatherer/graph.py` - RENAMED `RequirementsGraph`):**
    *   The graph consists of a `call_model` node (created by `_create_call_model` factory) and a `ToolNode` ("tools"). LLM and tools are initialized within `create_builder`.
    *   `_create_call_model` factory:
        *   Retrieves `agent_config` from `config["configurable"]["agent_config"]`.
        *   Uses `agent_config.gatherer_system_prompt`.
    *   `create_builder()`:
        *   Initializes LLM: `llm = init_chat_model(self._agent_config.model)`.
        *   `human_feedback` tool is created by `tools.create_human_feedback_tool(use_human_ai=self._agent_config.use_human_ai)`.
    *   `call_model`: Retrieves memories, formats them into the system prompt (which includes current time), and invokes an LLM bound with new tools.
    *   `ToolNode`: Executes tools like `human_feedback`, `memorize`, `summarize`.
    *   Routing: `START` -> `call_model`. `call_model` routes to `tools` if tool calls are present, or back to `call_model` or `END` if a summary is generated. `tools` routes back to `call_model`. This logic is encapsulated in a route function created by `_create_gather_requirements` factory.
    *   The previous `call_evaluator_model` and `Veredict`-based flow is REMOVED.
*   **State (`src/requirement_gatherer/state.py`):**
    *   `State` dataclass now has `messages: Annotated[list[AnyMessage], add_messages]` and `summary: str = ""`. Docstring updated.
    *   The `veredict` field has been REMOVED.
*   **Tools (`src/requirement_gatherer/tools.py`):**
    *   Tools are now more modular and defined in `tools.py`:
        *   `human_feedback`: Tool created by `create_human_feedback_tool(...)` factory. The inner `human_feedback` function now gets `agent_config` from `config["configurable"]["agent_config"]` to determine if AI should simulate human responses based on `agent_config.use_human_ai`. Prints interaction to console.
        *   `memorize(content: str, context: str, ...)`: Tool to upsert a memory. Uses `store.aput` with `("memories", user_id)`. This tool is a refactoring of the previous `upsert_memory` function from this file.
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
*   **`src/requirement_gatherer/utils.py`:** DELETED.

#### 5.7. Grumpy (`src/grumpy/`)
*   (No changes mentioned in PR - assumed same as previous state. If it follows `agent_template`, its configuration and graph instantiation would be updated as per section 4.1.)

#### 5.8. Task Manager (`src/task_manager/`) (REVISED)
*   **Architecture:** Uses `AgentGraph`. `TaskManagerGraph.__init__` now takes `agent_config: Optional[Configuration]` (its own `Configuration` subclassing `AgentConfiguration`).
*   **Configuration (`src/task_manager/configuration.py` - UPDATED):**
    *   Defines its own `Configuration` dataclass, subclassing `common.configuration.AgentConfiguration`.
*   **Graph Logic (`src/task_manager/graph.py`):**
    *   `_create_call_model` factory:
        *   Retrieves `agent_config` from `config["configurable"]["agent_config"]`.
        *   Uses `agent_config.task_manager_system_prompt`.
    *   `create_builder()`:
        *   Initializes LLM: `llm = init_chat_model(self._agent_config.model)`.


## 6. Testing Framework (`tests/`)

*   **`tests/integration_tests/test_orchestrator.py`:**
    *   Updated to use the new `OrchestratorGraph` for testing (implicitly, as the demo script it might be based on was updated).
*   **`tests/integration_tests/test_requirement_gatherer.py`:**
    *   Updated to use the new `RequirementsGraph` (renamed from `RequirementsGathererGraph`).
    *   Still uses `create_async_graph_caller` and `LLMJudge` for evaluation against LangSmith datasets.
*   **`tests/integration_tests/test_coder.py`:**
    *   Added a new test `test_coder_changes_server_port_on_existing_pr`. This test verifies that the Coder agent, using `coder_change_request_config`, correctly applies changes to the head branch of an existing pull request. It utilizes the `MockGithubApi` for setting up the test scenario.
    *   These tests are now executed as part of the CI pipeline in a dedicated "Coder Tests" job (defined in `.github/workflows/checks.yml`), requiring the `GOOGLE_API_KEY` secret.
*   **`tests/integration_tests/test_graph.py` (UPDATED):**
    *   Updated to instantiate `AgentTemplateGraph` using `agent_config=config`.
*   **`tests/unit_tests/test_configuration.py`:**
    *   The previous test `test_configuration_from_none()` related to `orchestrator.configuration.Configuration` is removed as that file was deleted and re-added with a new structure. Test content likely changed.
*   **`src/orchestrator/test.py` (Local test script) RENAMED to `src/demo/orchestrate.py` (UPDATED):**
    *   Updated to instantiate `OrchestratorGraph` using `OrchestratorConfiguration` (which includes nested configurations like `RequirementsAgentConfig` and `RequirementsConfiguration`).
    *   Demonstrates setting `use_stub` and `use_human_ai` via the new configuration objects.
    *   Sets `recursion_limit` in `RunnableConfig` for the demo run.
*   **`tests/datasets/task_manager_dataset.py`:** Typo fix in an output message.


## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`)

*   **Make:** Used as a task runner to automate common commands. New targets include:
    *   `make test_coder`: Runs Coder integration tests (`tests/integration_tests/test_coder.py`).
*   **CI (`.github/workflows/checks.yml`):**
    *   The CI pipeline includes jobs for:
        *   Linting (Ruff, codespell)
        *   Unit tests (`make test_unit`)
        *   Coder integration tests (`make test_coder`), which requires the `GOOGLE_API_KEY` secret.
*   **Ruff Linting:** `pyproject.toml` updated with per-file ignores for `T201` (print statements) in `src/orchestrator/{graph}.py`, `src/requirement_gatherer/graph.py`, `src/requirement_gatherer/tools.py`, and now `src/demo/*`. (Note: `src/orchestrator/test.py` is now `src/demo/orchestrate.py`).
*   **`.gitignore` (UPDATED):** Added `dump.json` (output from the demo script).
*   **README.md (UPDATED):**
    *   Examples for adding semantic memory and agent usage updated to reflect new configuration system (`agent_config`, `AgentConfiguration`).
    *   Added instructions for running the local demo script `src/demo/orchestrate.py`.


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/
│   └── rules/
│       └── read-project-memories.mdc
├── .env.example
├── .gitignore                    # UPDATED: Added dump.json
├── .github/
│   └── workflows/
│       └── checks.yml
├── Makefile
├── README.md                     # UPDATED: New config examples, demo instructions
├── agent_memories/
│   └── grumpy/
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml                # UPDATED: Ruff per-file ignores for src/demo
├── scripts/
│   └── generate_project_memory.sh
├── src/
│   ├── agent_template/
│   │   ├── __init__.py
│   │   ├── agent.py              # REVISED: Role in AgentTemplateGraph diminished
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration
│   │   ├── graph.py              # REVISED: Uses local _create_call_model, no longer Agent class for model node
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
│   │   │   └── memory.py
│   │   ├── config.py             # DELETED
│   │   ├── configuration.py      # NEW: Defines AgentConfiguration
│   │   ├── graph.py              # REVISED: AgentGraph __init__ signature, no _create_call_model
│   │   └── utils/
│   ├── demo/                     # NEW Directory
│   │   └── orchestrate.py        # NEW (Renamed from src/orchestrator/test.py, updated)
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py      # REVISED: Subclasses AgentConfiguration, includes sub-agent configs
│   │   ├── graph.py              # REVISED: Uses new Configuration, updated LLM/sub-agent instantiation
│   │   ├── memory/
│   │   │   └── team.md
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── stubs/
│   │   │   └── __init__.py       # UPDATED: RequirementsGathererStub __init__ takes AgentConfiguration
│   │   ├── test.py               # DELETED (Moved to src/demo/orchestrate.py)
│   │   └── tools.py
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py      # REVISED: Subclasses AgentConfiguration, adds use_human_ai
│   │   ├── graph.py              # REVISED: Renamed to RequirementsGraph, uses new Configuration, updated LLM/tool instantiation
│   │   ├── prompts.py
│   │   ├── state.py
│   │   ├── tools.py              # REVISED: human_feedback tool uses agent_config.use_human_ai
│   │   └── utils.py              # DELETED
│   ├── task_manager/
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration
│   │   └── graph.py              # REVISED: Uses new Configuration
│   └── tester/
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py # UPDATED: Typo fix in output
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py
    │   ├── eval_coder.py
    │   ├── test_graph.py           # UPDATED: Uses new AgentTemplateGraph(agent_config=...)
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py
    │   ├── test_requirement_gatherer.py # UPDATED: Uses new RequirementsGraph
    │   ├── test_task_manager.py
    │   └── test_tester_agent.py
    ├── testing/
    │   ├── __init__.py
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py   # REVISED: Content likely changed due to config system overhaul
```
