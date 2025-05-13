# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy) working collaboratively.
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

Most agents in AI Nexus follow a common structural and operational pattern, largely derived from `src/agent_template/`. *Note: Some agents, like the Tester or Coder, may deviate significantly from this template's graph logic or tool usage.*

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

*   **Role:** Software developer, writes code, interacts with GitHub repositories.
*   **`prompts.py` (`src/coder/prompts.py`):**
    *   `SYSTEM_PROMPT = "You are a sofware developer whose task is to write code."` (This is a basic prompt; a more detailed one might be used in a production scenario).
*   **`tools.py` (`src/coder/tools.py`):**
    *   `GITHUB_TOOLS`: A list of specific GitHub tool names to be used: `create_file`, `read_file`, `update_file`, `delete_file`, `get_contents` (renamed from `get_files_from_directory`), `create_pull_request`, `create_branch`.
    *   `github_tools()`:
        *   Uses `GitHubAPIWrapper` and `GitHubToolkit` from `langchain_community.agent_toolkits` to create actual GitHub tools.
        *   `make_gemini_compatible(tool)`: Adapts tool schema if needed (e.g., by ensuring descriptions are present).
        *   Returns a list of selected GitHub tools.
    *   `mock_github_tools(mock_api: MockGithubApi)`:
        *   Creates mocked versions of GitHub tools using `RunnableLambda` that call methods on a `MockGithubApi` instance.
        *   Tools created: `create_file`, `read_file`, `update_file`, `delete_file`, `get_contents`, `create_pull_request`, `create_branch`.
        *   Some tools like `update_file` and `create_file` have their arguments schema converted to a string input for the mock.
*   **`mocks.py` (`src/coder/mocks.py`):**
    *   `MockGithubApi`: A class that simulates a GitHub API for testing.
        *   Maintains a mock file system (`self.files` as a nested dict), branches (`self.branches`), active branch (`self.active_branch`), and logs operations (`self.operations`).
        *   Methods: `set_active_branch`, `create_branch` (handles unique naming), `_get_files_recursive`, `get_files_from_directory` (renamed to `get_contents` in tools), `create_pull_request`, `create_file`, `update_file`, `delete_file`, `read_file`.
*   **`graph.py` (`src/coder/graph.py`):**
    *   Initializes LLM (e.g., `gemini-1.5-flash-latest` or `gemini-2.0-flash` as per file).
    *   Uses `mock_github_tools` by default (can be switched to real `github_tools()`).
    *   `call_model` node:
        *   Signature: `async def call_model(state: State) -> dict` (Note: no `config` or `store` passed directly if not using memory features from template).
        *   Constructs messages list including the `SYSTEM_PROMPT`.
        *   Binds the `github_tools` (mocked or real) to the LLM.
        *   Invokes LLM: `await llm.bind_tools(github_tools).ainvoke(messages)`.
        *   Returns `{"messages": [messages_after_invoke]}`.
    *   `ToolNode(tools=github_tools)`: Handles execution of GitHub tool calls from the LLM.
    *   Flow:
        *   Entry point: `call_model`.
        *   Conditional edge from `call_model` based on tool calls:
            *   If tool calls: to `execute_tools` (the `ToolNode`).
            *   Else: to `END`.
        *   Edge from `execute_tools` back to `call_model` (to allow the LLM to respond after tool execution).
*   **`state.py` (`src/coder/state.py`):**
    *   `class State(TypedDict): messages: Annotated[list[AnyMessage], add_messages]` (Uses `AnyMessage` for type hinting).
*   **`README.md` (`src/coder/README.md`):**
    *   Instructions for setting up a GitHub App with necessary permissions (Contents R/W, Pull requests R/W, Commit statuses R, Issues R/W, Metadata R) and environment variables (`GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_REPOSITORY`).

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
        *   Contains tests for the Coder agent's GitHub interactions using `MockGithubApi`.
        *   Introduces a custom evaluation framework for the Coder agent using `openevals`.
        *   Defines `CodeEvaluatorInputs`, `CodeEvaluatorReferenceOutputs`, and `Result` TypedDicts for structuring evaluation data.
        *   Uses a specific `EVAL_PROMPT` and an LLM (`gemini-2.0-flash`) configured for structured output (`Result`) to act as a judge.
        *   The `evaluate_code` function orchestrates the evaluation using `openevals.utils._arun_evaluator`.
        *   The `invoke_agent` function runs the Coder graph with mocked GitHub tools and specific starting code state.
        *   The `test_coder_creates_rest_api` test demonstrates this custom evaluation flow.

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
    *   **LangSmith Datasets + LLM Judge:** Used for Requirement Gatherer, Tester (simple case), Grumpy. Relies on `client.aevaluate()` and evaluators defined in `tests/testing/evaluators.py`.
    *   **Custom `openevals` Framework:** Implemented in `tests/integration_tests/test_coder.py` for the Coder agent. Involves custom prompts, input/output structures, and direct use of `openevals` utilities with an LLM judge defined within the test file.
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
    *   `langgraph.json` can be used to set the default graph to open in Studio (e.g., by setting `default_graph`). It now includes an entry for the `architect` graph.
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
├── Makefile                      # Task runner (Added test-memory-graph target)
├── README.md                     # Includes NEW section on using semantic memory
├── agent_memories/               # Agent-specific static memories (e.g., for Grumpy)
│   └── grumpy/
│       ├── review-coding.md      # Context for Grumpy's code review
│       ├── review-designing.md   # Context for Grumpy's design review
│       └── role.md               # Core operational rules and Mermaid diagram for Grumpy
├── langgraph.json                # LangGraph Studio configuration (e.g., default graph, agent entries)
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
│   ├── coder/                    # Coder agent: writes code, interacts with GitHub
│   │   ├── mocks.py              # Mock GitHub API for testing
│   │   └── README.md             # Setup instructions for GitHub App
│   ├── common/                   # Common utilities shared across agents
│   │   └── utils/                # Shared utility functions
│   ├── grumpy/                   # Grumpy agent: reviews design/coding tasks based on strict rules
│   ├── orchestrator/             # Orchestrator agent: delegates tasks to other agents
│   │   ├── memory/               # Markdown files defining Orchestrator's rules and team
│   │   └── stubs/                # Stub implementations for delegated agent calls (for testing/dev)
│   ├── requirement_gatherer/     # Requirement Gatherer agent: elicits and clarifies requirements
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
    │   ├── coder_dataset.py      # NEW: Defines LangSmith dataset for Coder agent evaluation
    │   └── requirement_gatherer_dataset.py
    ├── integration_tests/        # Integration tests for agents and full graph functionality
    │   ├── test_architect_agent.py # Tests for Architect agent
    │   ├── test_coder.py         # REVISED: Uses LangSmith dataset and custom evaluator for Coder agent
    │   ├── test_graph.py         # Tests agent_template memory
    │   ├── test_grumpy_agent.py
    │   ├── test_requirement_gatherer.py
    │   └── test_tester_agent.py  # REWRITTEN: Uses create_async_graph_caller, LLMJudge, custom prompt, specific dataset
    ├── testing/                  # Test utilities, 
    │   ├── __init__.py           # REVISED: create_async_graph_caller updated
    │   ├── evaluators.py         # LLM-based evaluators (e.g., LLMJudge)
    │   └── formatter.py          # Utilities for formatting/printing evaluation results
    └── unit_tests/               # Unit tests for isolated components
        └── test_configuration.py
```
