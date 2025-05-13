# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager) working collaboratively.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is now `langmem`, providing semantic search capabilities over stored memories, replacing the previous conceptual Markdown-based "Memory Bank" and direct `upsert_memory` tool usage for agents based on the template.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory (using `langmem` tools or custom tools like `file_dump`).
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols.
6.  **Configuration Management:** Agents have configurable parameters, including LLM models, system prompts, and memory settings (e.g., `use_static_mem`), managed via `Configuration` dataclasses.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.
8.  **`langmem` Integration:** Provides semantic memory capabilities (storage, search) for agents, typically managed via the `Agent` class and `SemanticMemory` component.


## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence, particularly for the "Cursor" idea. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem`):** The project has integrated the `langmem` library to provide a more robust and queryable semantic memory system. Agents based on the `agent_template` now utilize `langmem` tools for storing and retrieving memories.

*   **Storage:** Memories are stored in a `BaseStore` (e.g., `InMemoryStore` configured with embeddings like `GoogleGenerativeAIEmbeddings`).
*   **Namespace:** Memories are typically namespaced by `("memories", "semantic", user_id)` or `("memories", "static", user_id)`.
*   **Tools:** Agents use `langmem`-provided tools (`manage_memory`, `search_memory`) for interaction, often wrapped within the `SemanticMemory` component (`src/common/components/memory.py`). A custom `memory_dump` tool is also available.
*   **Static Memories:** The concept of static, pre-loaded knowledge persists. JSON files in `.langgraph/static_memories/` can be loaded into the `BaseStore` under a static namespace if `use_static_mem` is enabled in the agent's configuration.
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
*   **Version Control:** Git.
*   **LLM Models:**
    *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default updated to `gemini-2.5-flash-preview-04-17`).
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning.


## 4. General Agent Architecture (based on `src/agent_template/` and common patterns)

Most agents in AI Nexus follow a common structural and operational pattern, largely derived from `src/agent_template/`. *Note: Some agents, like the Tester, Coder, or Task Manager, may deviate significantly from this template's graph logic or tool usage.*

*   **Typical Agent Directory Structure:**
    *   `__init__.py`: Exposes the agent's graph.
    *   `agent.py`: **NEW:** Contains the `Agent` class handling LLM interaction and memory integration.
    *   `configuration.py`: Defines agent-specific configurable parameters.
    *   `graph.py`: Contains the LangGraph `StateGraph` definition, typically using the `Agent` class.
    *   `prompts.py`: Stores default system prompts and potentially other prompts.
    *   `state.py`: Defines the `State` dataclass for the agent's graph.
    *   `tools.py`: Defines utility tools (e.g., `file_dump`). Memory tools are now managed by the `Agent` class via `SemanticMemory`.
    *   `utils.py`: Utility functions (often moved to `src/common/utils/`).

*   **`configuration.py` (Typical Structure - `src/agent_template/configuration.py`):**
    ```python
    from dataclasses import dataclass, field
    from typing import Annotated, Any
    from langchain_core.runnables import RunnableConfig
    from . import prompts

    AGENT_NAME = "base_agent" # Example agent name

    @dataclass(kw_only=True)
    class Configuration:
        """Main configuration class for the memory graph system."""
        user_id: str = "default_user" # Default user ID
        model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
            default="google_genai:gemini-2.5-flash-preview-04-17" # Updated default model
        )
        system_prompt: str = prompts.SYSTEM_PROMPT
        use_static_mem: bool = True # NEW: Flag to control static memory loading

        # Other agent-specific configurations might be added here

        @classmethod
        def from_runnable_config(cls, config: RunnableConfig) -> "Configuration":
            # ... (implementation remains similar)
            ...
    ```

*   **`state.py` (Typical Structure - `src/agent_template/state.py`):**
    ```python
    import logging
    from dataclasses import dataclass, field
    from typing import Annotated, List
    from langgraph.graph.message import AnyMessage, add_messages

    logger = logging.getLogger(__name__)

    @dataclass(kw_only=True)
    class State:
        """Main graph state."""
        messages: Annotated[List[AnyMessage], add_messages] = field(default_factory=list)
        user_id: str = "default" # NEW: User ID for memory management
    ```

*   **`agent.py` (NEW - `src/agent_template/agent.py`):**
    *   Defines an `Agent` class responsible for LLM interaction and memory management.
    *   `__init__(config: Configuration)`: Initializes the LLM based on `config.model`. Sets up tool dictionary. Initializes `SemanticMemory` if needed. Sets `user_id`.
    *   `initialize(config: Configuration)`: Initializes `SemanticMemory` (from `src/common/components/memory.py`) using `agent_name` and `config`. Gets memory tools (`manage_memory`, `search_memory`) and utility tools (`file_dump`). Binds all tools to the LLM.
    *   `__call__(state: State, config: RunnableConfig)`: The main method called by the graph node. Ensures the agent is initialized. Ensures `user_id` is present in `config["configurable"]` for `langmem` tools. Constructs messages (including system prompt). Invokes the LLM with messages and tools. Returns updated messages.
    *   `get_tools() -> List[Tool]`: Returns all bound tools (memory + utility).

*   **`graph.py` (Core Logic - Revised Flow from `src/agent_template/graph.py`):**
    *   **`graph_builder(config: Configuration) -> StateGraph`:**
        *   Creates a `StateGraph(State)`.
        *   Instantiates the `Agent` class: `agent = Agent(config)`.
        *   Initializes the agent: `agent.initialize(config)`.
        *   Adds the main agent node: `builder.add_node("call_model", agent.__call__)`.
        *   Adds a `ToolNode` to execute tool calls: `tool_node = ToolNode(agent.get_tools(), name="tools")`, `builder.add_node("tools", tool_node)`.
        *   Sets the entry point: `builder.add_edge("__start__", "call_model")`.
        *   Adds conditional routing based on tool calls: `builder.add_conditional_edges("call_model", tools_condition)`. `tools_condition` is a LangGraph helper that checks for tool calls in the last message.
        *   Routes tool execution back to the model: `builder.add_edge("tools", "call_model")`.
        *   Routes non-tool responses to the end: `builder.add_edge("call_model", END)`.
    *   **Compilation:**
        *   A default graph instance is compiled using the builder: `graph = graph_builder(default_config).compile()`.
        *   The old logic involving manual memory retrieval (`store.asearch`), formatting memories into the prompt, and the separate `store_memory` node is **removed** and replaced by the `Agent` class logic using `langmem` tools and the `ToolNode`.

*   **`tools.py` (Utility Tools - `src/agent_template/tools.py`):**
    *   **`create_file_dump_tool() -> Tool`:**
        *   Defines and returns a `Tool` named `file_dump`.
        *   Function signature: `file_dump(content: str, output_path: str, filename: Optional[str] = None) -> bool`.
        *   Purpose: Writes arbitrary `content` string to a specified `filename` within the `output_path` directory. Creates the directory if needed. Returns `True` on success, `False` on failure.
    *   **`upsert_memory` tool is REMOVED.** Memory operations are handled by `langmem` tools (`manage_memory`, `search_memory`) provided via `SemanticMemory`.

*   **`memory.py` (`src/agent_template/memory.py`):**
    *   This file has been **DELETED**. Static memory loading logic is now part of `src/common/components/memory.py`.

*   **`src/common/components/memory.py` (NEW):**
    *   **`SemanticMemory` Class:**
        *   Encapsulates `langmem` functionality.
        *   `__init__(agent_name, store, config)`: Initializes with agent name (for namespacing), an optional `BaseStore`, and configuration.
        *   `initialize(config)`: Creates a `BaseStore` (using `create_memory_store`) if not provided. Loads static memories using `load_static_memories` if `config.use_static_mem` is true.
        *   `get_tools()`: Returns a list of `langmem` tools (`manage_memory`, `search_memory`) and a custom `memory_dump` tool, configured for the agent's namespace and store.
    *   **`load_static_memories(store, user_id)`:** Loads memories from JSON files in `.langgraph/static_memories/` into the provided `store` under the namespace `("memories", "static", user_id)`.
    *   **`create_memory_tools(namespace, store)`:** Creates the list of memory tools (`manage_memory`, `search_memory`, `memory_dump`). `manage_memory` uses `CategoryMemory` schema (`content`, `category`, `timestamp`). `memory_dump` writes all memories across namespaces to a JSON file.
    *   **`create_memory_store()`:** Creates an `InMemoryStore` configured with `GoogleGenerativeAIEmbeddings`.
    *   **`CategoryMemory(BaseModel)`:** Pydantic model defining the structure for memories stored via `manage_memory` tool (`content: str`, `category: Literal["knowledge", "rule", "procedure"]`, `timestamp: str`).

*   **`prompts.py` (`src/agent_template/prompts.py`):**
    *   `SYSTEM_PROMPT` updated to instruct the agent to inform the user when memories are retrieved: `"When using the memory tools for search, always tell the user that those memories were retrieved from my semantic memory store like saying 'I retrieved the following memories from my semantic memory store: {memories}'"`


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`)
*   (No changes mentioned in PR - likely still uses its custom `Delegate` and `Memory` tools and stubs, not directly affected by `langmem` integration in the template).

#### 5.2. Architect (`src/architect/`)

*   **Role:** Expert software engineer responsible for architecting a project, not writing code. Receives project needs, coordinates other AI agents. Manages project documentation and defines tasks for other agents.
*   **Key Prompt (`src/architect/prompts/v0.1.md`):** This is a detailed system prompt.
    *   **Identity:** "I am Architect..."
    *   **Core Responsibility:** MUST read ALL files in 'project' folder at the start of EVERY task.
    *   **Core Values:** Research Driven, Technology Selection, Task Definition, Validation and Adjustment, Transparency and Traceability.
    *   **Project Structure Understanding:** Defines a hierarchy of Markdown files it expects and manages within a 'project' folder:
        *   Core Files (Required): `projectbrief.md`, `projectRequirements.md`, `systemPatterns.md`, `techContext.md`, `progress.md`.
        *   Specific Files (Required): `featuresContext.md`, `testingContext.md`, `securityContext.md`. These track current work, changes, next steps, decisions, patterns, learnings for their respective scopes. Tasks need start/finish dates.
        *   `progress.md` is updated last.
        *   Flowchart of file dependencies is provided in the prompt.
    *   **Old Information Management:** Information older than two weeks from task/progress files is moved to `changelog.md`. This file is checked only if prompted with "check changelog".
    *   **Task Allocation:** After reading files and ensuring documentation is up-to-date, the Architect defines the next tasks based on `featuresContext.md`, `testingContext.md`, and `securityContext.md`.
        *   Tasks must be small (couple of hours for a human).
        *   Tasks require thorough explanation, technology list, restrictions, and pointers to relevant code/files.
        *   Tasks are written to `codingTask.md`, `testingTask.md`, and `securityTask.md` respectively.
    *   **Documentation Updates:** Triggered by: new patterns, significant changes, user request "update project" (MUST review ALL files), context clarification. Includes a flowchart for the update process.
*   **`prompts.py` (`src/architect/prompts.py`):**
    *   Reads `src/architect/prompts/v0.1.md`.
    *   Formats it by injecting `user_info` (OS, username, current directory) and current `time`.
*   **`output.py` (`src/architect/output.py`):** Defines Pydantic models for structured output:
    *   `ArchitectAgentTaskOutput`: `id`, `name`, `description`, `task`, `requirement_id`.
    *   `ArchitectAgentQuestionOutput`: `id`, `question`, `context`.
    *   `ArchitectAgentFinalOutput`: Contains lists of questions and tasks. (Note: The graph currently doesn't explicitly parse or bind these models).
*   **Structure:** Follows the `agent_template` pattern with modifications.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`.
    *   `graph.py`: Standard `call_model`, `store_memory`, `route_message` flow. Uses `tools.upsert_memory`.
        *   The `call_model` node now returns `{"messages": [{"role": "assistant", "content": str(msg)}]}`.
    *   `state.py`: Standard `State` with `messages`.
    *   `tools.py`: Defines the standard `upsert_memory` tool.
    *   `utils.py`: Standard `split_model_and_provider`, `init_chat_model`.

#### 5.3. Coder (`src/coder/`)

*   **Role:** Software developer, writes code, interacts with GitHub repositories. The Coder module now provides two distinct agent flows/graphs:
    *   **`coder_new_pr`**: For creating new Pull Requests.
    *   **`coder_change_request`**: For applying changes to existing Pull Requests.
    Each flow has a dedicated system prompt and a specific set of GitHub tools, managed via `CoderInstanceConfig`.
*   **`prompts.py` (`src/coder/prompts.py`):**
    *   `NEW_PR_SYSTEM_PROMPT`: System prompt for the `coder_new_pr` flow. Instructs the agent on creating a new branch (`code-agent-*`) and submitting a PR.
    *   `CHANGE_REQUEST_SYSTEM_PROMPT`: System prompt for the `coder_change_request` flow. Instructs the agent on applying changes to an existing PR branch.
    *   The previous generic `SYSTEM_PROMPT` has been replaced by these more specific prompts.
*   **`tools.py` (`src/coder/tools.py`):**
    *   `GITHUB_TOOLS`: A list of tool names (e.g., `"create_branch"`, `"get_contents"`, `"get_pull_request"`) used to filter tools obtained from `GitHubToolkit` (for real API) or `mock_github_tools`. **Updated** to include tools for PR inspection like `"get_pull_request"` and `"list_pull_requests_files"`.
    *   `get_github_tools(github_source: Union[GitHubAPIWrapper, MockGithubApi]) -> list[Tool]`:
        *   If `github_source` is `MockGithubApi`, calls `mock_github_tools`.
        *   If `github_source` is `GitHubAPIWrapper`, gets tools from `GitHubToolkit.from_github_api_wrapper().get_tools()`.
        *   Applies `make_gemini_compatible` to each tool.
        *   Filters the tools, returning only those whose names are present in the `GITHUB_TOOLS` list.
    *   `mock_github_tools(mock_api: MockGithubApi) -> list[Tool]`:
        *   Creates mocked versions of GitHub tools.
        *   Tools created include: `create_file`, `read_file`, `update_file`, `delete_file`, `create_pull_request`, `create_a_new_branch`, `set_active_branch`.
        *   The tool for getting directory/file contents is named **`get_files_from_a_directory`** (wraps `mock_api.get_files_from_directory`).
        *   **NEW Mocked Tools:** `get_pull_request`, `list_pull_requests_files` (wrapping corresponding `MockGithubApi` methods).
*   **`mocks.py` (`src/coder/mocks.py`):**
    *   `MockGithubApi`:
        *   Methods: `set_active_branch`, `create_branch`, `_get_files_recursive`, `get_files_from_directory`, `create_pull_request`, `create_file`, `update_file`, `delete_file`, `read_file`.
        *   **NEW Methods:** `get_pull_request`, `list_pull_requests_files`.
*   **`graph.py` (`src/coder/graph.py`):**
    *   Defines `CoderInstanceConfig(Dataclass)`:
        *   Attributes: `name: str`, `system_prompt: str`, `github_tools: List[str]` (list of specific tool names for this instance).
        *   Methods:
            *   `graph_builder(self, github_toolset: list[Tool]) -> StateGraph`: Builds a LangGraph `StateGraph` using the toolset (after filtering by `self.github_tools`) and `self.system_prompt`.
            *   `filter_tools(self, tools: List[Tool]) -> List[Tool]`: Filters a provided list of `Tool` objects to include only those whose names are specified in `self.github_tools`. Asserts that the number of filtered tools matches expectations.
    *   Factory functions returning `CoderInstanceConfig`:
        *   `coder_new_pr_config()`: Config for "new PR" flow. `github_tools` include: `"set_active_branch"`, `"create_a_new_branch"`, `"get_files_from_a_directory"`, `"create_pull_request"`, `"create_file"`, `"update_file"`, `"read_file"`, `"delete_file"`. Uses `NEW_PR_SYSTEM_PROMPT`.
        *   `coder_change_request_config()`: Config for "change request" flow. `github_tools` include: `"set_active_branch"`, `"get_files_from_a_directory"`, `"create_file"`, `"update_file"`, `"read_file"`, `"delete_file"`, `"get_pull_request"`, `"list_pull_requests_files"`. Uses `CHANGE_REQUEST_SYSTEM_PROMPT`.
    *   `_graph_builder(github_toolset: list[Tool], system_prompt: str) -> StateGraph` (renamed from top-level `graph_builder`):
        *   Constructs the `StateGraph(State)`.
        *   Initializes LLM (e.g., `gemini-2.0-flash`).
        *   `CallModel` class:
            *   `__init__(self, github_tools: list[Tool], system_prompt: str)`: Now takes `system_prompt` as an argument.
            *   `__call__(self, state: State) -> dict`: Constructs messages list including the specific `system_prompt`. Binds the provided `github_tools` to the LLM.
        *   `ToolNode(tools=github_toolset)`: Handles execution of GitHub tool calls.
        *   Flow: `__start__` -> `call_model` -> (conditional: `tools` if tool call, `END` otherwise) -> `call_model` (if from `tools`).
*   **`lg_server.py` (`src/coder/lg_server.py`):**
    *   Exposes two compiled graph instances for LangGraph Server:
        *   `graph_new_pr = coder_new_pr_config().graph_builder(github_tools).compile()`
        *   `graph_change_request = coder_change_request_config().graph_builder(github_tools).compile()`
    *   `get_github_source() -> Union[GitHubAPIWrapper, MockGithubApi]`:
        *   Dynamically selects the GitHub tool source.
        *   Uses `GitHubAPIWrapper` if `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, and `GITHUB_REPOSITORY` environment variables are set (logs "Using live GitHub API toolkit").
        *   Otherwise, falls back to `MockGithubApi` (logs "Using mock GitHub API toolkit").
    *   `github_tools` are initialized using `get_github_tools(get_github_source())`.
*   **`state.py` (`src/coder/state.py`):**
    *   `class State(TypedDict): messages: Annotated[list[AnyMessage], add_messages]` (Remains the same).
*   **`README.md` (`src/coder/README.md`):** (No changes mentioned in PR, assumed same).

#### 5.4. Code Reviewer (`src/code_reviewer/`)
*   **Role:** Expert code reviewer, makes suggestions to maintain a high-quality codebase. Does NOT modify code/assets directly.
*   **`system_prompt.md` (`src/code_reviewer/system_prompt.md`):** (Remains the same).
*   **Structure:** Follows the `agent_template` pattern.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`. Default model likely updated. Includes `use_static_mem`.
    *   `graph.py`: Now uses the `Agent` class, `ToolNode`, and `tools_condition` flow. Relies on `langmem` tools and `file_dump` provided by the `Agent` class, replacing `upsert_memory`.
    *   `state.py`: Standard `State` with `messages` and `user_id`.
    *   `tools.py`: Defines utility tools like `file_dump`. `upsert_memory` is removed. Memory tools come from `Agent`.
    *   `agent.py`: Contains the `Agent` class instance for this agent.

#### 5.5. Tester (`src/tester/`)
*   **Role:** Generates tests based on requirements, asks clarifying questions. Uses structured output. (Note: The Tester agent's graph and tools are distinct from the `agent_template` and do not directly use `langmem` for memory in the same way).
*   **`test-agent-system-prompt.md` (`src/tester/test-agent-system-prompt.md`):** REVISED. The system prompt has been significantly updated to be more succinct, assertive, and provide clearer operational guidelines.
    *   **Core Principle:** ONLY generate tests based on explicit requirements; NEVER invent rules or make assumptions.
    *   **Process:**
        1.  Analyze requirements for completeness.
        2.  ALWAYS ask clarifying questions for undefined behavior *before* test generation.
        3.  Generate tests after clarification, grouped by category, linked to source requirement ID.
    *   **Questioning Guidelines:**
        *   **Ask when:** Field validation rules undefined, error handling unspecified, uniqueness constraints missing, response formats/status codes unclear, edge cases unaddressed, auth/authz ambiguous.
        *   **Do NOT ask when:** Detail is purely internal implementation, question is about non-functional UI styling, or info is inferable from standard API conventions.
        *   **Format:** One specific issue per question, include unique ID referencing the requirement, keep questions short and direct.
    *   **Key Sections Added/Revised:** "Role", "Process", "When to Ask Questions", "Questions Format", "Test Examples", "Workflow Checklist", "Key Rules", "Completion Verification".
    *   **Emphasis:** Rigorous analysis, proactive clarification of ambiguities, and strict adherence to defined requirements.

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`)
*   **Role:** Elicits, clarifies, and refines project goals, needs, and constraints.
*   **`prompts.py` (`src/requirement_gatherer/prompts.py`):** (Remains the same detailed prompt, including mention of `upsert_memory` which is now superseded by `manage_memory`).
*   **Structure:** Based on `agent_template` but with a custom graph.
    *   `configuration.py`: Standard. Default model likely updated. Includes `use_static_mem`.
    *   `graph.py`: The custom graph flow (`call_model`, `store_memory`, `call_evaluator_model`, `human_feedback`) needs adaptation. The `store_memory` node (which previously handled `upsert_memory` calls) would likely be replaced by a `ToolNode` handling `langmem` tool calls (`manage_memory`) generated by `call_model`. The `call_model` node would now be implemented using the `Agent` class. Memory retrieval logic in `call_evaluator_model` would need to use `langmem` search tools or rely on memories retrieved by `call_model`. *Assumption: This agent now uses the `Agent` class and `langmem` tools.*
    *   `state.py`: Standard `State` with `messages` and `user_id`.
    *   `tools.py`: Defines utility tools like `file_dump`. `upsert_memory` is removed. Memory tools come from `Agent`.
    *   `agent.py`: Contains the `Agent` class instance for this agent.

#### 5.7. Grumpy (`src/grumpy/`)
*   **Role:** Analyzes and reviews a provided request (task) related to "designing" or "coding".
*   **Key Memory Files:** (Remain the same).
*   **Structure:** Based on `agent_template`.
    *   `configuration.py`: Includes `system_prompt`, `question_prompt`. Default model likely updated. Includes `use_static_mem`.
    *   `graph.py`: Now uses the `Agent` class, `ToolNode`, and `tools_condition` flow. Relies on `langmem` tools and `file_dump` provided by the `Agent` class, replacing `upsert_memory`. The memory retrieval logic within its `call_model` is replaced by `langmem` search capabilities invoked via tool calls. The `graph_no_memory` variant might still exist or be adapted.
    *   `state.py`: Includes `analysis_question`, `messages`, and `user_id`.
    *   `tools.py`: Defines utility tools like `file_dump`. `upsert_memory` is removed. Memory tools come from `Agent`.
    *   `agent.py`: Contains the `Agent` class instance for this agent.

#### 5.8. Task Manager (`src/task_manager/`) (NEW)
*   **Role:** Manages tasks, initially focused on identifying necessary input documents for its work (e.g., `prd.md`, `techstack.md`, `split_criteria.md`).
*   **Structure:** Appears to follow an older agent structure, not the latest `agent_template` with the `Agent` class and `langmem`.
    *   `configuration.py`:
        *   Defines `TASK_MANAGER_MODEL = "google_genai:gemini-2.5-flash-preview-04-17"`.
        *   Standard `Configuration` dataclass using this model by default.
        *   Imports `prompts` from `task_manager` module.
    *   `graph.py`:
        *   Initializes LLM using `init_chat_model(model=configuration.TASK_MANAGER_MODEL)`.
        *   Defines graph nodes: `call_model`, `store_memory`, `route_message`, `process_tools`.
        *   Likely uses an `upsert_memory` tool via the `process_tools` node and `store_memory` node for memory operations.
        *   Exports `graph` (compiled graph instance) and `builder` (StateGraph builder).
    *   `prompts.py`: Implied to exist within `src/task_manager/` for system/other prompts.
    *   `state.py`: Implied to exist, defining the agent's state (likely including `messages`).
    *   `tools.py`: Implied to exist, likely defining an `upsert_memory` tool.


## 6. Testing Framework (`tests/`)

The project uses `pytest` for testing and integrates with LangSmith for evaluation and dataset management.


*   **Common Test Setup:**
    *   `Client()` from `langsmith` for LangSmith interactions.
    *   `MemorySaver()` from `langgraph.checkpoint.memory` for graph checkpointing.
    *   `InMemoryStore()` from `langgraph.stores.memory` for agent memory during tests.
    *   Graphs are typically compiled with a checkpointer and store: `graph_compiled = graph_builder.compile(checkpointer=memory_saver, store=memory_store)`.
    *   A wrapper function (e.g., `run_graph_with_config` or `call_tester_agent`) is often created to:
        *   TTake a dataset example (and potentially attachments) as input.
        *   Format the input for the graph (e.g., converting to `HumanMessage` lists, injecting attachments as `SystemMessage`s).
        *   Generate a unique `thread_id` (using `uuid.uuid4()`) for state isolation in `RunnableConfig`.
        *   Set necessary configuration like `user_id` and `model`.
        *   Invoke the compiled graph: `await graph_compiled.ainvoke(graph_input, config=config)`.
        *   Extract and format the output (often the content of the last message) for evaluation.
    *   `client.aevaluate()` is used to run evaluations against LangSmith datasets, passing the wrapper function and dataset name/examples.

*   **`tests/datasets/requirement_gatherer_dataset.py`:**
    *   Defines `REQUIREMENT_GATHERER_DATASET_NAME = "Requirement-gatherer-naive-dataset"`.
    *   `create_dataset()` function:
        *   Initializes `Client()`.
        *   Creates a LangSmith dataset using `client.create_dataset()`.
        *   Adds examples (input-output pairs) to the dataset using `client.create_examples()`. Inputs are simple strings, outputs are expected agent responses.

*   **`tests/datasets/coder_dataset.py`:**
    *   Defines `CODER_DATASET_NAME = "coder-test-dataset"`.
    *   Defines input (`CodeEvaluatorInputs`) and reference output (`CodeEvaluatorReferenceOutputs`) structures for Coder evaluation.
    *   `create_dataset()` function:
        *   Initializes `Client()`.
        *   Creates the LangSmith dataset.
        *   Adds examples (input-output pairs) to the dataset.

*   **`tests/datasets/task_manager_dataset.py` (NEW):**
    *   Defines `TASK_MANAGER_DATASET_NAME = "task-manager-requirements"`.
    *   `create_dataset()` function:
        *   Initializes `Client()`.
        *   Creates a LangSmith dataset.
        *   Adds examples to the dataset, focusing on the Task Manager's ability to identify its required input documents (e.g., `prd.md`, `techstack.md`, `split_criteria.md`).

*   **`tests/integration_tests/`:**
    *   **`test_graph.py`:**
        *   `test_memory_storage`: Basic test for the `agent_template` graph's memory storage.
        *   Sends a series of messages.
        *   Checks if memories are saved in `InMemoryStore` under the correct `user_id` and namespace `("memories", user_id)`.
        *   Verifies that memories are not found under an incorrect namespace.
    *   **`test_requirement_gatherer.py`:**
        *   Tests the requirement gatherer agent against the `REQUIREMENT_GATHERER_DATASET_NAME` LangSmith dataset.
        *   Uses `create_async_graph_caller` from `tests.testing` to wrap the agent's graph for evaluation runs.
        *   Employs `LLMJudge` from `tests.testing.evaluators`. It calls the `create_correctness_evaluator` method of `LLMJudge` with `plaintext=True` and a custom, detailed prompt (`REQUIREMENT_GATHERER_CORRECTNESS_PROMPT` defined within the test file) to assess the agent's output against reference data.
        *   The test invokes `client.aevaluate()` with the graph caller, dataset, the configured evaluator, and an updated `experiment_prefix` (e.g., `"requirement-gatherer-gemini-2.5-correctness-eval-plain"`).
        *   Uses `print_evaluation` from `testing.formatter` to display evaluation results, with configurable `Verbosity`.
        *   The previous complex input formatting logic (formerly in a local `run_graph_with_config` function) has been refactored, likely simplified by the use of `create_async_graph_caller`.
    *   **`test_tester_agent.py`:**
        *   Tests the tester agent against `LANGSMITH_DATASET_NAME = "tester-agent-test-dataset"`.
        *   Uses `LLMJudge` from `tests.testing.evaluators` with a custom `CORRECTNESS_PROMPT` (defined in the test file) tailored for evaluating the Tester agent's output (analyzing requirements, asking questions, generating tests).
        *   Uses the `create_async_graph_caller` utility from `tests/testing` to wrap the Tester agent's graph for evaluation.
        *   Runs the evaluation multiple times (`num_repetitions=3`).
    *   **`test_grumpy_agent.py`:**
        *   Tests the grumpy agent against a LangSmith dataset (e.g., `LANGSMITH_DATASET_NAME = "grumpy-failed-questions"`).
        *   Uses `LLMJudge` from `tests.testing.evaluators` to create a `correctness_evaluator` with a specific prompt for judging Grumpy's output.
        *   The `create_graph_caller` utility is used to wrap the Grumpy agent's graph for evaluation.
    *   **`test_coder.py`:**
        *   Contains integration tests for the Coder agent's GitHub interactions using `MockGithubApi`.
        *   Tests now instantiate the graph using `coder_new_pr_config().graph_builder(github_tools).compile()`.
        *   The custom evaluation framework using `openevals` has been moved to `tests/integration_tests/eval_coder.py`.
    *   **`eval_coder.py` (`tests/integration_tests/eval_coder.py`) (NEW):**
        *   Defines a custom evaluation framework for the Coder agent (specifically the `coder_new_pr` flow) using `openevals`.
        *   `EVAL_PROMPT`: A detailed prompt for an LLM judge to review the Coder agent's trajectory (branch creation, code changes vs. expectations).
        *   `Result` TypedDict (`score`, `comment`) for structured LLM judge output.
        *   `judge_llm`: An LLM (e.g., `gemini-2.0-flash`) configured for structured output.
        *   `evaluate_code_scorer`: Async function that formats inputs and invokes the `judge_llm`.
        *   `evaluate_code`: Async function that uses `openevals.utils._arun_evaluator` with `evaluate_code_scorer` to perform evaluation.
        *   `invoke_agent(inputs: CodeEvaluatorInputs) -> dict`:
            *   Sets up `MockGithubApi` with `inputs["starting_code"]`.
            *   Compiles the `coder_new_pr` graph: `coder_new_pr_config().graph_builder(github_tools).compile()`.
            *   Invokes the graph with `inputs["user_input"]`.
        *   `test_coder_run_eval_dataset()`: Pytest async test that runs `langsmith.aevaluate` using `invoke_agent` against the `CODER_DATASET_NAME`, with `evaluate_code` as the evaluator.
    *   **`test_task_manager.py` (NEW):**
        *   Tests the Task Manager agent against the `TASK_MANAGER_DATASET_NAME` LangSmith dataset.
        *   Compiles the Task Manager graph using `graph_builder.compile(checkpointer=MemorySaver())`.
        *   Defines a custom `create_task_manager_graph_caller` function to adapt dataset inputs and invoke the graph.
        *   Uses `LLMJudge().create_correctness_evaluator(plaintext=True)` for evaluation.
        *   Runs `client.aevaluate()` with `num_repetitions=4`.

*   **`tests/testing/__init__.py`:**
    *   `get_logger()`: Utility to create a Python logger with a default format.
    *   `create_async_graph_caller(graph, process_inputs_fn=None, process_outputs_fn=None)`:
        *   A generic async function to create a caller for `graph.ainvoke`.
        *   Handles creating a unique `thread_id` for each call.
        *   Sets default `user_id` and `model` in the config.
        *   Processes input messages (extracting content, wrapping in `HumanMessage`).
        *   Returns the content of the last message from the graph's output.

*   **`tests/testing/evaluators.py`:**
    *   `LLMJudge` class:
        *   Wrapper for using an LLM (default: `gemini-1.5-flash-latest`) as an evaluator.
        *   `__init__(model_name: str = "google_genai:gemini-1.5-flash-latest")`.
        *   `create_llm_as_judge(prompt: str, input_keys: List[str], output_key: str, reference_output_key: str, continuous: bool = True)`:
            *   Creates an evaluator chain using an LLM.
            *   Takes a prompt template, keys for input, output, reference, and a flag for continuous feedback.
        *   `create_correctness_evaluator(plaintext: bool, prompt: str)`: (Method usage seen in PRs)
            *   A specialized method to create a correctness evaluator, likely taking a prompt and a flag for plaintext comparison.
    *   `CORRECTNESS_PROMPT`: A prompt template for an LLM to judge if the `prediction` matches the `reference` output given an `input`.
    *   `correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict)`:
        *   A specific evaluator instance created using `LLMJudge().create_llm_as_judge` (or potentially `LLMJudge().create_correctness_evaluator`) with `CORRECTNESS_PROMPT`.
        *   Compares `outputs['output']` (actual agent response) with `reference_outputs['message']['content']` (expected response from dataset).

*   **Evaluation Approaches:**
    *   **LangSmith Datasets + LLM Judge:** Used for Requirement Gatherer, Tester (simple case), Grumpy, Task Manager. Relies on `client.aevaluate()` and evaluators defined in `tests/testing/evaluators.py`.
    *   **Custom `openevals` Framework:** Implemented in `tests/integration_tests/eval_coder.py` for the Coder agent's `coder_new_pr` flow. Involves custom prompts, input/output structures, and direct use of `openevals` utilities with an LLM judge defined within the test file. The test itself (`test_coder_run_eval_dataset`) uses `langsmith.aevaluate` to run these custom evaluations against a dataset.
*   **`tests/testing/formatter.py` (Implied by PR usage):**
    *   Provides utility functions for formatting and printing evaluation results.
    *   Includes `print_evaluation(results, client, verbosity)` for displaying detailed evaluation outcomes.
    *   May include enums like `Verbosity` to control output detail.

*   **`tests/unit_tests/test_configuration.py`:**
    *   `test_configuration_from_none()`: Basic unit test to check if `Configuration.from_runnable_config()` handles a `None` config correctly, falling back to default values.



## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`)


*   **Environment Management:** `uv` (from Astral) is used for creating virtual environments and installing Python packages.
    *   Run commands within `uv` environment: `uv run -- <CMD>`.
*   **Task Runner:** `Makefile` provides targets for common development tasks:
    *   `make run`: Runs the LangGraph development server (`langgraph dev`).
    *   `make sync`: Synchronizes dependencies (likely `uv pip sync pyproject.toml`).
    *   `make deps`: Installs dependencies (likely `uv pip install -r requirements.txt` or similar, though `pyproject.toml` is primary).
    *   `make clean`: Cleans up build artifacts and caches (`__pycache__`, `.pytest_cache`, etc.).
    *   `make lint`: Runs linters (Ruff: `uv run -- ruff check .`).
    *   `make fmt`: Formats code (Ruff: `uv run -- ruff format .`).
    *   `make spell_check`: Checks for spelling mistakes using `codespell`.
    *   `make spell_fix`: Fixes spelling mistakes using `codespell`.
    *   `make check`: Runs `lint` and `spell_check`.
    *   `make test_unit`: Runs unit tests (`uv run -- pytest tests/unit_tests`).
    *   `make test_integration`: Runs integration tests (`uv run -- pytest tests/integration_tests`).
    *   `make test`: Runs both `test_unit` and `test_integration`.
    *   `make test-grumpy`: Runs Grumpy agent integration tests.
    *   `make test-requirement-gatherer`: Runs Requirement Gatherer integration tests.
    *   `make test-tester`: Runs Tester agent integration tests.
    *   `make test-architect`: Runs Architect agent integration tests.
    *   `make test-task-manager`: Runs Task Manager integration tests (`uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_task_manager.py`). (NEW)
    *   `make set-requirement-dataset`: Creates the Requirement Gatherer LangSmith dataset.
    *   `make set-task-manager-dataset`: Creates the Task Manager LangSmith dataset (`uv run --env-file .env -- python tests/datasets/task_manager_dataset.py`). (NEW)
*   **Configuration:** `.env` file (copied from `.env.example`) for environment variables.
    *   Required for Google AI services: `GOOGLE_API_KEY` (this is the preferred variable). Alternatively, `GEMINI_API_KEY` can be set; scripts will use `GOOGLE_API_KEY` if present, otherwise they will use `GEMINI_API_KEY`.
    *   Optional for Coder agent: `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_REPOSITORY`.
    *   Optional for LangSmith: `LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2`, `LANGCHAIN_ENDPOINT`, `LANGCHAIN_PROJECT`.
*   **CI/CD (GitHub Actions):**
    *   Workflow defined in `.github/workflows/checks.yml`.
    *   Triggers on `push` to `main` and `pull_request` to `main`.
    *   Jobs:
        *   `Lint`: Installs dependencies (`uv pip sync`) and runs `make lint`.
        *   `Spell Check`: Installs `codespell` and runs `make spell_check` on `README.md` and `src/`.
        *   `Unit Tests`: Installs dependencies and runs `make test_unit`.
    *   Integration tests (`make test_integration`) are commented out in the `checks.yml` file, indicating they might be run separately or are pending full CI integration.
*   **LangGraph Studio:**
    *   The project can be opened in LangGraph Studio for visualization, interaction, and debugging.
    *   `langgraph.json` can be used to set the default graph to open in Studio. It now includes entries for the `architect` graph, and **has been updated to reflect the Coder agent's split into `coder_new_pr` and `coder_change_request` graphs.**
    *   The README provides a badge/link to open the project directly in LangGraph Studio using a GitHub URL.
*   **Adding New Agents:**
    1.  Copy the `src/agent_template/` directory and rename it.
    2.  Update package paths within the new agent's files (e.g., imports).
    3.  Add the new agent package to `pyproject.toml` under `[tool.poetry.packages]` or `[project.entry-points."langgraph.graphs"]` if using that mechanism for discovery.
    4.  Add the new agent graph entry to `langgraph.json`.
    5.  Run `make run` and navigate to the new agent in LangGraph Studio.
*   **Memory Exploration:** LangGraph Studio UI allows reviewing saved memories (e.g., by clicking a "memory" button if the store is connected and UI supports it).


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── checks.yml
├── Makefile                      # Task runner (Added test-memory-graph, test-task-manager, set-task-manager-dataset targets)
├── README.md                     # Includes NEW section on using semantic memory
├── agent_memories/               # Agent-specific static memories (e.g., for Grumpy)
│   └── grumpy/
│       ├── review-coding.md      # Context for Grumpy's code review
│       ├── review-designing.md   # Context for Grumpy's design review
│       └── role.md               # Core operational rules and Mermaid diagram for Grumpy
├── langgraph.json                # LangGraph Studio configuration (UPDATED: Coder agent split into coder_new_pr, coder_change_request)
├── project_memories/             # Project-wide standards, global context
│   ├── PRD.md                    # Product Requirements Document: standards, tech stack, goals
│   └── global.md                 # High-level project mission, "Cursor" Memory Bank concept
├── pyproject.toml                # Project metadata, dependencies (for uv/Poetry), package definitions
├── src/                          # Source code for all agents and common utilities
│   ├── agent_template/           # Base template for creating new agents
│   │   ├── __init__.py
│   │   ├── agent.py              # NEW: Agent class handling LLM/memory interaction
│   │   ├── configuration.py      # UPDATED: Added use_static_mem, new default model
│   │   ├── graph.py              # REVISED: Uses Agent class, ToolNode, tools_condition
│   │   ├── memory.py             # DELETED
│   │   ├── prompts.py            # UPDATED: Instructs agent to mention memory retrieval
│   │   ├── state.py              # UPDATED: Added user_id field
│   │   ├── tools.py              # REVISED: Defines file_dump tool, upsert_memory removed
│   │   └── utils.py              # (May be moved/refactored to common)
│   ├── architect/                # Architect agent: manages project design and documentation
│   │   ├── output.py             # Pydantic models for Architect's structured output
│   │   └── prompts/v0.1.md       # Detailed system prompt for Architect (v0.1)
│   ├── code_reviewer/            # Code Reviewer agent: reviews code for quality
│   │   └── system_prompt.md      # System prompt for Code Reviewer
│   ├── coder/                    # Coder agent: writes code, interacts with GitHub (Now split into new_pr and change_request flows)
│   │   ├── __init__.py           # Exports graph_new_pr, graph_change_request
│   │   ├── graph.py              # Defines CoderInstanceConfig, _graph_builder, and config factories for new_pr and change_request flows
│   │   ├── lg_server.py          # NEW: Exposes compiled Coder graphs (graph_new_pr, graph_change_request) for LangGraph Server, handles dynamic GitHub source
│   │   ├── mocks.py              # Mock GitHub API for testing (UPDATED: new mock methods for PR details)
│   │   ├── prompts.py            # UPDATED: NEW_PR_SYSTEM_PROMPT, CHANGE_REQUEST_SYSTEM_PROMPT
│   │   ├── state.py              # Defines Coder agent state
│   │   ├── tools.py              # Defines GitHub tools (UPDATED: new tools for PR details, GITHUB_TOOLS list, get_github_tools function)
│   │   └── README.md             # Setup instructions for GitHub App
│   ├── common/                   # Common utilities shared across agents
│   │   └── utils/                # Shared utility functions
│   ├── grumpy/                   # Grumpy agent: reviews design/coding tasks based on strict rules
│   ├── orchestrator/             # Orchestrator agent: delegates tasks to other agents
│   │   ├── memory/               # Markdown files defining Orchestrator's rules and team
│   │   └── stubs/                # Stub implementations for delegated agent calls (for testing/dev)
│   ├── requirement_gatherer/     # Requirement Gatherer agent: elicits and clarifies requirements
│   ├── task_manager/             # Task Manager agent (NEW - uses older agent structure)
│   │   ├── __init__.py           # (Implied)
│   │   ├── configuration.py      # Defines specific model, standard config
│   │   ├── graph.py              # Uses older graph structure (call_model, store_memory, etc.)
│   │   ├── prompts.py            # (Implied)
│   │   ├── state.py              # (Implied)
│   │   └── tools.py              # (Implied, likely with upsert_memory)
│   └── tester/                   # Tester agent: generates tests based on requirements
│       ├── README.md             # Goal, responsibilities, workflow diagram for Tester
│       ├── configuration.py      # Default model changed to gemini-2.0-flash-lite
│       ├── graph.py              # REVISED: Uses structured output, multi-stage workflow (analyze/generate), no memory store interaction
│       ├── output.py             # Pydantic models for Tester's structured output
│       ├── state.py              # Standard state (messages)
│       ├── test-agent-system-prompt.md # REVISED: System prompt made more succinct, assertive, with clearer guidelines on asking questions, and new workflow/rule sections.
│       ├── test-prompts/         # Example requirements for Tester
│       │   ├── web-api-simple.md # NEW: Simpler web API example
│       │   └── web-api.md
│       ├── tools.py              # Defines upsert_memory, but NOT used by current graph.py
│       └── utils.py              # Standard utils
└── tests/                        # Automated tests
    ├── datasets/                 # Scripts for creating LangSmith datasets
    │   ├── coder_dataset.py      # Defines LangSmith dataset for Coder agent evaluation
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py # Defines LangSmith dataset for Task Manager agent
    ├── integration_tests/        # Integration tests for agents and full graph functionality
    │   ├── test_architect_agent.py # Tests for Architect agent
    │   ├── test_coder.py         # REVISED: Basic integration tests for Coder, uses coder_new_pr_config. Advanced eval moved.
    │   ├── eval_coder.py         # NEW: Custom evaluation framework for Coder agent (coder_new_pr flow) using openevals and LangSmith.
    │   ├── test_graph.py         # Tests agent_template memory
    │   ├── test_grumpy_agent.py
    │   ├── test_requirement_gatherer.py
    │   ├── test_task_manager.py  # Tests for Task Manager agent
    │   └── test_tester_agent.py  # Uses create_async_graph_caller, LLMJudge, custom prompt, specific dataset
    ├── testing/                  # Test utilities,
    │   ├── __init__.py           # REVISED: create_async_graph_caller updated
    │   ├── evaluators.py         # LLM-based evaluators (e.g., LLMJudge)
    │   └── formatter.py          # Utilities for formatting/printing evaluation results
    └── unit_tests/               # Unit tests for isolated components
        └── test_configuration.py
```
