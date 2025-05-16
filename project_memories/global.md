# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is now `langmem`, providing semantic search capabilities over stored memories, replacing the previous conceptual Markdown-based "Memory Bank" and direct `upsert_memory` tool usage for agents based on the template. Agents like Task Manager now also explicitly use a `store` for memory retrieval.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools or custom tools like `file_dump`, or agent-specific tools like the Requirement Gatherer's `memorize` and `human_feedback`, or file system tools like Task Manager's `read_file`, `create_file`, `list_files`).
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols.
6.  **Configuration Management:** Agents have configurable parameters, including LLM models, system prompts, and memory settings (e.g., `use_static_mem`). This is managed via:
    *   `Configuration` dataclasses from `agent_template`.
    *   A common `BaseConfiguration` in `src/common/config.py`.
    *   Agent-specific `Configuration` dataclasses (e.g., in `src/orchestrator/configuration.py`, `src/requirement_gatherer/configuration.py`, `src/task_manager/configuration.py`) that subclass `BaseConfiguration`.
    *   A new `AgentConfiguration` from `src/common/configuration.py` (implied) used by the Coder agent.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents, typically managed via the `Agent` class and `SemanticMemory` component for agents following the `agent_template`. Other agents like Requirement Gatherer or Task Manager might implement memory tools or direct store interaction differently.
9.  **`AgentGraph` (NEW):** A common base class (`src/common/graph.py`) for defining agent graphs, promoting modularity. Used by Orchestrator, Requirement Gatherer, Coder, and now Task Manager. Its `__init__` method takes an agent-specific configuration (e.g., `base_config: BaseConfiguration` for Orchestrator/Requirement Gatherer/Task Manager, or `name: str, agent_config: AgentConfiguration` for Coder), and optional `checkpointer` and `store`, suggesting an evolving or flexible signature.


## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence, particularly for the "Cursor" idea. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and custom tools/direct store access):** The project has integrated the `langmem` library to provide a more robust and queryable semantic memory system for agents based on the `agent_template`. These agents utilize `langmem` tools for storing and retrieving memories.
Other agents, like the Requirement Gatherer, now use custom tools (e.g., `memorize`) that might interact with the same underlying storage mechanism but are defined and invoked differently within their specific graph structure. The Task Manager now also directly interacts with a `store` (e.g., `langmem`'s `BaseStore`) to retrieve contextual memories using `store.asearch`.

*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`).
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`. Task Manager retrieves memories from `("memories", user_id)`.
*   **Tools:**
    *   `agent_template` based agents: Use `langmem`-provided tools (`manage_memory`, `search_memory`) via `SemanticMemory`. A custom `memory_dump` tool is also available.
    *   Requirement Gatherer: Uses a custom `memorize` tool (defined in `src/requirement_gatherer/tools.py`, refactored from a previous `upsert_memory` function in the same file) for storing memories.
*   **Static Memories:** The concept of static, pre-loaded knowledge persists. JSON files in `.langgraph/static_memories/` can be loaded into the `BaseStore` under a static namespace if `use_static_mem` is enabled in the agent's configuration.
*   **Shift:** The shift moves from human-readable Markdown files as the primary memory source to a database/store queried semantically via tools or direct access. The core principle of externalized memory remains, but the implementation mechanism has evolved. The specific file structure (`projectbrief.md`, `productContext.md`, etc.) described previously is not directly implemented by the `langmem` system, although the *types* of information they represent might be stored as individual memories. However, the Task Manager now expects a specific set of input markdown files (e.g., `projectRequirements.md`, `techContext.md`) as its primary input, which it reads using file system tools.


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
    *   **debugpy:** (NEW) Development dependency for remote debugging support.
    *   **CI Pipeline (`.github/workflows/checks.yml`):** Runs linting (Ruff, codespell), unit tests (`make test_unit`), and Coder integration tests (`make test_coder`). The Coder tests job requires `GOOGLE_API_KEY` as a secret.
*   **Version Control:** Git.
*   **LLM Models:**
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default updated to `gemini-2.5-flash-preview-04-17`). Orchestrator and Requirement Gatherer default to `google_genai:gemini-2.0-flash` via `BaseConfiguration`. Task Manager defaults to `google_genai:gemini-2.5-flash-preview-04-17`.
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

**4.2. `AgentGraph` based Architecture (NEW - e.g., Orchestrator, Requirement Gatherer, Coder, Task Manager)**

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
*   **`src/common/configuration.py` (NEW - Implied by PR):**
    *   Implied new module defining `AgentConfiguration`. This configuration type is used by the Coder agent when initializing its `AgentGraph` subclasses. Its specific structure and relationship to `BaseConfiguration` (from `common.config.py`) are not detailed in PR#79.
*   **`src/common/graph.py` (NEW):**
    *   Defines an abstract base class `AgentGraph(ABC)`.
    *   `__init__(...)`: Initializes the graph. The constructor signature appears to be flexible or evolving:
        *   Older agent patterns (Orchestrator, Requirement Gatherer, Task Manager) initialize `AgentGraph` subclasses passing their specific configuration which is a subclass of `BaseConfiguration` (from `src/common/config.py`), effectively using `base_config`.
        *   Newer usage (e.g., Coder agent as per PR#79) involves passing `name: str` and `agent_config: AgentConfiguration` (from `src/common/configuration.py`) to the `AgentGraph` constructor.
        *   The constructor also takes optional `checkpointer` and `store`.
    *   `create_builder() -> StateGraph` (abstract method): To be implemented by subclasses to define the graph.
    *   `compiled_graph`: Property to get or compile the graph.
    *   `ainvoke(state, config)`: Invokes the compiled graph, merging instance config with call-time config.

Agents like Orchestrator, Requirement Gatherer, Coder, and Task Manager subclass `AgentGraph` and define their specific configurations and graph structures. Graph construction is more modular, often using factory functions or direct builder methods.


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
*   **Role:** Expert software engineer responsible for architecting a project, not writing code. Receives project needs, coordinates other AI agents. Manages project documentation and defines tasks for other agents. Its output is now used as input for the Task Manager.
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
*   **Architecture:** Now refactored to use the `AgentGraph` pattern for its core graph definitions (`CoderNewPRGraph`, `CoderChangeRequestGraph`).
*   **Graph Logic (`src/coder/graph.py`):**
    *   The previous configuration functions (`coder_new_pr_config`, `coder_change_request_config`) have been replaced by `AgentGraph` subclasses: `CoderNewPRGraph` and `CoderChangeRequestGraph`.
    *   These classes define configurations for different coding tasks (new PRs, modifying existing PRs).
    *   `__init__(self, *, github_tools: List[Tool], agent_config: Optional[AgentConfiguration] = None, checkpointer: Optional[Checkpointer] = None, store: Optional[BaseStore] = None)`: Constructor for these graph classes. `agent_config` is of type `AgentConfiguration` from `common.configuration` (a new implied module/class). They are initialized with a list of GitHub tools.
    *   `create_builder(self) -> StateGraph`: Implements the abstract method from `AgentGraph` to define the specific graph structure, reusing the logic from the former `coder_*_config()` functions for graph building.
    *   The `coder_change_request_config()` logic (now part of `CoderChangeRequestGraph`) allows the agent to use the `get_pull_request_head_branch` tool.
    *   The `CallModel` class and `_graph_builder` helper function are retained for internal graph construction within the `create_builder` methods.
    *   `__all__` in `src/coder/graph.py` is updated to export the new class names: `CoderNewPRGraph` and `CoderChangeRequestGraph`.
*   **Prompts (`src/coder/prompts.py`):**
    *   `CHANGE_REQUEST_SYSTEM_PROMPT`: Updated to instruct the agent that when implementing changes on an existing pull request, it will be given the PR number and needs to work on the PR's head branch. It should sync with the latest changes on the PR's head branch and submit changes there.
*   **Tools:**
    *   Utilizes a suite of GitHub tools provided by `src/common/components/github_tools.py`. This suite is configured via the `GITHUB_TOOLS` list in the same file.
    *   A new tool `get_pull_request_head_branch` (implemented as `GetPullRequestHeadBranch` class) has been added to this suite. This tool allows the agent to fetch the head branch name of a pull request given its number. It is available in both live (via `GitHubAPIWrapper`) and mock (via `MockGithubApi`) environments.
    *   The mock GitHub API (`src/common/components/github_mocks.py`) has been updated:
        *   The `get_pull_request` method now returns a simplified dictionary containing essential PR details (title, number, body, comments, commits).
        *   A `get_pull_request_head_branch` method was added to support mocking the new tool.
*   **`lg_server.py` (`src/coder/lg_server.py`):**
    *   Updated to import and instantiate `CoderNewPRGraph` and `CoderChangeRequestGraph` to obtain compiled graphs for serving.
*   (Other files like `__init__.py`, `mocks.py`, `state.py`, `tools.py` specific to the coder, and `README.md` are as previously described in the project structure, if detailed.)

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
*   **Role:** Responsible for project planning based on input documentation (likely from Architect). It splits the project into tasks, creates individual task files, and generates a roadmap.
    *   Workflow:
        1.  Receives a `project_name`.
        2.  Validates the project directory and the presence of 8 required input files (e.g., `projectRequirements.md`, `techContext.md`, `systemPatterns.md`, etc. - see `prompts.py` for full list). Example input files are available in `src/task_manager/volume/api_rust/`.
        3.  Analyzes these files.
        4.  Creates engineering tasks (6-14 hours each) as individual Markdown files in a `planning/` subdirectory within the project's volume.
        5.  Generates a `roadmap.md` file in the `planning/` subdirectory, organizing tasks week by week for a team of 1 engineer.
*   **Architecture:** Refactored to use the `AgentGraph` pattern. `TaskManagerGraph` in `src/task_manager/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/task_manager/configuration.py`):**
    *   Defines its own `Configuration` dataclass, subclassing `common.config.BaseConfiguration`.
    *   `task_manager_system_prompt: str = prompts.SYSTEM_PROMPT`.
    *   `model: str = "google_genai:gemini-2.5-flash-preview-04-17"` (defined as `TASK_MANAGER_MODEL`).
*   **Graph Logic (`src/task_manager/graph.py`):**
    *   `TaskManagerGraph` class initializes with `base_config`, `checkpointer`, and `store`.
    *   `create_builder` method defines the graph structure.
    *   A factory function `_create_call_model` creates the main model-calling node:
        *   Retrieves contextual memories from the `store` using `store.asearch(("memories", user_id), query=...)`.
        *   Formats these memories (as `user_info`) and the current `time` into the system prompt.
        *   Invokes an LLM bound with tools: `read_file`, `create_file`, `list_files`.
        *   Sets `recursion_limit` for the LLM call to `100` (`TASK_MANAGER_RECURSION_LIMIT`).
    *   A `ToolNode` is used for executing the file system tools.
    *   The graph flow is `START` -> `call_model` -> (conditional) `tools` -> `call_model` or `END`.
*   **State (`src/task_manager/state.py`):** Uses the standard `State` object with `messages` to track conversation history.
*   **Tools (`src/task_manager/tools.py`):** Utilizes `read_file`, `create_file`, and `list_files` tools (likely common or defined within `task_manager.tools`).
*   **Prompts (`src/task_manager/prompts.py`):**
    *   `SYSTEM_PROMPT` has been significantly REVISED to reflect the new two-stage workflow (task creation and planning), new input file requirements, output format (individual markdown task files and `roadmap.md`), and task splitting guidelines.
    *   Specifies a team size of 1 engineer and task sizing of 6-14 hours.
    *   Details the required input files: `projectRequirements.md`, `techContext.md`, `systemPatterns.md`, `testingContext.md`, `projectbrief.md`, `featuresContext.md`, `securityContext.md`, `progress.md`.
    *   Details the output structure: individual task files (e.g., `task-01-short-title.md`) and `roadmap.md` in a `planning/` subfolder.
*   **Input:** Takes a `project_name` as initial input. It is expected to use output from the Architect agent, which should ensure the required project files are available in `src/task_manager/volume/[project_name]/`.
*   **Output:**
    *   A `planning/` subfolder within the project's directory (`src/task_manager/volume/[project_name]/planning/`).
    *   Individual Markdown files for each task (e.g., `task-01-setup-scaffolding-dependencies.md`).
    *   A `roadmap.md` file detailing the task execution plan.


## 6. Testing Framework (`tests/`)

*   **`tests/integration_tests/test_orchestrator.py`:**
    *   Updated to use the new `OrchestratorGraph` for testing.
*   **`tests/integration_tests/test_requirement_gatherer.py`:**
    *   Updated to use the new `RequirementsGathererGraph`.
    *   Still uses `create_async_graph_caller` and `LLMJudge` for evaluation against LangSmith datasets.
*   **`tests/integration_tests/test_coder.py`:**
    *   Updated to use `CoderNewPRGraph` and `CoderChangeRequestGraph` for instantiating the Coder agent in tests.
    *   Added a new test `test_coder_changes_server_port_on_existing_pr`. This test verifies that the Coder agent, using `CoderChangeRequestGraph` (which wraps `coder_change_request_config`), correctly applies changes to the head branch of an existing pull request. It utilizes the `MockGithubApi` for setting up the test scenario.
    *   These tests are now executed as part of the CI pipeline in a dedicated "Coder Tests" job (defined in `.github/workflows/checks.yml`), requiring the `GOOGLE_API_KEY` secret.
*   **`tests/integration_tests/eval_coder.py`:**
    *   Updated to use `CoderNewPRGraph` for agent instantiation during evaluation.
*   **`tests/integration_tests/test_task_manager.py`:**
    *   Updated to use the new `TaskManagerGraph` for testing.
    *   Uses `TASK_MANAGER_MODEL` (`google_genai:gemini-2.5-flash-preview-04-17`).
    *   Uses a specialized `create_task_manager_graph_caller` for invoking the graph.
    *   Continues to use `LLMJudge` for evaluation against LangSmith datasets.
*   **`tests/datasets/task_manager_dataset.py`:**
    *   Dataset examples updated to reflect the Task Manager's new initial interaction flow (e.g., asking for project name, listing required files if not found or if user asks).
*   **`tests/unit_tests/test_configuration.py`:**
    *   The previous test `test_configuration_from_none()` related to `orchestrator.configuration.Configuration` is removed as that file is deleted. A dummy test `test_foo()` might be present.
*   **`src/orchestrator/test.py` (Local test script):**
    *   Updated to instantiate `OrchestratorGraph` using `AgentsConfig` and `BaseConfiguration`.
    *   Demonstrates setting `agents_config.requirements.use_stub = False` and `agents_config.requirements.use_human_ai = True`.


## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`)

*   **Development Workflow & Build:**
    *   **Make:** Used as a task runner to automate common commands.
        *   `make run`: (UPDATED) Now includes `--debug-port 2025` to enable remote debugging by default when running `langgraph dev`.
    *   **gcloud:** Deployment of services.
    *   **Remote Debugging:** (NEW) Supported via `debugpy`. A VSCode launch configuration (`.vscode/launch.json`) is provided to attach a remote debugger to the process started by `make run`.
*   **Make:** Used as a task runner to automate common commands. New targets include:
    *   `make test_coder`: Runs Coder integration tests (`tests/integration_tests/test_coder.py`).
*   **CI (`.github/workflows/checks.yml`):**
    *   The CI pipeline includes jobs for:
        *   Linting (Ruff, codespell)
        *   Unit tests (`make test_unit`)
        *   Coder integration tests (`make test_coder`), which requires the `GOOGLE_API_KEY` secret.
*   **Ruff Linting:** `pyproject.toml` updated with per-file ignores for `T201` (print statements) in `src/orchestrator/{graph,test}.py` and `src/requirement_gatherer/graph.py` and `src/requirement_gatherer/tools.py`.
*   **Project Memory Update Script (`scripts/update_project_memory_from_pr.sh`):** The LLM generation parameters (`temperature` from `0.2` to `0.1`, `topK` from `40` to `20`, `topP` from `0.95` to `0.90`) used by this script (which updates this condensed memory based on PRs) were adjusted to reduce output randomness.


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/                      # NEW: Cursor specific rules
│   └── rules/                    # NEW
│       └── read-project-memories.mdc # NEW: Rule to always read project_memories
├── .env.example
├── .gitignore
├── .vscode/                      # NEW
│   └── launch.json               # NEW: VSCode launch configuration for remote debugging
├── .github/
│   └── workflows/
│       └── checks.yml
├── Makefile                      # UPDATED: 'make run' includes --debug-port
│       └── checks.yml            # UPDATED: Added Coder Tests job
├── README.md
├── agent_memories/
│   └── grumpy/
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml                # UPDATED: Ruff per-file ignores, debugpy dependency
├── scripts/
│   └── generate_project_memory.sh
│   └── update_project_memory_from_pr.sh  # UPDATED: LLM generation parameters
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
│   │   ├── graph.py              # UPDATED: Refactored to use AgentGraph subclasses (CoderNewPRGraph, CoderChangeRequestGraph)
│   │   ├── lg_server.py          # UPDATED: Uses new Coder AgentGraph classes
│   │   ├── mocks.py
│   │   ├── prompts.py            # UPDATED: CHANGE_REQUEST_SYSTEM_PROMPT modified
│   │   ├── state.py
│   │   ├── tools.py
│   │   └── README.md
│   ├── common/
│   │   ├── components/
│   │   │   ├── github_mocks.py   # UPDATED: Mock API updated for new tool and PR info
│   │   │   ├── github_tools.py   # UPDATED: Added GetPullRequestHeadBranch tool
│   │   │   └── memory.py
│   │   ├── config.py             # REVISED: Defines BaseConfiguration
│   │   ├── configuration.py      # NEW - Implied: Defines AgentConfiguration used by Coder
│   │   ├── graph.py              # REVISED: AgentGraph __init__ updated (flexible signature)
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
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Refactored to subclass BaseConfiguration, new model default
│   │   ├── graph.py              # UPDATED: Refactored to use AgentGraph, memory retrieval, new recursion limit
│   │   ├── prompts.py            # UPDATED: Major revision to system prompt, new workflow, inputs, outputs
│   │   ├── state.py              # (Assumed to be standard State, no changes in PR diff)
│   │   ├── tools.py              # (Assumed to use existing file system tools, no changes in PR diff)
│   │   └── volume/               # NEW - Example input files
│   │       └── api_rust/         # NEW
│   │           ├── featuresContext.md
│   │           ├── progress.md
│   │           ├── projectRequirements.md
│   │           ├── projectbrief.md
│   │           ├── securityContext.md
│   │           ├── systemPatterns.md
│   │           ├── techContext.md
│   │           └── testingContext.md
│   └── tester/
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py # UPDATED: Reflects new Task Manager interaction
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py           # UPDATED: New test added for PR head branch changes; uses new Coder AgentGraph classes; now run in CI
    │   ├── eval_coder.py           # UPDATED: Uses new Coder AgentGraph class
    │   ├── test_graph.py
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py    # UPDATED: Uses new OrchestratorGraph
    │   ├── test_requirement_gatherer.py # UPDATED: Uses new RequirementsGathererGraph
    │   ├── test_task_manager.py    # UPDATED: Uses new TaskManagerGraph
    │   └── test_tester_agent.py
    ├── testing/
    │   ├── __init__.py
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py   # REVISED: Old test removed, may contain dummy test
```
