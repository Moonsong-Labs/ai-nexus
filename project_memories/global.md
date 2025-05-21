# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager (NEW)) working collaboratively. The Orchestrator agent's delegation mechanism to other agents (Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Task Manager) has been refactored. It now uses direct tool calls for each agent task instead of a generic `Delegate` tool. The Code Reviewer is consistently referred to as "Code Reviewer" (e.g., Orchestrator tool name `code_reviewer`).
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is `langmem`, providing semantic search capabilities over stored memories. `AgentGraph` can now automatically initialize and provide `SemanticMemory` and its tools to subclasses based on its configuration. The Tester agent, for instance, now includes logic to read from a `BaseStore` for contextual memories.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory.
    *   Orchestrator (REVISED): The `Delegate` tool has been removed. It now uses a set of specific tools:
        *   `requirements`: Invokes the Requirement Gatherer agent/stub.
        *   `architect`: Invokes the Architect agent/stub.
        *   `task_manager` (NEW): Invokes the Task Manager agent/stub.
        *   `coder_new_pr`: Invokes the Coder agent/stub for new pull requests.
        *   `coder_change_request`: Invokes the Coder agent/stub for changes to existing pull requests.
        *   `tester`: Invokes the Tester agent/stub.
        *   `code_reviewer`: Invokes the Code Reviewer agent/stub.
        *   `memorize`: (Replaces its previous `store_memory` tool concept) For persisting information, created by `tools.memorize`.
        *   `summarize`: (NEW) For the Orchestrator to output a final summary of its operations.
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools (`manage_memory`, `search_memory`) from the `AgentGraph`-managed `SemanticMemory` instance (via `self.memory.get_tools()`).
    *   Requirement Gatherer: Uses a custom `memorize` tool (created by `create_memorize_tool`) and `human_feedback` tool.
    *   Tester: Its custom `upsert_memory` tool has been removed.
    *   Code Reviewer: Can use GitHub tools like `get_pull_request_diff` and `create_pull_request_review`.
    *   Architect (NEW, REVISED): Uses `create_memorize_tool` and `create_recall_tool` for memory, file system tools (`read_file`, `create_file`, `list_files`), and a new `summarize` tool (from `architect.tools.summarize`) for outputting its final architecture summary. Its `use_human_ai` configuration field has been removed. Its previous `upsert_memory` tool has been removed.
    *   Task Manager (REVISED): Uses file system tools. Integrated into Orchestrator.
    *   General: Tools like `file_dump` can be used by agents.
5.  **System Prompts (REVISED):** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols. System prompts are now typically part of agent-specific `Configuration` classes.
    *   Orchestrator (REVISED): Its system prompt, dynamically loaded from markdown files in `src/orchestrator/memory/`, has been updated to reflect its new toolset (direct agent calls like `requirements`, `architect`, `task_manager`, `coder_new_pr`, `coder_change_request`, `tester`, `code_reviewer`, plus `memorize` and `summarize`) and refined workflow logic (e.g., using the `summarize` tool when no tasks are pending). The static `ORCHESTRATOR_SYSTEM_PROMPT` string in `src/orchestrator/prompts.py` has been removed.
    *   Task Manager (NEW): System prompt defined in `task_manager.configuration.Configuration` via `task_manager_system_prompt` (which defaults to `prompts.SYSTEM_PROMPT` from `src/task_manager/prompts.py`).
    *   Other agents: System prompts are accessed by the agent's graph logic (e.g., in custom `call_model` implementations). The Tester agent features enhanced prompt management (e.g., its graph logic in `src/tester/graph.py` now directly uses `agent_config.system_prompt` for formatting its system message). The Code Reviewer agent has `PR_REVIEW_PROMPT`. The Architect agent has `architect_system_prompt` (REVISED to include a dedicated "Summarize" step using its new `summarize` tool before finalization).
6.  **Configuration Management (REVISED):** Agents have configurable parameters, including LLM models, system prompts, and memory settings.
    *   `MemoryConfiguration` (`common.components.memory.MemoryConfiguration`).
    *   Common `AgentConfiguration` (`src/common/configuration.py`).
    *   Agent-specific `Configuration` dataclasses subclass `AgentConfiguration`.
    *   Architect: `src/architect/configuration.py`'s `Configuration` class no longer defines `use_human_ai`.
    *   Code Reviewer: `CodeReviewerInstanceConfig` dataclass.
    *   Task Manager (`src/task_manager/configuration.py` - REVISED): `Configuration` class includes `use_stub: bool`, `use_human_ai: bool`, and `task_manager_system_prompt: str`.

## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and `AgentGraph` integration):** The project has integrated the `langmem` library to provide a robust and queryable semantic memory system.
*   **`MemoryConfiguration` (`common.components.memory.MemoryConfiguration`):** A dedicated dataclass to hold memory settings.
*   **`AgentConfiguration` (`common.configuration.AgentConfiguration` - NEW, replaces `BaseConfiguration`):** Now embeds a `MemoryConfiguration` instance.
*   **`SemanticMemory` (`common.components.memory.SemanticMemory` - REVISED):**
    *   Its constructor now accepts `memory_config: Optional[MemoryConfiguration]`.
*   **`AgentGraph` (`common.graph.AgentGraph` - REVISED):**
    *   Can automatically initialize a `SemanticMemory` instance.
*   **Storage:** Memories are stored in a `BaseStore`.
*   **Namespace:** Memories are namespaced.
*   **Tools:**
    *   Orchestrator (REVISED): Uses direct tools `requirements`, `architect`, `task_manager` (NEW), `coder_new_pr`, `coder_change_request`, `tester`, `code_reviewer` (which invoke sub-graphs/stubs), `memorize` (for memory persistence), and `summarize`.
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools from `AgentGraph`.
    *   Requirement Gatherer: Uses `create_memorize_tool` and `human_feedback` tool.
    *   Tester: Custom `upsert_memory` tool removed.
    *   Code Reviewer: Uses GitHub tools.
    *   Architect (NEW, REVISED): Uses `create_memorize_tool`, `create_recall_tool`, file system tools, and a new `summarize` tool. `use_human_ai` removed from its config.
*   **Static Memories:** JSON files in `.langgraph/static_memories/` can be loaded.
*   **Shift:** Externalized memory via `langmem`, integrated via `AgentGraph` and configured through `AgentConfiguration` and `MemoryConfiguration`.


## 3. Project-Level Standards & Goals (`project_memories/PRD.md`)

This file outlines the overarching standards and technological choices for the AI Nexus project.
*   (No changes from PR)


## 4. General Agent Architecture

AI Nexus employs a few architectural patterns for its agents:

**4.1. `agent_template` based Architecture (e.g., Grumpy) - REVISED**
*   (No changes from PR)

**4.2. `AgentGraph` based Architecture (REVISED - e.g., Orchestrator, Requirement Gatherer, Coder, Task Manager (NEW), AgentTemplateGraph, Tester, Architect)**
*   (No direct changes to base `AgentGraph` or `AgentConfiguration` structure from this PR, but Orchestrator's implementation using it is heavily revised, and Task Manager is now an example)

**4.3. Custom `StateGraph` Architecture (e.g., Code Reviewer - NEW)**
*   (No changes from PR)


## 5. Specific Agent Details

#### 5.1. Orchestrator (`src/orchestrator/`) (REVISED)
*   **Architecture:** Uses the `AgentGraph` pattern. `OrchestratorGraph` in `src/orchestrator/graph.py` subclasses `common.graph.AgentGraph`.
*   **Configuration (`src/orchestrator/configuration.py` - REVISED):**
    *   The `OrchestratorConfiguration` class (defined in this file, subclasses `common.configuration.AgentConfiguration`) specifies the configuration for the Orchestrator agent itself and how it integrates with its sub-agents. It includes fields for:
        *   `requirements_agent` (type `RequirementsAgentConfig`)
        *   `architect_agent` (type `ArchitectAgentConfig`)
        *   `task_manager_agent` (NEW, type `TaskManagerAgentConfig`)
        *   `coder_new_pr_agent` (type `SubAgentConfig`)
        *   `coder_change_request_agent` (type `SubAgentConfig`)
        *   `tester_agent` (type `SubAgentConfig`)
        *   `code_reviewer_agent` (type `SubAgentConfig`)
    *   These sub-agent configurations (e.g., `SubAgentConfig`, `ArchitectAgentConfig`, `RequirementsAgentConfig`, `TaskManagerAgentConfig` (NEW), also defined/imported in this module) typically allow specifying whether to use a full agent or a stub, and can contain agent-specific nested configurations.
    *   As an example of nested configuration, the `ArchitectAgentConfig` contains a nested `config: architect.configuration.Configuration` field, and this nested Architect configuration is what reflects changes like the removal of `use_human_ai` from the Architect's own configuration file. The new `TaskManagerAgentConfig` similarly contains a nested `config: task_manager.configuration.Configuration`.
*   **State (`src/orchestrator/state.py` - REVISED):** Added `summary: str = ""` field to its `State` dataclass.
*   **Graph (`src/orchestrator/graph.py` - REVISED):**
    *   The graph structure has been refactored to use a `ToolNode` for invoking all agent-specific tasks and other utilities.
    *   The `_create_orchestrate` node is renamed to `_create_orchestrator`.
    *   The previous delegation logic (`_create_delegate_to` and individual agent node creators like `_create_requirements_node`, `_create_architect_node`, etc.) has been removed.
    *   The LLM is now bound with a new set of tools (see Orchestrator Tools under Key Concepts or Tools section below). This now includes a `task_manager` tool.
    *   Conditional logic (`_create_orchestrate_condition`) routes from the main `orchestrator` (model call) node to the `ToolNode` if tool calls are present, or to `END` if a `summary` is available in the state, otherwise back to the `orchestrator` node.
    *   Sub-agent graphs (or their stubs, including for Task Manager) are passed to tool factory functions which create the tools bound to the Orchestrator's LLM.
*   **Stubs (`src/orchestrator/stubs/__init__.py` - REVISED):**
    *   The `StubGraph` base class's `run_fn` is now expected to return a dictionary that includes a `summary` field. The graph built by `StubGraph` now adds an edge from its "run" node to `END`.
    *   `RequirementsGathererStub`, `ArchitectStub`, `CoderNewPRStub`, `CoderChangeRequestStub` are updated to align with this, providing a `summary` in their output.
    *   `TesterStub` (NEW class, subclasses `StubGraph`): Replaces the previous simple `stubs.tester` function.
    *   `CodeReviewerStub` (NEW class, subclasses `StubGraph`): Replaces the previous simple `stubs.reviewer` function.
    *   `TaskManagerStub` (NEW class, subclasses `StubGraph`): Provides a stub for the Task Manager agent.
    *   The old simple stub functions (`stubs.tester`, `stubs.reviewer`, `stubs.memorizer`) have been removed.
*   **Tools (`src/orchestrator/tools.py` - REVISED):**
    *   The `Delegate` tool has been removed.
    *   The `store_memory` tool has been effectively replaced by the `memorize` tool. Its `origin` parameter's type hint is updated to include `code_reviewer`.
    *   New tool factory functions are introduced:
        *   `create_requirements_tool(agent_config, requirements_graph)`: Creates the `requirements` tool.
        *   `create_architect_tool(agent_config, architect_graph)`: Creates the `architect` tool.
        *   `create_task_manager_tool(agent_config, task_manager_graph)` (NEW): Creates the `task_manager` tool.
        *   `create_coder_new_pr_tool(agent_config, coder_new_pr_graph)`: Creates the `coder_new_pr` tool.
        *   `create_coder_change_request_tool(agent_config, coder_change_request_graph)`: Creates the `coder_change_request` tool.
        *   `create_tester_tool(agent_config, tester_graph)`: Creates the `tester` tool.
        *   `create_code_reviewer_tool(agent_config, code_reviewer_graph)`: Creates the `code_reviewer` tool.
    *   These tools take `content` (and other injected args like `tool_call_id`, `state`, `config`), invoke the respective sub-graph (or stub), and return the `summary` from the sub-graph's result as the tool's output.
    *   A new `summarize` tool is added: it takes a `summary` string, prints it, and updates the Orchestrator's state with this `summary` and a corresponding `ToolMessage`.
*   **Prompts (`src/orchestrator/prompts.py` and `src/orchestrator/memory/` - REVISED):**
    *   `src/orchestrator/prompts.py`: The static `ORCHESTRATOR_SYSTEM_PROMPT` string definition has been removed. The `get_prompt()` function continues to load prompt content from markdown files.
    *   `src/orchestrator/memory/absolute.md`, `process.md`, `project_states.md`, `team.md`: These markdown files, which constitute the Orchestrator's system prompt, have been significantly updated to reflect the new toolset (direct agent invocation tools including `task_manager`, `memorize`, `summarize`) and the refined operational workflow (e.g., explicit instruction to use the `summarize` tool when no tasks are pending). `project_states.md` now includes a "Create tasks" step and an updated Mermaid flowchart. `team.md` now includes a section for the "Task Manager" agent.

#### 5.2. Architect (`src/architect/`) (REWORKED, REVISED)
*   **Configuration (`src/architect/configuration.py` - REVISED):**
    *   The `use_human_ai: bool = False` field has been removed.
*   **State (`src/architect/state.py` - REVISED):** Added `summary: str = ""` field.
*   **Graph (`src/architect/graph.py` - REVISED):**
    *   The Architect's graph now includes a `summarize` tool (from `architect.tools.summarize`) in its set of available tools.
*   **Tools (`src/architect/tools.py` - REVISED):**
    *   Added a new `summarize` tool. This tool takes a `summary` string, prints it, and returns a `Command` to update the agent's state with a `ToolMessage` containing the summary and updates the `summary` field in the state.
*   **Prompts (`src/architect/prompts.py` - REVISED):**
    *   The Architect's system prompt (`architect_system_prompt`) has been updated to include a new "Summarize" step. This step instructs the agent to write a `summary` of the architecture and call its `summarize` tool before proceeding to the "Finalize" step.

#### 5.3. Coder (`src/coder/`)
*   **State (`src/coder/state.py` - REVISED):**
    *   Changed from `TypedDict` to `@dataclass(kw_only=True)`.
    *   Added `summary: str = ""` field.
*   **Graph (`src/coder/graph.py` - MINOR UPDATE):** Accesses state messages via `state.messages` instead of `state["messages"]` due to state being a dataclass.

#### 5.4. Code Reviewer (`src/code_reviewer/`) (REVISED)
*   **State (`src/code_reviewer/state.py` - REVISED):** Added `summary: str = ""` field.
*   **Tool Naming:** Referred to as `code_reviewer` in Orchestrator's tools and stubs.

#### 5.5. Tester (`src/tester/`) (REWORKED)
*   **State (`src/tester/state.py` - REVISED):** Added `summary: str = ""` field.
*   **Graph (`src/tester/graph.py` - REVISED):**
    *   The internal `_create_call_model` function, responsible for preparing and invoking the LLM, now explicitly accepts the agent's `Configuration` (as `agent_config`).
    *   The system prompt used in `_create_call_model` is now directly sourced from `agent_config.system_prompt`, improving how the configured prompt is passed and utilized within the graph's execution logic.

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`) (REVISED)
*   **Graph (`src/requirement_gatherer/graph.py` - MINOR UPDATE):** The conditional logic in `_create_gather_requirements` for routing to the tool node is updated to `if state.messages and state.messages[-1].tool_calls:`.

#### 5.7. Grumpy (`src/grumpy/`)
*   (No changes from PR)

#### 5.8. Task Manager (`src/task_manager/`) (REVISED & INTEGRATED)
*   **Role:** Creates tasks based on project architecture. Integrated into the Orchestrator.
*   **Architecture:** Uses the `AgentGraph` pattern (`TaskManagerGraph` in `src/task_manager/graph.py`).
*   **Configuration (`src/task_manager/configuration.py` - REVISED):**
    *   `Configuration` class (subclasses `common.configuration.AgentConfiguration`).
    *   Added `use_stub: bool = True` (default).
    *   Added `use_human_ai: bool = False` (default).
    *   `task_manager_system_prompt: str` field, defaults to `prompts.SYSTEM_PROMPT` from `src/task_manager/prompts.py`.
    *   `model: str` field, defaults to `TASK_MANAGER_MODEL`.
*   **State (`src/task_manager/state.py` - REVISED):** Added `summary: str = ""` field. (Used by `TaskManagerStub` and consistent with other agents).
*   **Tools:** Uses file system tools (as previously noted). The Orchestrator uses a `task_manager` tool to invoke this agent.
*   **Prompts (`src/task_manager/prompts.py`):** Contains `SYSTEM_PROMPT` used by the agent.


## 6. Testing Framework (`tests/`) (UPDATED)

*   **`tests/integration_tests/test_orchestrator.py` (UPDATED):**
    *   Tests updated to reflect the Orchestrator's new tool usage (e.g., `memorize` instead of `store_memory`, and direct agent tool calls like `code_reviewer` instead of generic `Delegate`).
*   **Smoke Tests (NEW):**
    *   **`tests/smoke/langgraph_dev/`**: Contains a smoke test for the `langgraph dev` CLI and its UI.
        *   **Purpose**: Verifies basic end-to-end functionality of launching `langgraph dev`, interacting with the LangGraph Studio UI for the `orchestrator` agent, and ensuring it reaches an expected state (e.g., human interrupt for the Requirement Gatherer).
        *   **Technology**: Node.js, TypeScript, Puppeteer.
        *   **Execution**:
            1.  Launches the `langgraph dev` server for the AI Nexus project.
            2.  Uses Puppeteer to open a browser and navigate to the LangGraph Studio (`https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8080`).
            3.  Selects the `orchestrator` graph.
            4.  Inputs a test message (e.g., "I want to build a website").
            5.  Submits the message and waits for the graph to process.
            6.  Asserts that the graph execution pauses for a human interrupt (e.g., from the Requirement Gatherer).
        *   **Artifacts**: Produces `langgraph-test-result.png` (a screenshot of the UI state) which is uploaded by the CI workflow.
        *   **Configuration**: Requires `GOOGLE_API_KEY` (via `.env` file at project root) for the `langgraph dev` server.
*   (Other test files as previously described, or minor updates not impacting core logic)


## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`) (UPDATED)

*   **`Makefile` (UPDATED):**
    *   Changed `demo` target to `demo-%` (e.g., `make demo-ai`, `make demo-human`) for explicit mode selection when running the demo orchestration script (`src/demo/orchestrate.py`).
*   **`README.md` (UPDATED):**
    *   Updated "Local Demo" instructions to use the new `make demo-ai` and `make demo-human` commands.
*   **CI/CD (GitHub Actions - `.github/workflows/`):**
    *   `checks.yml` (UPDATED):
        *   Includes jobs for linting, type checking, unit tests, and integration tests.
        *   **New `smoke-test` job**:
            *   Runs on `ubuntu-latest`.
            *   Checks out the code.
            *   Creates an `.env` file with `GOOGLE_API_KEY=${{ secrets.GEMINI_API_KEY }}` at the project root.
            *   Installs `uv` and Python dependencies (`make deps`).
            *   Navigates to `tests/smoke/langgraph_dev`, installs Node.js dependencies (`npm i`), and runs the smoke test (`npm test`).
            *   Uploads `tests/smoke/langgraph_dev/langgraph-test-result.png` as an artifact with a 10-day retention period if the test runs (regardless of pass/fail).
    *   `compile-check.yml`: Ensures the LangGraph graphs can be compiled.
    *   `update_project_memory.yml`: (As previously described)
*   **Dependency Management (`pyproject.toml` - UPDATED):**
    *   Dependency version specifiers have been changed from `>=` (greater than or equal to) to `~=` (compatible release, e.g., `~=1.2.3` implies `>=1.2.3` and `<1.3.0`). This change restricts updates to patch versions for the specified minor versions of main and development dependencies, aiming to enhance build stability.
    *   The `[tool.setuptools]` `packages` list within `pyproject.toml` has also been reformatted for improved readability.
*   **LangSmith Tracing (NEW aspect for demo):**
    *   The demo script (`src/demo/orchestrate.py`) now integrates LangSmith tracing, providing a trace URL for each run. This includes user identification and run metadata.
*   (Other workflow aspects like `pytest.ini` setup as previously described, or minor updates not impacting core logic)


## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/
│   └── rules/
│       └── read-project-memories.mdc
├── .env.example
├── .gitignore
├── .vscode/
│   └── launch.json
├── .github/
│   └── workflows/
│       ├── checks.yml            # UPDATED: Added smoke-test job
│       ├── compile-check.yml
│       └── update_project_memory.yml
├── Makefile                      # UPDATED: Changed demo target to demo-% (e.g., demo-ai, demo-human).
├── README.md                     # UPDATED: Local demo instructions updated.
├── agent_memories/
│   └── grumpy/
├── langgraph.json
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml                # UPDATED: Dependency constraints changed to `~=`; package list reformatted.
├── pytest.ini                    # UPDATED: Minor formatting
├── scripts/
│   └── generate_project_memory.sh
│   └── update_project_memory_from_pr.sh
├── src/
│   ├── agent_template/
│   │   ├── __init__.py
│   │   ├── configuration.py
│   │   ├── graph.py
│   │   ├── prompts.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── architect/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses common.configuration.AgentConfiguration, defines architect_system_prompt, use_human_ai removed
│   │   ├── graph.py              # UPDATED: Added tools.summarize to the agent's toolset
│   │   ├── prompts.py            # UPDATED: System prompt includes new "Summarize" step and use of summarize tool
│   │   ├── state.py              # UPDATED: summary field added
│   │   └── tools.py              # UPDATED: Added new 'summarize' tool
│   ├── code_reviewer/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── lg_server.py
│   │   ├── prompts.py
│   │   ├── state.py              # UPDATED: summary field added
│   │   └── system_prompt.md
│   ├── coder/
│   │   ├── __init__.py
│   │   ├── graph.py              # UPDATED: Minor state access change (state.messages)
│   │   ├── lg_server.py
│   │   ├── mocks.py
│   │   ├── prompts.py
│   │   ├── state.py              # UPDATED: Now a dataclass, summary field added
│   │   ├── tools.py
│   │   └── README.md
│   ├── common/
│   │   ├── components/
│   │   │   ├── github_mocks.py
│   │   │   ├── github_tools.py
│   │   │   └── memory.py
│   │   ├── configuration.py
│   │   ├── graph.py
│   │   └── utils/
│   ├── demo/
│   │   └── orchestrate.py        # MOVED & RENAMED from src/orchestrator/test.py; UPDATED to use create_runnable_config and compiled_graph.ainvoke. UPDATED: Imports TaskManagerAgentConfig, TaskManagerConfiguration; configures task_manager_agent; prints task_manager tool calls. UPDATED: Integrates LangSmith tracing (prints trace URL, uses @traceable). The demo script's configuration for the Orchestrator now sets `use_stub=False` by default for the Requirements, Architect, Coder New PR, and Coder Change Request agents. The Task Manager agent remains configured with `use_stub=True` in the demo.
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration. Defines OrchestratorConfiguration including fields for sub-agent configs (e.g., ArchitectAgentConfig, TaskManagerAgentConfig (NEW), SubAgentConfig for coders, tester, reviewer).
│   │   ├── graph.py              # UPDATED: Major refactor to use ToolNode, direct agent tool calls (requirements, architect, task_manager (NEW), coder_new_pr, coder_change_request, tester, code_reviewer), memorize, and summarize tools. Removed Delegate pattern.
│   │   ├── memory/
│   │   │   ├── absolute.md       # UPDATED: Reflects new tools and workflow
│   │   │   ├── process.md        # UPDATED: Reflects new tools and workflow
│   │   │   ├── project_states.md # UPDATED: Reflects new tools, workflow (incl. task creation), includes Mermaid diagram
│   │   │   └── team.md           # UPDATED: Reflects new tools (direct calls, memorize, summarize), includes Task Manager agent
│   │   ├── prompts.py            # UPDATED: Static ORCHESTRATOR_SYSTEM_PROMPT string removed, get_prompt() loads from memory files.
│   │   ├── state.py              # UPDATED: summary field added
│   │   ├── stubs/
│   │   │   └── __init__.py       # UPDATED: StubGraph base class modified (returns summary, END edge). RequirementsGathererStub, ArchitectStub, CoderNewPRStub, CoderChangeRequestStub updated. New TesterStub, CodeReviewerStub, TaskManagerStub (NEW) classes. Old simple stub functions removed. Imports TaskManagerState.
│   │   ├── tools.py              # UPDATED: Delegate tool removed. store_memory effectively replaced by memorize. New tool factories (create_requirements_tool, etc.) for direct agent invocation, including create_task_manager_tool (NEW). New summarize tool. Imports TaskManagerGraph, TaskManagerState.
│   │   └── utils.py              # ADDED: Contains utility functions like split_model_and_provider.
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py
│   │   ├── graph.py              # UPDATED: Renamed to RequirementsGraph, uses AgentConfiguration, new AgentGraph init; helpers receive agent_config; memorize tool now created via create_memorize_tool(self._agent_config); minor conditional logic update in _create_gather_requirements
│   │   ├── prompts.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── task_manager/
│   │   ├── configuration.py      # UPDATED: Added use_stub, use_human_ai fields; uses prompts.SYSTEM_PROMPT.
│   │   ├── graph.py
│   │   ├── prompts.py
│   │   ├── state.py              # UPDATED: summary field added
│   │   └── tools.py
│   └── tester/
│       ├── __init__.py
│       ├── configuration.py
│       ├── deprecated/
│       │   ├── deprecated-test-agent-system-prompt.md
│       │   └── test-agent-analyze-requirements-workflow-stage.md
│       ├── graph.py
│       ├── prompts.py
│       ├── state.py              # UPDATED: New WorkflowStage enum, State includes workflow_stage, summary field added
│       ├── test-agent-system-prompt.md
│       ├── test-agent-testing-workflow-stage.md
│       └── tools.py
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py
    │   └── task_manager_dataset.py
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py
    │   ├── eval_coder.py
    │   ├── test_graph.py
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py    # UPDATED: Tests reflect new Orchestrator tool usage (e.g., memorize, direct agent calls like code_reviewer).
    │   ├── test_requirement_gatherer.py
    │   ├── test_task_manager.py
    │   ├── test_tester_agent.py
    │   └── inputs/
    │       └── api_rust/
    │           ├── featuresContext.md
    │           ├── progress.md
    │           ├── projectRequirements.md
    │           ├── projectbrief.md
    │           ├── securityContext.md
    │           ├── systemPatterns.md
    │           ├── techContext.md
    │           └── testingContext.md
    ├── smoke/                      # ADDED
    │   └── langgraph_dev/          # ADDED
    │       ├── .gitignore          # ADDED
    │       ├── package.json        # ADDED
    │       ├── src/                # ADDED
    │       │   └── index.ts        # ADDED
    │       └── tsconfig.json       # ADDED
    ├── testing/
    │   ├── __init__.py
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py
```
