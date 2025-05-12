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
    *   **openevals:** Suggests involvement in evaluating language models.
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
*   **Role:** Expert software engineer responsible for architecting a project, not writing code. Receives project needs, coordinates other AI agents. Manages project documentation.
*   **Key Prompt (`src/architect/prompts/v0.md`):** (Remains the same detailed prompt).
*   **Structure:** Follows the `agent_template` pattern.
    *   `configuration.py`: Standard, uses `prompts.SYSTEM_PROMPT`. Default model likely updated if inheriting from template. Includes `use_static_mem`.
    *   `graph.py`: Now uses the `Agent` class, `ToolNode`, and `tools_condition` flow from the updated `agent_template`. Relies on `langmem` tools (`manage_memory`, `search_memory`) and `file_dump` provided by the `Agent` class, instead of the previous direct `upsert_memory` tool.
    *   `state.py`: Standard `State` with `messages` and `user_id`.
    *   `tools.py`: Defines utility tools like `file_dump`. `upsert_memory` is removed. Memory tools come from `Agent`.
    *   `agent.py`: Contains the `Agent` class instance for this agent.

#### 5.3. Coder (`src/coder/`)
*   (No changes mentioned in PR - primarily uses GitHub tools, not memory tools. Unaffected).

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
*   (No changes mentioned in PR - uses structured output, no memory tools. Unaffected by `langmem` integration).

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

*   **Common Test Setup:** (Remains similar, but graph compilation might not always need explicit `MemorySaver` or `InMemoryStore` if the graph manages its state internally or via `langmem`'s store).
*   **`tests/integration_tests/`:**
    *   **`test_graph.py`:** **REWRITTEN:**
        *   Tests the new semantic memory functionality of the `agent_template` graph (`langmem`).
        *   Includes tests to assert the correct `category` (`knowledge`, `rule`, `procedure`) is used when storing memories via the `manage_memory` tool.
        *   Includes a test for the `memory_dump` tool, verifying that it creates a non-empty JSON dump file in a specified directory after memories have been stored.
        *   No longer tests the old `upsert_memory` logic or direct `InMemoryStore` inspection for memories under `("memories", user_id)`.
    *   **`test_requirement_gatherer.py`:** (Test logic remains, but the underlying agent graph uses the new memory system).
    *   **`test_tester_agent.py`:** (Test logic remains, agent is unaffected).
    *   **`test_grumpy_agent.py`:** (Test logic remains, but the underlying agent graph uses the new memory system).
*   **`tests/testing/evaluators.py`:** (Remains the same - `LLMJudge` for correctness evaluation).
*   **`tests/testing/__init__.py`:** (`create_async_graph_caller` likely still used).
*   **Makefile Target:** Added `make test-memory-graph` to run the tests in `tests/integration_tests/test_graph.py`.


## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`)

*   **Environment Management:** `uv`.
*   **Task Runner:** `Makefile` provides targets:
    *   `make run`, `make sync`, `make deps`, `make clean`, `make lint`, `make fmt`, `make spell_check`, `make spell_fix`, `make check`, `make test_unit`, `make test_integration`, `make test`, `make test-tester`, `make test-memory-graph` (**NEW**).
*   **Configuration:** `.env` file. `GOOGLE_API_KEY` required. Optional GitHub and LangSmith variables.
*   **CI/CD (GitHub Actions):** (`checks.yml`) Runs lint, spell check, unit tests. Integration tests might run separately.
*   **LangGraph Studio:** Supported.
*   **Adding New Agents:** Process remains similar, but new agents should use the updated `agent_template` with the `Agent` class and `langmem`.
*   **Memory Usage (README):** **NEW** section added to `README.md` explaining how to add semantic memory to an agent using `SemanticMemory` from `src.common.components.memory`, initializing it, and binding its tools to the LLM.


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
│       ├── review-coding.md
│       ├── review-designing.md
│       └── role.md
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md                 # Describes original "Memory Bank" concept
├── pyproject.toml                # Added langmem dependency
├── src/
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
│   ├── architect/                # Architect agent (inherits template changes)
│   │   └── prompts/v0.md
│   ├── code_reviewer/            # Code Reviewer agent (inherits template changes)
│   │   └── system_prompt.md
│   ├── coder/                    # Coder agent (unaffected by memory changes)
│   │   ├── mocks.py
│   │   └── README.md
│   ├── common/                   # Common utilities shared across agents
│   │   ├── components/           # NEW: Reusable components
│   │   │   ├── __init__.py
│   │   │   └── memory.py         # NEW: SemanticMemory class, static loading, tool creation
│   │   └── utils/
│   ├── grumpy/                   # Grumpy agent (inherits template changes)
│   ├── orchestrator/             # Orchestrator agent (likely unaffected)
│   │   ├── memory/
│   │   └── stubs/
│   ├── requirement_gatherer/     # Requirement Gatherer agent (inherits template changes, graph needs adaptation)
│   └── tester/                   # Tester agent (unaffected by memory changes)
│       ├── README.md
│       ├── configuration.py
│       ├── graph.py
│       ├── output.py
│       ├── state.py
│       ├── test-agent-system-prompt.md
│       ├── test-prompts/
│       │   ├── web-api-simple.md
│       │   └── web-api.md
│       ├── tools.py
│       └── utils.py
└── tests/
    ├── datasets/
    │   └── requirement_gatherer_dataset.py
    ├── integration_tests/
    │   ├── test_graph.py         # REWRITTEN: Tests semantic memory categories and dump tool
    │   ├── test_grumpy_agent.py
    │   ├── test_requirement_gatherer.py
    │   └── test_tester_agent.py
    ├── testing/
    │   ├── __init__.py
    │   └── evaluators.py
    └── unit_tests/
        └── test_configuration.py
```
