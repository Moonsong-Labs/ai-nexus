# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy) working collaboratively.
2.  **Externalized Memory (Memory Bank):** A core principle, especially for the "Cursor" concept, where agents rely on structured external files (primarily Markdown) for persistent knowledge, project state, and context. This addresses context loss in AI agents.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory.
5.  **System Prompts:** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols.
6.  **Configuration Management:** Agents have configurable parameters, including LLM models and system prompts, managed via `Configuration` dataclasses.
7.  **Asynchronous Operations:** The system heavily utilizes `async` and `await` for non-blocking operations within the agent graphs.


## 2. The Memory Bank System (Conceptualized for "Cursor")

The Memory Bank is designed as Cursor's (and potentially other agents') sole source of project knowledge, ensuring continuity despite internal memory resets. It consists of structured Markdown files.

**Location:** `memory-bank/` (This directory is conceptualized and its contents are described in `project_memories/global.md` but not present as actual files in the provided codebase snapshot, except for `project_memories/global.md` itself which describes it).

**Core Files & Purpose (as defined in `project_memories/global.md`):**

*   **`projectbrief.md`**:
    *   **Project Name:** AI Nexus
    *   **Core Requirements & Goals:**
        *   Develop a system for managing AI agents, initially "Cursor".
        *   Cursor's memory resets completely between sessions.
        *   Create a "Memory Bank" for Cursor to understand the project and continue work.
        *   Memory Bank must be perfect, meticulously maintained documentation.
    *   **Scope:**
        *   Initial: Establish Memory Bank structure, populate core files, define Cursor-Memory Bank interaction.
        *   Future: Develop Cursor and other AI agents.
    *   **Stakeholders:** Primary user/developer interacting with Cursor.

*   **`productContext.md`**:
    *   **Why This Project Exists:** To implement a novel approach to AI agent operation, addressing memory persistence challenges (e.g., Cursor's session-based memory reset).
    *   **Problems It Solves:**
        *   Context loss in AI agents.
        *   Maintaining project continuity.
        *   Ensuring accurate AI task execution via comprehensive memory.
        *   Facilitating complex AI collaboration.
    *   **How It Should Work:**
        *   Cursor's internal memory resets post-session.
        *   Cursor MUST read ALL Memory Bank files at new session start.
        *   Memory Bank is the sole source of project knowledge (structured Markdown).
        *   Cursor updates Memory Bank with new info, decisions, progress.
        *   Hierarchical structure for layered context.
    *   **User Experience Goals:**
        *   Seamless interaction (feels like persistent memory).
        *   Reliable AI performance.
        *   Transparent operation (reliance on Memory Bank is clear).
        *   High-quality, understandable documentation in the Memory Bank.

*   **`activeContext.md`**:
    *   **Current Work Focus:** Tracks the immediate tasks and objectives.
    *   **Recent Changes:** Logs significant updates and accomplishments.
    *   **Next Steps:** Outlines upcoming tasks.
    *   **Active Decisions and Considerations:** Records ongoing decision-making processes and important factors being considered.
    *   *This file is expected to be frequently updated by the agent.*

*   **`systemPatterns.md`**:
    *   **System Architecture:**
        *   Core Agent (e.g., Cursor): AI with memory reset.
        *   External Memory (Memory Bank): Markdown files in `memory-bank/`.
        *   Interaction Model:
            1.  Session Start: Agent reads ALL Memory Bank files.
            2.  Task Execution: Agent performs tasks based on Memory Bank and user requests.
            3.  Memory Update: Agent updates Memory Bank (esp. `activeContext.md`, `progress.md`, `.cursorrules`).
            4.  Session End: Agent's internal state lost.
    *   **Key Technical Decisions:**
        *   Memory Externalization.
        *   Markdown for Memory Bank (human-readable, AI-parsable, versionable).
        *   Hierarchical file structure.
        *   Mandatory Full Read of Memory Bank at session start.
    *   **Design Patterns in Use:**
        *   State Externalization.
        *   Observer Pattern (Implicit): Agent observes Memory Bank; future self observes changes.
        *   Single Source of Truth: Memory Bank for project information.
    *   **Component Relationships (Mermaid Diagram):**
        ```mermaid
        graph TD
            User --> CursorAgent[Cursor Agent]
            CursorAgent -- Reads/Writes --> MemoryBank[Memory Bank Files]
            MemoryBank -- Contains --> ProjectBrief[projectbrief.md]
            MemoryBank -- Contains --> ProductContext[productContext.md]
            MemoryBank -- Contains --> ActiveContext[activeContext.md]
            MemoryBank -- Contains --> SystemPatternsDoc[systemPatterns.md]
            MemoryBank -- Contains --> TechContextDoc[techContext.md]
            MemoryBank -- Contains --> ProgressDoc[progress.md]
            MemoryBank -- May Contain --> AdditionalContext[Additional Context Files/Folders]
            CursorAgent -- Reads/Writes --> CursorRules[.cursorrules]

            ProjectBrief --> ProductContext
            ProjectBrief --> SystemPatternsDoc
            ProjectBrief --> TechContextDoc

            ProductContext --> ActiveContext
            SystemPatternsDoc --> ActiveContext
            TechContextDoc --> ActiveContext

            ActiveContext --> ProgressDoc
        ```

*   **`techContext.md`**:
    *   **Technologies Used:**
        *   Memory Bank Storage: Markdown files (`.md`).
        *   Cursor Agent (Conceptual): AI model capable of R/W Markdown, user interaction, tool use.
        *   Environment: VS Code, Linux.
        *   Version Control: Git (assumed).
    *   **Development Setup:**
        *   Workspace: `/home/crystalin/projects/ai-nexus` (example).
        *   Memory Bank Location: `memory-bank/` subdirectory.
        *   Core Files: (listed above).
        *   Project Intelligence File: `.cursorrules` in workspace root.
    *   **Technical Constraints:**
        *   Memory Reset (primary constraint for Cursor).
        *   Reliance on documentation (all knowledge from Memory Bank).
        *   Markdown parsing and generation proficiency.
        *   Adherence to tool use protocols (e.g., XML-style tags).
    *   **Dependencies:**
        *   File System Access tools.
        *   User Interface.
        *   Tooling Environment (access to defined tools like `read_file`, `write_to_file`).

*   **`progress.md`**:
    *   **What Works:** Lists completed features and milestones.
    *   **What's Left to Build:** Identifies pending tasks and development areas.
    *   **Current Status:** Overall project status (e.g., documentation phase, development phase).
    *   **Known Issues:** Tracks identified bugs or problems.
    *   *This file is also expected to be frequently updated.*


## 3. Project-Level Standards & Goals (`project_memories/PRD.md`)

This file outlines the overarching standards and technological choices for the AI Nexus project.

*   **Language:** English
*   **Goal:** Create a fully functional team of AI agents to design, develop, and maintain technical projects.
*   **Core Technologies & Frameworks:**
    *   **Python:** >= 3.12 (Primary programming language).
    *   **LangGraph:** Core framework for building AI agents.
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
    *   **openevals:** Suggests involvement in evaluating language models.
*   **Version Control:** Git.
*   **LLM Models:**
    *   **`gemini-1.5-flash-latest` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (PRD mentions `gemini-2.0-flash`, current common models are 1.5 series. The intent is a fast model.)
    *   **`gemini-1.5-pro-latest` (or similar pro variants):** Preferred for complex tasks needing reasoning. (PRD mentions `gemini-2.5-pro-preview-03-25`, intent is a powerful model.)


## 4. General Agent Architecture (based on `src/agent_template/` and common patterns)

Most agents in AI Nexus follow a common structural and operational pattern, largely derived from `src/agent_template/`.

*   **Typical Agent Directory Structure:**
    *   `__init__.py`: Exposes the agent's graph.
    *   `configuration.py`: Defines agent-specific configurable parameters.
    *   `graph.py`: Contains the LangGraph `StateGraph` definition.
    *   `memory.py` (in `agent_template`): Handles loading of static memories.
    *   `prompts.py`: Stores default system prompts and potentially other prompts.
    *   `state.py`: Defines the `State` dataclass for the agent's graph.
    *   `tools.py`: Defines tools available to the agent.
    *   `utils.py`: Utility functions, often including `init_chat_model` and `split_model_and_provider`.

*   **`configuration.py` (Typical Structure - `src/agent_template/configuration.py`):**
    ```python
    from dataclasses import dataclass, field
    from typing import Annotated, Any
    from langchain_core.runnables import RunnableConfig
    from . import prompts # Or specific prompts module for other agents

    @dataclass(kw_only=True)
    class Configuration:
        """Main configuration class for the memory graph system."""
        user_id: str = "default"
        """The ID of the user to remember in the conversation."""
        model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
            default="google_genai:gemini-1.5-flash-latest" # Example, actual default may vary
        )
        system_prompt: str = prompts.SYSTEM_PROMPT # Default system prompt from agent's prompts.py

        # Other agent-specific configurations might be added here
        # e.g., question_prompt: str for Grumpy agent

        @classmethod
        def from_runnable_config(cls, config: RunnableConfig) -> "Configuration":
            """Create a Configuration instance from a RunnableConfig."""
            configurable = (
                config.get("configurable")
                if config.get("configurable") is not None
                else {}
            )
            values: dict[str, Any] = {
                k: configurable.get(k, getattr(cls, k)) for k in cls.__annotations__
            }
            return cls(**values)
    ```

*   **`state.py` (Typical Structure - `src/agent_template/state.py`):**
    ```python
    from dataclasses import dataclass
    from typing import Annotated, Any
    from langgraph.graph.message import AnyMessage, add_messages

    @dataclass(kw_only=True)
    class State:
        """Main graph state."""
        messages: Annotated[list[AnyMessage], add_messages]
        """The messages in the conversation."""
        # Other agent-specific state variables might be added here
        # e.g., analysis_question: str = "" for Grumpy agent
    ```

*   **`graph.py` (Core Logic - Simplified General Flow from `src/agent_template/graph.py`):**
    *   **Initialization:**
        *   Logger setup (`logging.getLogger(__name__)`).
        *   Language Model (LLM) initialization using `init_chat_model()` (from `utils.py`).
    *   **`call_model` Node:**
        *   Signature: `async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict`
        *   Retrieves `Configuration` from `RunnableConfig`.
        *   Ensures static memories are loaded using `ensure_static_memories(store)` (from `memory.py`).
        *   Retrieves recent dynamic memories from `store.asearch()` based on `user_id` and a query derived from recent messages.
        *   Formats dynamic and static memories for inclusion in the prompt. Static memories are loaded from JSON files in `.langgraph/static_memories/` and have a specific format in the prompt.
        *   Constructs the system prompt using `configurable.system_prompt.format(...)`, injecting current time, user info, and retrieved memories.
        *   Invokes the LLM (`llm.bind_tools([tools.upsert_memory]).ainvoke(...)`) with the conversation history (`state.messages`) and the constructed system prompt. The `upsert_memory` tool is bound to the LLM.
        *   Returns a dictionary to update the graph's state, typically `{"messages": [msg]}` where `msg` is the LLM's response.
    *   **`store_memory` Node:**
        *   Signature: `async def store_memory(state: State, config: RunnableConfig, *, store: BaseStore)`
        *   Extracts tool calls (specifically for `upsert_memory`) from the last AI message in `state.messages`.
        *   Executes `upsert_memory` tool calls concurrently using `asyncio.gather`. Each call involves `store.aupsert()` with `user_id`, `memory_id`, content, and context.
        *   Formats results of memory storage operations into `ToolMessage`s.
        *   Returns a dictionary to update the graph's state with these `ToolMessage`s: `{"messages": results}`.
    *   **`route_message` Conditional Edge:**
        *   Signature: `def route_message(state: State)`
        *   Determines the next node based on whether the last AI message (`state.messages[-1]`) contains tool calls.
        *   If tool calls exist (e.g., for `upsert_memory`), routes to the `store_memory` node.
        *   Otherwise, routes to `END`, allowing the user to send the next message.
    *   **Graph Compilation:**
        *   A `StateGraph` instance is created: `builder = StateGraph(State, config_schema=configuration.Configuration)`.
        *   Nodes (`call_model`, `store_memory`) are added using `builder.add_node()`.
        *   The entry point is set to `call_model`: `builder.set_entry_point("call_model")`.
        *   Edges are added:
            *   `builder.add_conditional_edges("call_model", route_message, {"store_memory": "store_memory", "__end__": "__end__"})`
            *   `builder.add_edge("store_memory", "__end__")` (or back to `call_model` if further response is needed after memory storage).
        *   The graph is compiled: `graph = builder.compile()`.
        *   For testing/evaluation, the graph is compiled with a checkpointer (e.g., `MemorySaver()`) and a store (e.g., `InMemoryStore()`).

*   **`tools.py` (Typical `upsert_memory` Tool - `src/agent_template/tools.py`):**
    ```python
    import uuid
    from langchain_core.runnables import RunnableConfig
    from langchain_core.tools import tool
    from .configuration import Configuration # Agent's config
    # from langgraph.prebuilt import ToolNode # Not directly used for upsert_memory's definition
    # from ..services.store import BaseStore # Interaction is handled by store_memory node

    @tool
    async def upsert_memory(
        content: str, context: str, memory_id: str | None = None, *, config: RunnableConfig
    ) -> str:
        """Upsert a memory in the database.

        If a memory conflicts with an existing one, then just UPDATE the
        existing one by passing in memory_id - don't create two memories
        that are the same. If the user corrects a memory, UPDATE it.

        Args:
            content: The main content of the memory. For example:
                "User expressed interest in learning about French."
            context: Additional context for the memory. For example:
                "This was mentioned while discussing career options in Europe."
            memory_id: ONLY PROVIDE IF UPDATING AN EXISTING MEMORY.
            The memory to overwrite.
        """
        # This tool definition provides the schema for the LLM.
        # The actual storage logic is handled by the `store_memory` node in the graph,
        # which calls `store.aupsert()`.
        # The `user_id` is retrieved from `Configuration.from_runnable_config(config).user_id`
        # within the `store_memory` node before calling `store.aupsert()`.
        # The `mem_id` (if None) is generated using `uuid.uuid4()` in the `store_memory` node.

        # The return string here is for the LLM to know the format of a successful call.
        # The actual ToolMessage content will be generated by the `store_memory` node.
        effective_mem_id = memory_id or "newly_generated_uuid"
        return f"Memory {effective_mem_id} upserted with content: '{content}' and context: '{context}'."
    ```

*   **`memory.py` (Static Memory Loading - `src/agent_template/memory.py`):**
    *   `STATIC_MEMORIES_DIR = Path(".langgraph/static_memories/")`: Defines the directory for static memory JSON files.
    *   `async def _load_memories_from_directory(directory_path: Path, store: BaseStore)`:
        *   Iterates through JSON files in `directory_path`.
        *   For each file, loads memories (expected to be a list of dicts, each with `content` and `context`).
        *   Stores each memory in the `store` using `store.aput()` with a key like `filename_index` and namespace `("static_memories", "global")`.
    *   `async def ensure_static_memories(store: BaseStore)`:
        *   Checks if any static memories (namespace `("static_memories", "global")`) already exist in the `store` using `store.asearch()`.
        *   If not found (or on error), calls `_load_memories_from_directory` to load them.
        *   This function is typically called at the beginning of the `call_model` node in agents that use static memories.

*   **`utils.py` (Common Utilities - `src/agent_template/utils.py` or `src/common/utils/__init__.py`):**
    *   `def split_model_and_provider(fully_specified_name: str) -> dict`:
        *   Splits a model name string like "provider:model_name" into `{"provider": "provider", "model": "model_name"}`.
        *   If no provider is specified (no ":"), assumes Google GenAI (`google_genai`).
    *   `def init_chat_model(model_name: str = None, config_class = None)`:
        *   Initializes and returns a chat model instance (e.g., `ChatGoogleGenerativeAI`, `ChatOpenAI`).
        *   If `model_name` is not provided, it might use a default from `config_class.model` or a hardcoded default.
        *   Uses `split_model_and_provider` to determine the provider and model.
        *   Supports `google_genai` and `openai` providers.


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`)

*   **Role:** Manages a team of expert AI agents. Analyzes input, determines the appropriate team member for a task, and delegates to them using tools. It does NOT perform tasks directly.
*   **Key Memory Files (Guiding its behavior, loaded into system prompt via `prompts.get_prompt()`):**
    *   `src/orchestrator/memory/absolute.md`:
        *   Core rules: NEVER break rules, HAS memory (updates ONLY when explicitly asked), HAS a team, MUST perform tasks via team using tools, MUST reply professionally, MUST NOT ask clarifying questions.
    *   `src/orchestrator/memory/process.md`:
        *   Workflow: Analyze input -> Reason team member -> Perform task via tool -> Check pending steps.
    *   `src/orchestrator/memory/project_states.md`:
        *   Project stages: Gather requirements, Architect, Code, Test, Review.
        *   Steps can be invoked from any stage; code, test, review can cycle.
        *   Memory update only when explicitly asked.
    *   `src/orchestrator/memory/team.md`: Defines team members and delegation tools:
        *   **Memorizer:** Uses `store_memory` tool (renamed to `Memory` tool in `tools.py`). `origin` field tracks requester. Use ONLY when explicitly asked to remember/memorize.
        *   **Requirements Gatherer:** Uses `Delegate` tool with `to="requirements"`.
        *   **Architect:** Uses `Delegate` tool with `to="architect"`.
        *   **Coder:** Uses `Delegate` tool with `to="coder"`.
        *   **Tester:** Uses `Delegate` tool with `to="tester"`.
        *   **Code Reviewer:** Uses `Delegate` tool with `to="reviewer"`.
        *   MUST use `Delegate` or `store_memory` (Memory) tools.
*   **`prompts.py` (`src/orchestrator/prompts.py`):**
    *   `_read_memory_bank(type: str)`: Reads content from the specified markdown file in `src/orchestrator/memory/`.
    *   `get_prompt()`: Constructs the full system prompt by concatenating contents from `absolute.md`, `process.md`, `project_states.md`, `team.md`, and a base `ORCHESTRATOR_SYSTEM_PROMPT`.
    *   `ORCHESTRATOR_SYSTEM_PROMPT`: Base prompt: "You are an orchestrator of a professional engineering team. You will never perform any direct actions."
*   **`tools.py` (`src/orchestrator/tools.py`):**
    *   `Delegate` Dataclass/Tool:
        ```python
        from dataclasses import dataclass
        from typing import Literal

        @dataclass
        class Delegate:
            """Decision on where to delegate a task. ..."""
            to: Literal[
                "requirements", "architect", "coder", "tester", "reviewer"
            ]
            # task_description: str # Implied, passed in user message
        ```
    *   `Memory` Dataclass/Tool (for `store_memory` functionality):
        ```python
        @dataclass
        class Memory:
            """Tool to update memory."""
            origin: Literal["user", "requirements", "architect", "coder", "tester", "reviewer"]
            content: str
        ```
*   **`graph.py` (`src/orchestrator/graph.py`):**
    *   `call_orchestrator` node:
        *   Uses `model_orchestrator` (initialized via `init_chat_model`).
        *   System prompt is formatted with current time.
        *   Binds `tools.Delegate` and `tools.Memory` (as `store_memory`) to the LLM.
    *   `route_tools` conditional edge:
        *   Checks `tool_call["name"]`.
        *   If "Delegate", routes to the corresponding stub function in `src/orchestrator/stubs/` (e.g., `stubs.requirements`, `stubs.architect`).
        *   If "store_memory" (or "Memory"), routes to `stubs.memorizer`.
    *   Stub functions (`src/orchestrator/stubs/__init__.py`):
        *   These are placeholders (e.g., `requirements`, `architect`, `coder`, `tester`, `reviewer`, `memorizer`).
        *   They simulate agent responses by returning `ToolMessage` with predefined or cycled content.
        *   `memorizer` stub: Constructs a `ToolMessage` like `"[MEMORIZE] for {origin}: {content}"`.
        *   Other stubs use a `MessageWheel` to cycle through predefined responses.
*   **`configuration.py` (`src/orchestrator/configuration.py`):**
    *   Uses `prompts.get_prompt()` for `system_prompt` default.
*   **`state.py` (`src/orchestrator/state.py`):** Standard `State` with `messages`.

#### 5.2. Architect (`src/architect/`)

*   **Role:** Expert software engineer responsible for architecting a project, not writing code. Receives project needs, coordinates other AI agents. Manages project documentation.
*   **Key Prompt (`src/architect/prompts/v0.md`):** This is a very detailed system prompt.
    *   **Identity:** "I am Architect..."
    *   **Core Responsibility:** MUST read ALL files in 'project' folder at the start of EVERY task.
    *   **Core Values:** Requirement Gathering, Research Driven, Technology Selection, Task Definition, Validation and Adjustment, Transparency and Traceability.
    *   **Project Structure Understanding:** Defines a hierarchy of Markdown files it expects and manages within a 'project' folder:
        *   Core Files (Required): `projectbrief.md`, `projectRequirements.md`, `systemPatterns.md`, `techContext.md`, `progress.md`.
        *   Specific Files (Required): `featuresContext.md`, `testingContext.md`, `securityContext.md`. These track current work, changes, next steps, decisions, patterns, learnings for their respective scopes. Tasks need start/finish dates.
        *   `progress.md` is updated last.
        *   Flowchart of file dependencies is provided in the prompt.
    *   **Old Information Management:** Information older than two weeks from task/progress files is moved to `changelog.md`. This file is checked only if prompted with "check changelog".
    *   **Documentation Updates:** Triggered by: new patterns, significant changes, user request "update project" (MUST review ALL files), context clarification. Includes a flowchart for the update process.
*   **`prompts.py` (`src/architect/prompts.py`):**
    *   Reads `src/architect/prompts/v0.md`.
    *   Formats it by injecting `user_info` (OS, username, current directory) and current `time`.
*   **Structure:** Follows the `agent_template` pattern.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`.
    *   `graph.py`: Standard `call_model`, `store_memory`, `route_message` flow. Uses `tools.upsert_memory`.
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
    *   `class State(TypedDict): messages: Annotated[list, add_messages]`
*   **`README.md` (`src/coder/README.md`):**
    *   Instructions for setting up a GitHub App with necessary permissions (Contents R/W, Pull requests R/W, Commit statuses R, Issues R/W, Metadata R) and environment variables (`GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_REPOSITORY`).

#### 5.4. Code Reviewer (`src/code_reviewer/`)

*   **Role:** Expert code reviewer, makes suggestions to maintain a high-quality codebase. Does NOT modify code/assets directly.
*   **`system_prompt.md` (`src/code_reviewer/system_prompt.md`):**
    *   **Agent Role:** Expert code reviewer in a multi-agent framework.
    *   **Goal:** Review code/assets, make suggestions for high quality, covering:
        *   Best programming practices, idiomatic conventions, patterns.
        *   Concise, clear code.
        *   Well-defined inputs, graceful error handling.
        *   Test coverage.
        *   Security against malicious input/state manipulation.
        *   Bug-free, considers corner cases, maintainable logic.
    *   **Interaction:** Makes suggestions, does not modify. Other agents incorporate suggestions.
    *   **Feedback Style:** Clear, concise, unambiguous, with context.
*   **`prompts.py` (`src/code_reviewer/prompts.py`):**
    *   Reads `src/code_reviewer/system_prompt.md`.
    *   Formats it by injecting `user_info` and current `time`.
*   **Structure:** Follows the `agent_template` pattern.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`.
    *   `graph.py`: Standard `call_model`, `store_memory`, `route_message` flow. Uses `tools.upsert_memory`. Does not use static memories from `agent_template/memory.py` explicitly in its `call_model` but inherits the structure.
    *   `state.py`: Standard `State` with `messages`.
    *   `tools.py`: Defines the standard `upsert_memory` tool.

#### 5.5. Tester (`src/tester/`)

*   **Role:** Generates tests for the codebase based on business requirements (from Product Agent) and code architecture/interfaces (from Architecture Agent).
*   **`test-agent-system-prompt.md` (`src/tester/test-agent-system-prompt.md`):**
    *   **Objective:** Sole responsibility is to generate tests.
    *   **Must Not:** Invent rules/behaviors, make assumptions, define architecture, suggest design changes.
    *   **How You Operate:** Follow requirements/interfaces strictly. Generate comprehensive behavior tests. Propose edge case tests; if handling undefined, ask for clarification.
    *   **Workflow (Strict & Iterative):**
        1.  Analyze requirements, identify ambiguities/missing info.
        2.  Always begin by sending a "questions" message with ALL questions.
        3.  Wait for answers.
        4.  Group requirements by category/functionality.
        5.  For EACH category:
            a.  Generate tests for that category ONLY.
            b.  Send a single "tests" message with all tests for that category (traceability included).
            c.  STOP, wait for explicit user feedback on each test.
            d.  Handle rejected tests (skip if not needed, regenerate if feedback given).
            e.  Proceed to next category ONLY after ALL tests in current category are approved.
        6.  Continue until all categories covered.
    *   **Rules:** Only generate tests for explicit definitions. Identify gaps, ask questions. Traceable tests.
    *   **Mindset:** Methodical, precise, transparent, rigorous QA engineer.
    *   **User Feedback Format (JSON):** Defines schema for user feedback on tests, including `testId`, `approved`, `rejectionReason`, and `allTestsApproved` flag. Details how to handle feedback.
*   **`prompts.py` (`src/tester/prompts.py`):**
    *   Reads `src/tester/test-agent-system-prompt.md`.
    *   Escapes curly braces (`{`, `}`) for `format` compatibility, then injects `user_info` and `time`.
*   **`output.py` (`src/tester/output.py`):** Defines Pydantic models for structured LLM output:
    *   `TesterAgentTestOutput(BaseModel)`: `id`, `name`, `description`, `code`, `requirement_id`.
    *   `TesterAgentQuestionOutput(BaseModel)`: `id`, `question`, `context`.
    *   `TesterAgentFinalOutput(BaseModel)`: `questions: List[TesterAgentQuestionOutput]`, `tests: List[TesterAgentTestOutput]`. The LLM is expected to produce output conforming to this model.
*   **`test-prompts/web-api.md` (`src/tester/test-prompts/web-api.md`):** Example requirements for a Todo List Web API (business requirements, endpoints) that the Tester agent might consume as input.
*   **Structure:** Follows the `agent_template` pattern.
    *   `configuration.py`: Standard.
    *   `graph.py`: Standard `call_model`, `store_memory`, `route_message` flow. Uses `tools.upsert_memory`. The `call_model` is expected to bind the `TesterAgentFinalOutput` as a tool or parse its structured output. The current `graph.py` for tester is standard agent_template, so it doesn't explicitly show parsing of `TesterAgentFinalOutput` but would need adaptation.
    *   `state.py`: Standard.
    *   `tools.py`: Standard `upsert_memory`.
    *   `utils.py`: Standard.

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`)

*   **Role:** Elicits, clarifies, and refines project goals, needs, and constraints.
*   **`prompts.py` (`src/requirement_gatherer/prompts.py`):**
    *   The `SYSTEM_PROMPT` is a detailed markdown document guiding the agent. Key aspects include:
        *   **Operating Principles:** First question classification (vision, project type), adaptive inquiry depth (hobby projects focus on Vision and Functional Requirements; full products are comprehensive), prioritization intelligence, product-first mindset, zero-assumption rule, iterative refinement, structured output, proactive clarification, memory utilization.
        *   **Requirement Bank Structure:** Defines categories like Vision, Goals, User Stories, Functional/Non-Functional Requirements, Constraints, Risks, etc.
        *   **Interaction Style:** Professional, empathetic, inquisitive, structured.
        *   **Workflow:**
            1.  Begin with Project Classification (vision, hobby/full product). For hobby/personal projects, focus only on Vision and Functional Requirements.
            2.  Intelligent Questioning based on project type and context.
            3.  Iterative Deep Dive for each relevant section of the Requirement Bank.
            4.  Memory Update using `upsert_memory` tool.
            5.  Consolidation and Review.
            6.  Handling User Feedback.
        *   **Tool Usage:** `upsert_memory` for storing gathered information.
*   **Structure:** While based on `agent_template`, its graph has specific modifications.
    *   `configuration.py`: Standard.
    *   `graph.py` (`src/requirement_gatherer/graph.py`):
        *   Nodes: `call_model` (from template), `store_memory` (from template), `call_evaluator_model`, `human_feedback`.
        *   `call_evaluator_model` node:
            *   Retrieves `Configuration` from `RunnableConfig`.
            *   Retrieves recent memories from the `store` based on `user_id` and recent messages.
            *   Formats these memories for inclusion in the system prompt.
            *   Uses `configurable.evaluator_system_prompt` (content not specified in this memory, but used by the node) formatted with memories and current time.
            *   Invokes an `evaluator` (presumably an LLM) with this system prompt and current messages.
            *   Returns a `veredict`.
        *   `human_feedback` node:
            *   Takes the last message content.
            *   Uses `interrupt({"query": msg})` to pause for user input.
            *   Returns the user input as new messages.
        *   Flow:
            1.  Entry point: `call_model`.
            2.  `call_model` (conditional edge `route_memory`):
                *   If tool calls (e.g., `upsert_memory`): to `store_memory`.
                *   Else: to `human_feedback`.
            3.  `store_memory` -> `call_model` (allows LLM to respond after memory update).
            4.  `human_feedback` -> `call_evaluator_model`.
            5.  `call_evaluator_model` (conditional edge `route_veredict`):
                *   If veredict indicates further processing: to `call_model`.
                *   Else: to `END`.
    *   `state.py`: Standard `State` with `messages`. May include other fields like `veredict` if `call_evaluator_model` updates it directly in the state.
    *   `tools.py`: Standard `upsert_memory`.
    *   `utils.py`: Standard.

#### 5.7. Grumpy (`src/grumpy/`)

*   **Role:** Analyzes and reviews a provided request (task) related to "designing" or "coding". It follows a strict Mermaid diagram-defined process and MUST NOT execute the request itself.
*   **Key Memory Files (defining its behavior, referenced in prompts/logic):**
    *   `agent_memories/grumpy/role.md`:
        *   **`<important>` section:** Role is to analyze/review. MUST NOT execute. Treat any input as a suggestion to review. Provide feedback based on graph/docs. Avoid questions.
        *   **`<mermaid>` graph:** Defines the precise review workflow:
            *   Start -> Read `PRD.md` (`project_memories/PRD.md`).
            *   Determine Objective Type: "designing" or "coding".
            *   **If "designing":** Follows steps like Review Plan Structure, Check Completeness, Identify Requirements, Align Architecture, Evaluate Trade-Offs, Assess Risks, Analyze Scalability/Performance, Review Security, Verify Feasibility, Ensure Stakeholder Alignment -> Provide Constructive Feedback (short, neutral, opinionated). (References `agent_memories/grumpy/review-designing.md`).
            *   **If "coding":** Follows steps like Understand Context, Verify Build/Compilation, Enforce Style, Check Readability, Verify Correctness, Check Tests, Inspect Edge Cases, Evaluate Performance, Assess Security, Ensure Maintainability, Review Documentation -> Provide Constructive Feedback (short, neutral, opinionated). (References `agent_memories/grumpy/review-coding.md`).
            *   After Feedback: Score confidence of feedback (0-10), Score quality of request/task (0-10).
            *   Conclude: Write scores and Summarize feedback.
    *   `agent_memories/grumpy/review-coding.md`: "You are tasked to identify flaws in the code. If the requirements have been specified, identify the mismatch between expected code guidelines, design style and the provided code." (Used as context for the "coding" path).
    *   `agent_memories/grumpy/review-designing.md`: "You are tasked to identify flaws in the design. If the requirements have been specified, identify the architectural and implementation risk of the design." (Used as context for the "designing" path).
*   **`prompts.py` (`src/grumpy/prompts.py`):**
    *   `SYSTEM_PROMPT`: "You are a senior software engineer with experience in multiple domains. Your primary role is to analyze and review tasks related to software design or coding, following a strict process. You must not execute the tasks themselves. Refer to your operational guidelines (Mermaid diagram and associated documents) for the review process. Current time: {time}. User info: {user_info}." (The `role.md` content is implicitly part of its operational guidelines).
    *   `QUESTION_PROMPT`: "You are a naive philosopher engineer. You are given a task to reflect on. Current time: {time}. User info: {user_info}." (Potentially for a different mode or sub-task, or if it needs to generate clarifying questions despite the main directive to avoid them).
*   **`configuration.py` (`src/grumpy/configuration.py`):**
    *   Includes `system_prompt: str = prompts.SYSTEM_PROMPT` and `question_prompt: str = prompts.QUESTION_PROMPT`.
*   **`state.py` (`src/grumpy/state.py`):**
    *   Includes `analysis_question: str = ""` in its state, in addition to `messages`.
*   **`graph.py` (`src/grumpy/graph.py`):**
    *   The `call_model` node:
        *   Retrieves configuration, including `system_prompt` and `question_prompt`.
        *   Checks if the model supports memory (based on `configurable.model` name, e.g., if it's not "ollama"). If so, it retrieves memories and formats them.
        *   Constructs the system prompt using `configurable.system_prompt.format(...)`.
        *   Binds `tools.upsert_memory` if memory is supported.
        *   Invokes the LLM.
        *   If the LLM response is empty and `analysis_question` is empty, it formats the `question_prompt` and invokes the LLM again with this prompt to generate a question (this part seems to be for a specific scenario, possibly when the initial review yields no output).
    *   Provides two compiled graphs: `graph` (with memory tools and logic) and `graph_no_memory` (a simpler version without memory interaction in `call_model` and no `store_memory` node).
*   **`tools.py` (`src/grumpy/tools.py`):** Standard `upsert_memory` tool.
*   **`utils.py` (`src/grumpy/utils.py`):** Standard utilities.


## 6. Testing Framework (`tests/`)

The project uses `pytest` for testing and integrates with LangSmith for evaluation and dataset management.

*   **Common Test Setup:**
    *   `Client()` from `langsmith` for LangSmith interactions.
    *   `MemorySaver()` from `langgraph.checkpoint.memory` for graph checkpointing.
    *   `InMemoryStore()` from `langgraph.stores.memory` for agent memory during tests.
    *   Graphs are typically compiled with a checkpointer and store: `graph_compiled = graph_builder.compile(checkpointer=memory_saver, store=memory_store)`.
    *   A wrapper function (e.g., `run_graph_with_config` or `call_tester_agent`, or using `create_async_graph_caller`) is often created/used to:
        *   Take a dataset example as input.
        *   Format the input for the graph.
        *   Generate a unique `thread_id` (using `uuid.uuid4()`) for state isolation in `RunnableConfig`.
        *   Invoke the compiled graph: `await graph_compiled.ainvoke(graph_input, config=config)`.
        *   Extract and format the output for evaluation.
    *   `client.aevaluate()` is used to run evaluations against LangSmith datasets, passing the wrapper function and dataset name/examples.

*   **`tests/datasets/requirement_gatherer_dataset.py`:**
    *   Defines `REQUIREMENT_GATHERER_DATASET_NAME = "Requirement-gatherer-naive-dataset"`.
    *   `create_dataset()` function:
        *   Initializes `Client()`.
        *   Creates a LangSmith dataset using `client.create_dataset()`.
        *   Adds examples (input-output pairs) to the dataset using `client.create_examples()`. Inputs are simple strings, outputs are expected agent responses.

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
        *   `test_tester_hello_response`: Tests the tester agent's response to a simple "hello" message.
        *   Uses `client.aevaluate()` with a dataset named `TESTER_AGENT_DATASET_NAME = "tester-agent-hello-dataset"`.
        *   Also uses the `correctness_evaluator`.
        *   `call_tester_agent` function prepares input and extracts output similarly to other integration tests.
    *   **`test_grumpy_agent.py`:**
        *   Tests the grumpy agent against a LangSmith dataset (e.g., `LANGSMITH_DATASET_NAME = "grumpy-failed-questions"`).
        *   Uses `LLMJudge` from `tests.testing.evaluators` to create a `correctness_evaluator` with a specific prompt for judging Grumpy's output.
        *   The `create_graph_caller` utility is used to wrap the Grumpy agent's graph for evaluation.

*   **`tests/testing/__init__.py`:**
    *   `get_logger()`: Utility to create a Python logger with a default format.
    *   `create_async_graph_caller(graph, process_inputs_fn=None, process_outputs_fn=None)`: (Note: name updated from `create_graph_caller`)
        *   A generic function to create an asynchronous caller for `graph.ainvoke`.
        *   Handles creating a unique `thread_id` for each call.
        *   Optionally processes inputs and outputs using provided functions.
        *   Returns the last message from the graph's output.

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
    *   `langgraph.json` can be used to set the default graph to open in Studio (e.g., by setting `default_graph`).
    *   The README provides a badge/link to open the project directly in LangGraph Studio using a GitHub URL.
*   **Adding New Agents:**
    1.  Copy the `src/agent_template/` directory and rename it.
    2.  Update package paths within the new agent's files (e.g., imports).
    3.  Add the new agent package to `pyproject.toml` under `[tool.poetry.packages]` or `[project.entry-points."langgraph.graphs"]` if using that mechanism for discovery.
    4.  Run `make run` and navigate to the new agent in LangGraph Studio.
*   **Memory Exploration:** LangGraph Studio UI allows reviewing saved memories (e.g., by clicking a "memory" button if the store is connected and UI supports it).


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .env.example                  # Example environment variables
├── .gitignore                    # Specifies intentionally untracked files
├── .github/
│   └── workflows/
│       └── checks.yml            # GitHub Actions CI workflow (lint, spell check, unit tests)
├── README.md                     # Project overview, setup, usage, and contribution guidelines
├── agent_memories/               # Agent-specific, static, long-term memory files (prompts, roles)
│   └── grumpy/
│       ├── review-coding.md      # Context for Grumpy's code review
│       ├── review-designing.md   # Context for Grumpy's design review
│       └── role.md               # Core operational rules and Mermaid diagram for Grumpy
├── langgraph.json                # LangGraph Studio configuration (e.g., default graph)
├── project_memories/             # Project-wide standards, global context
│   ├── PRD.md                    # Product Requirements Document: standards, tech stack, goals
│   └── global.md                 # High-level project mission, "Cursor" Memory Bank concept
├── pyproject.toml                # Project metadata, dependencies (for uv/Poetry), package definitions
├── src/                          # Source code for all agents and common utilities
│   ├── agent_template/           # Base template for creating new agents
│   │   ├── __init__.py
│   │   ├── configuration.py      # Dataclass for agent configuration
│   │   ├── graph.py              # LangGraph definition using State, tools, LLM
│   │   ├── memory.py             # Logic for loading static memories from JSON
│   │   ├── prompts.py            # Default system prompts
│   │   ├── state.py              # Dataclass for agent's graph state
│   │   ├── tools.py              # Agent tools (e.g., upsert_memory)
│   │   └── utils.py              # Utility functions (e.g., init_chat_model)
│   ├── architect/                # Architect agent: manages project design and documentation
│   │   └── prompts/v0.md         # Detailed system prompt for Architect
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
│       ├── output.py             # Pydantic models for Tester's structured output
│       ├── test-agent-system-prompt.md # Detailed system prompt for Tester
│       └── test-prompts/         # Example requirements for Tester (e.g., web-api.md)
└── tests/                        # Automated tests
    ├── datasets/                 # Scripts for creating LangSmith datasets
    │   └── requirement_gatherer_dataset.py
    ├── integration_tests/        # Integration tests for agents and full graph functionality
    │   ├── test_graph.py         # Tests agent_template memory
    │   ├── test_grumpy_agent.py
    │   ├── test_requirement_gatherer.py
    │   └── test_tester_agent.py
    ├── testing/                  # Test utilities, evaluators
    │   ├── evaluators.py         # LLM-based evaluators (e.g., LLMJudge)
    │   └── formatter.py          # Utilities for formatting/printing evaluation results
    └── unit_tests/               # Unit tests for isolated components
        └── test_configuration.py
```
