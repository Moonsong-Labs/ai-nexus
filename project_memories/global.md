# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents. The Task Manager agent, for instance, now expects a structured set of 8 specific project documentation files (e.g., `projectRequirements.md`, `techContext.md`) to perform its planning functions.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is now `langmem`, providing semantic search capabilities over stored memories, replacing the previous conceptual Markdown-based "Memory Bank" and direct `upsert_memory` tool usage for agents based on the template.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools or custom tools like `file_dump`, or agent-specific tools like the Requirement Gatherer's `memorize` and `human_feedback`, or Task Manager's file system tools).
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols.
6.  **Configuration Management:** Agents have configurable parameters, including LLM models, system prompts, and memory settings (e.g., `use_static_mem`). This is managed via:
    *   `Configuration` dataclasses from `agent_template`.
    *   A common `BaseConfiguration` in `src/common/config.py`.
    *   Agent-specific `Configuration` dataclasses (e.g., in `src/orchestrator/configuration.py`, `src/requirement_gatherer/configuration.py`, `src/task_manager/configuration.py`) that subclass `BaseConfiguration`.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents, typically managed via the `Agent` class and `SemanticMemory` component for agents following the `agent_template`. Other agents like Requirement Gatherer or Task Manager might implement memory tools differently or focus on other types of state/file management.
9.  **`AgentGraph` (NEW):** A common base class (`src/common/graph.py`) for defining agent graphs, promoting modularity. Used by Orchestrator, Requirement Gatherer, and Task Manager. Its `__init__` method now takes `base_config: BaseConfiguration`.


## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence, particularly for the "Cursor" idea. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and custom tools):** The project has integrated the `langmem` library to provide a more robust and queryable semantic memory system for agents based on the `agent_template`. These agents utilize `langmem` tools for storing and retrieving memories.
Other agents, like the Requirement Gatherer, now use custom tools (e.g., `memorize`) that might interact with the same underlying storage mechanism but are defined and invoked differently within their specific graph structure. The Task Manager primarily interacts with the file system using tools like `read_file`, `create_file`, and `list_files` to manage project documentation and planning artifacts.

*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`). For Task Manager, memories can also be retrieved by its `call_model` node from the `BaseStore` if available, namespaced by `("memories", user_id)`.
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`.
*   **Tools:**
    *   `agent_template` based agents: Use `langmem`-provided tools (`manage_memory`, `search_memory`) via `SemanticMemory`. A custom `memory_dump` tool is also available.
    *   Requirement Gatherer: Uses a custom `memorize` tool (defined in `src/requirement_gatherer/tools.py`, refactored from a previous `upsert_memory` function in the same file) for storing memories.
    *   Task Manager: Uses tools like `read_file`, `create_file`, `list_files`.
*   **Static Memories:** The concept of static, pre-loaded knowledge persists. JSON files in `.langgraph/static_memories/` can be loaded into the `BaseStore` under a static namespace if `use_static_mem` is enabled in the agent's configuration.
*   **Shift:** The shift moves from human-readable Markdown files as the primary memory source to a database/store queried semantically via tools. The core principle of externalized memory remains, but the implementation mechanism has evolved. The specific file structure (`projectbrief.md`, `productContext.md`, etc.) described previously is not directly implemented by the `langmem` system, although the *types* of information they represent might be stored as individual memories. However, the Task Manager now explicitly relies on a defined set of 8 Markdown files as input.


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
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default updated to `gemini-2.5-flash-preview-04-17`). Orchestrator and Requirement Gatherer default to `google_genai:gemini-2.0-flash` via `BaseConfiguration`. Task Manager uses `google_genai:gemini-2.5-flash-preview-04-17`.
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning.


## 4. General Agent Architecture

AI Nexus employs a few architectural patterns for its agents:

**4.1. `agent_template` based Architecture (e.g., Code Reviewer, Grumpy)**

Most agents in AI Nexus follow a common structural and operational pattern, largely derived from `src/agent_template/`. *Note: Some agents, like the Tester, Coder, or Task Manager, may deviate significantly from this template's graph logic or tool usage.*

*   **Typical Agent Directory Structure:** (As previously described)
*   **`configuration.py` (Typical Structure - `src/agent_template/configuration.py`):** (As previously described, with `use_static_mem` and updated default model)
*   **`state.py` (Typical Structure - `src/agent_template/state.py`):** (As previously described, with `user_id`)
*   **`agent.py` (NEW - `src/agent_template/agent.py`):** (As previously described, handles LLM interaction and `langmem` via `SemanticMemory`)
*   **`graph.py` (Core Logic - Revised Flow from `src/agent_template/graph.py`):** (As previously described, uses `Agent` class, `ToolNode`, `tools_condition`)
*   **`tools.py` (Utility Tools - `src/agent_template/tools.py`):** (As previously described, `file_dump` tool, `upsert_memory` removed)
*   **`memory.py` (`src/agent_template/memory.py`):** DELETED.
*   **`src/common/components/memory.py` (NEW):** (As previously described, `SemanticMemory` class, static memory loading, `langmem` tool creation)
*   **`prompts.py` (`src/agent_template/prompts.py`):** (As previously described, instruction to mention memory retrieval)

**4.2. `AgentGraph` based Architecture (NEW - e.g., Orchestrator, Requirement Gatherer, Task Manager)**

A newer pattern utilizes a common base class for more modular graph definitions.

*   **`src/common/config.py` (NEW):**
    ```python
    from dataclasses import dataclass

    @dataclass(kw_only=True)
    class BaseConfiguration: # RENAMED from Configuration
        user_id: str = "default"
        model: str = "google_genai:gemini-2.0-flash"
        provider: str | None = None
        # Agent-specific prompts or other configs are added in subclasses
    ```
*   **`src/common/graph.py` (NEW):**
    *   Defines an abstract base class `AgentGraph(ABC)`.
    *   `__init__(base_config: BaseConfiguration, checkpointer, store)`: Initializes with common config (type updated to `BaseConfiguration`), optional checkpointer and store.
    *   `create_builder() -> StateGraph` (abstract method): To be implemented by subclasses to define the graph.
    *   `compiled_graph`: Property to get or compile the graph.
    *   `ainvoke(state, config)`: Invokes the compiled graph, merging instance config with call-time config.

Agents like Orchestrator, Requirement Gatherer, and Task Manager now subclass `AgentGraph` and define their specific `Configuration` (subclassing `common.config.BaseConfiguration` in their respective new or updated `configuration.py` files) and graph structure. Graph construction is more modular, often using factory functions to create nodes and tools.


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`)
*   **Architecture:** Uses the `AgentGraph` pattern. `OrchestratorGraph` in `src/orchestrator/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/orchestrator/configuration.py` - NEW FILE, REPLACING INLINE CONFIG):**
    *   Defines its own `Configuration` dataclass in `src/orchestrator/configuration.py`, subclassing `common.config.BaseConfiguration`.
    *   `system_prompt: str = prompts.get_prompt()` (which now formats current `time` into the prompt).
    *   The dedicated `src/orchestrator/configuration.py` file from a previous state was deleted, but this PR re-introduces it with the new structure.
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

*   (No changes mentioned in PR - likely still follows the `agent_template` pattern or its previous custom structure. If based on `agent_template`, it would benefit from the `langmem` updates indirectly.)
*   **Role:** Expert software engineer responsible for architecting a project, not writing code. Receives project needs, coordinates other AI agents. Manages project documentation and defines tasks for other agents.
*   **Key Prompt (`src/architect/prompts/v0.1.md`):** (As previously described)
*   **`prompts.py` (`src/architect/prompts.py`):** (As previously described)
*   **`output.py` (`src/architect/output.py`):** (As previously described)
*   **Structure:** Follows the `agent_template` pattern with modifications.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`.
    *   `graph.py`: Standard `call_model`, `store_memory`, `route_message` flow. Uses `tools.upsert_memory`. *This agent has not been updated to the new `Agent` class / `langmem` tools pattern yet.*
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
*   (No changes mentioned in PR - assumed same as previous state, follows `agent_template` and uses `langmem`)

#### 5.5. Tester (`src/tester/`)
*   (No changes mentioned in PR - assumed same as previous state, custom graph, revised prompt)

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`)
*   **Architecture:** Major refactor. Uses the `AgentGraph` pattern. `RequirementsGathererGraph` in `src/requirement_gatherer/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/requirement_gatherer/configuration.py` - NEW FILE, REPLACING INLINE CONFIG):**
    *   Defines its own `Configuration` dataclass in `src/requirement_gatherer/configuration.py`, subclassing `common.config.BaseConfiguration`.
    *   `gatherer_system_prompt: str = prompts.SYSTEM_PROMPT`.
    *   The dedicated `src/requirement_gatherer/configuration.py` file from a previous state was deleted, but this PR re-introduces it with the new structure.
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

#### 5.7. Grumpy (`src/grumpy/`)
*   (No changes mentioned in PR - assumed same as previous state, follows `agent_template` and uses `langmem`)

#### 5.8. Task Manager (`src/task_manager/`)
*   **Architecture:** Major refactor. Uses the `AgentGraph` pattern. `TaskManagerGraph` in `src/task_manager/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/task_manager/configuration.py` - REVISED):**
    *   Defines its own `Configuration` dataclass, subclassing `common.config.BaseConfiguration`.
    *   `task_manager_system_prompt: str = prompts.SYSTEM_PROMPT`.
    *   `model: str = "google_genai:gemini-2.5-flash-preview-04-17"`.
*   **Graph Logic (`src/task_manager/graph.py` - REVISED):**
    *   `TaskManagerGraph` initializes with `base_config`, `checkpointer`, `store`.
    *   `create_builder` method sets up the graph:
        *   LLM (`google_genai:gemini-2.5-flash-preview-04-17`) is bound with tools: `read_file`, `create_file`, `list_files`.
        *   `call_model` node created by `_create_call_model` factory:
            *   Retrieves recent memories from the `store` (if available, namespaced by `("memories", user_id)`) for context.
            *   Formats memories and current time into the system prompt.
            *   Invokes the LLM with a `recursion_limit` of 100 (`TASK_MANAGER_RECURSION_LIMIT`).
        *   `ToolNode` ("tools") executes the bound file system tools.
    *   Graph flow: `START` -> `call_model` -> (tools_condition routes to `tools` if tool calls, else `END`) -> `tools` -> `call_model`.
*   **State (`src/task_manager/state.py`):** (Assumed to be standard `State` with `messages`, as per `AgentGraph` pattern, but not explicitly changed in PR diff for state.py itself).
*   **Tools (`src/task_manager/tools.py`):** Uses standard file system tools: `read_file`, `create_file`, `list_files` (likely from `langchain_community.tools` or similar, bound in graph).
*   **Prompts (`src/task_manager/prompts.py` - REVISED):**
    *   `SYSTEM_PROMPT` is significantly updated to define a new workflow:
        *   **Input:** User provides a `project_name`. The agent then looks for a project directory (e.g., `src/task_manager/volume/[project_name]/`).
        *   **Required Input Files (8):** The agent MUST find the following 8 files in the project directory:
            1.  `projectRequirements.md`
            2.  `techContext.md`
            3.  `systemPatterns.md` (task splitting criteria)
            4.  `testingContext.md`
            5.  `projectbrief.md`
            6.  `featuresContext.md`
            7.  `securityContext.md`
            8.  `progress.md`
        *   **Workflow Stages:**
            1.  **Project Validation and Analysis:** Check for directory and all 8 files. If missing, respond with "VALIDATION_FAILED..." and stop. Otherwise, read and analyze files.
            2.  **Tasks Creation:** Apply task splitting guidelines (e.g., 6-14 hours per task). Create a `planning` subdirectory within the project's volume directory. Generate individual Markdown files for each task (e.g., `task-01-setup-scaffolding-dependencies.md`) in this `planning` directory. Each task file includes fields like `id`, `title`, `description`, `status` ("pending"), `dependencies`, `priority`, `details`, `testStrategy`, `subtasks`, `issueLink`, `pullRequestLink`, `skillRequirements`, `acceptanceCriteria`, `assignee` (blank), `estimatedHours`.
            3.  **Planning Creation:** Read all generated task files. Create a `roadmap.md` file in the `planning` directory (e.g., `src/task_manager/volume/[project_name]/planning/roadmap.md`). This roadmap organizes tasks week by week, assigns tasks to team members (1 engineer by default), respects dependencies, and manages workload.
        *   **Team Configuration:** Default 1 engineer, 40 hours/week.
        *   **Output:** Individual task Markdown files and a `roadmap.md` file, all located in the `planning` subdirectory.
*   **Example Input Files:** The PR adds a set of example input files for a "Simple Rust API" project under `src/task_manager/volume/api_rust/` demonstrating the 8 required file types.


## 6. Testing Framework (`tests/`)

*   **`tests/integration_tests/test_orchestrator.py`:**
    *   Updated to use the new `OrchestratorGraph` for testing.
*   **`tests/integration_tests/test_requirement_gatherer.py`:**
    *   Updated to use the new `RequirementsGathererGraph`.
    *   Still uses `create_async_graph_caller` and `LLMJudge` for evaluation against LangSmith datasets.
*   **`tests/integration_tests/test_coder.py`:**
    *   Added a new test `test_coder_changes_server_port_on_existing_pr`. This test verifies that the Coder agent, using `coder_change_request_config`, correctly applies changes to the head branch of an existing pull request. It utilizes the `MockGithubApi` for setting up the test scenario.
    *   These tests are now executed as part of the CI pipeline in a dedicated "Coder Tests" job (defined in `.github/workflows/checks.yml`), requiring the `GOOGLE_API_KEY` secret.
*   **`tests/integration_tests/test_task_manager.py` (UPDATED):**
    *   Updated to use the new `TaskManagerGraph`.
    *   The `call_model` helper function is updated for the new configuration and model (`google_genai:gemini-2.5-flash-preview-04-17`).
    *   LangSmith evaluation uses `TaskManagerGraph` instance.
*   **`tests/unit_tests/test_configuration.py`:**
    *   The previous test `test_configuration_from_none()` related to `orchestrator.configuration.Configuration` is removed as that file is deleted. A dummy test `test_foo()` might be present.
*   **`src/orchestrator/test.py` (Local test script):**
    *   Updated to instantiate `OrchestratorGraph` using `AgentsConfig` and `BaseConfiguration`.
    *   Demonstrates setting `agents_config.requirements.use_stub = False` and `agents_config.requirements.use_human_ai = True`.
*   **`tests/datasets/task_manager_dataset.py` (UPDATED):**
    *   Dataset examples updated to reflect the Task Manager's new initial interaction flow (e.g., asking for project name, listing the 8 required files if prompted).


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
├── .cursor/
│   └── rules/
│       └── read-project-memories.mdc
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── checks.yml
├── Makefile
├── README.md
├── agent_memories/
│   └── grumpy/
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml
├── scripts/
│   └── generate_project_memory.sh
├── src/
│   ├── agent_template/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── configuration.py
│   │   ├── graph.py
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
│   │   ├── config.py
│   │   ├── graph.py
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
│   │   ├── __init__.py
│   │   ├── configuration.py      # REVISED: Subclasses BaseConfiguration, specific model and prompt
│   │   ├── graph.py              # REVISED: Implements TaskManagerGraph(AgentGraph), new logic
│   │   ├── prompts.py            # REVISED: Major update to system prompt, new workflow, 8 input files, markdown outputs
│   │   ├── state.py              # (No explicit change in PR, assumed standard)
│   │   ├── tools.py              # (Uses file system tools bound in graph)
│   │   └── volume/               # NEW: Directory for Task Manager project inputs
│   │       └── api_rust/         # NEW: Example project input files
│   │           ├── featuresContext.md      # NEW
│   │           ├── progress.md             # NEW
│   │           ├── projectRequirements.md  # NEW
│   │           ├── projectbrief.md         # NEW
│   │           ├── securityContext.md      # NEW
│   │           ├── systemPatterns.md       # NEW
│   │           ├── techContext.md          # NEW
│   │           └── testingContext.md       # NEW
│   └── tester/
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py # UPDATED: Reflects new TM interaction
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py
    │   ├── eval_coder.py
    │   ├── test_graph.py
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py
    │   ├── test_requirement_gatherer.py
    │   ├── test_task_manager.py    # UPDATED: Uses new TaskManagerGraph
    │   └── test_tester_agent.py
    ├── testing/
    │   ├── __init__.py
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py
```
