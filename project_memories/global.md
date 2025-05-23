# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents. The system now includes robust project management capabilities, allowing the tracking and utilization of project names and paths across various agent workflows.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager (NEW)) working collaboratively. The Orchestrator agent's delegation mechanism to other agents (Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Task Manager) has been refactored. It now uses direct tool calls for each agent task instead of a generic `Delegate` tool. The Code Reviewer is consistently referred to as "Code Reviewer" (e.g., Orchestrator tool name `code_reviewer`). A `Project` object is now passed and updated across agent states to maintain consistent project context. Agent stubs now support dynamic, cycling messages for more flexible scenario testing.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is `langmem`, providing semantic search capabilities over stored memories. `AgentGraph` can now automatically initialize and provide `SemanticMemory` and its tools to subclasses based on its configuration. The Tester agent, for instance, now includes logic to read from a `BaseStore` for contextual memories.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory.
    *   Orchestrator (REVISED): The `Delegate` tool has been removed. It now uses a set of specific tools:
        *   `requirements`: Invokes the Requirement Gatherer agent/stub. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result.
        *   `architect`: Invokes the Architect agent/stub. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result.
        *   `task_manager` (NEW): Invokes the Task Manager agent/stub. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result.
        *   `coder_new_pr`: Invokes the Coder agent/stub for new pull requests.
        *   `coder_change_request`: Invokes the Coder agent/stub for changes to existing pull requests.
        *   `tester`: Invokes the Tester agent/stub. **UPDATED**: This tool now passes the Orchestrator's `project` state to the Tester agent's state.
        *   `code_reviewer`: Invokes the Code Reviewer agent/stub.
        *   `memorize`: (Replaces its previous `store_memory` tool concept) For persisting information, created by `tools.memorize`.
        *   `summarize`: (NEW) For the Orchestrator to output a final summary of its operations, now provided by `common.tools.summarize`.
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools (`manage_memory`, `search_memory`) from the `AgentGraph`-managed `SemanticMemory` instance (via `self.memory.get_tools()`).
    *   Requirement Gatherer: Uses a custom `memorize` tool (created by `create_memorize_tool`) and `human_feedback` tool. Its `summarize` tool is now provided by `common.tools.summarize`. A new `set_project` tool is available to set the active project name and path.
    *   Tester: Its custom `upsert_memory` tool has been removed. **UPDATED**: Now includes `common.tools.summarize`, `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file` in its toolset.
    *   Code Reviewer: Can use GitHub tools like `get_pull_request_diff` and `create_pull_request_review`.
    *   Architect (NEW, REVISED): Uses `create_memorize_tool`, `create_recall_tool`, `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`, and a new `summarize` tool (now provided by `common.tools.summarize`) for outputting its final architecture summary. Its `use_human_ai` configuration field has been removed. Its previous `upsert_memory` tool has been removed.
    *   Task Manager (REVISED): Uses `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`. Now also uses the `summarize` tool (from `common.tools.summarize`).
    *   Coder (REVISED): **UPDATED**: Now includes the `get_latest_pr_workflow_run` tool. The `create_issue_comment` tool is *not* provided to the Coder agent.
    *   General: Tools like `file_dump` can be used by agents. A common `summarize` tool is now available in `src/common/tools/summarize.py` for reuse across agents. New common file system tools (`common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`) are available for reuse. **UPDATED**: New common GitHub tools `common.components.github_tools.create_issue_comment` (for commenting on issues/PRs) and `common.components.github_tools.get_latest_pr_workflow_run` (for fetching workflow run logs) are now available. Agent outputs are now enhanced with formatted, actor-labeled messages for improved clarity.
5.  **System Prompts (REVISED):** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols. System prompts are now typically part of agent-specific `Configuration` classes.
    *   Orchestrator (REVISED): Its system prompt, dynamically loaded from markdown files in `src/orchestrator/memory/`, has been updated to reflect its new toolset (direct agent calls like `requirements`, `architect`, `task_manager`, `coder_new_pr`, `coder_change_request`, `tester`, `code_reviewer`, plus `memorize` and `summarize`) and refined workflow logic (e.g., using the `summarize` tool when no tasks are pending). The static `ORCHESTRATOR_SYSTEM_PROMPT` string in `src/orchestrator/prompts.py` has been removed.
    *   Task Manager (NEW, REVISED): System prompt defined in `task_manager.configuration.Configuration` via `task_manager_system_prompt` (which defaults to `prompts.SYSTEM_PROMPT` from `src/task_manager/prompts.py`). This prompt has been significantly updated to include stricter guidelines for task splitting (smaller tasks, buildable deliverables), mandatory testing requirements (unit, integration, edge cases), early CI/CD setup (GitHub Actions), expanded task metadata (contextual, technical, security, testing info), and reinforced roadmap creation and task sequencing rules (repo init -> project setup -> CI -> features). The prompt now dynamically references the active project name (`{project_name}`) and path (`{project_path}`). **UPDATED**: The prompt's list of required files has been updated: `techContext.md` is now `techPatterns.md`, `featuresContext.md` is now `codingContext.md`, and `securityContext.md` has been removed from the list. The prompt's internal descriptions and extraction guidelines for these files have been updated accordingly, including the removal of specific security context extraction instructions and the renaming of `relatedFeatureContext` to `relatedCodingContext` in the task metadata schema. The count of "Additional Context Files" has been adjusted from 4-8 to 4-7. **UPDATED**: The prompt now explicitly states that it will receive input documents in `{project_path}` and the project name is `{project_name}`. It also includes a new mandatory instruction to write a `summary` of the created tasks and call the `summarize` tool. The prompt now states that it will verify "all seven required files" (previously "eight").
    *   Architect (REVISED): Its system prompt (`architect_system_prompt`) now dynamically references the active project directory (`{project_dir}`). **UPDATED**: The prompt's description of the core project files and their interdependencies (including the Mermaid flowchart and numbered list) has been updated. `projectRequirements.md` is now explicitly listed as a core file and is positioned as an intermediary document between `projectbrief.md` and `systemPatterns.md`/`techPatterns.md`. The description of `projectbrief.md` is now more focused on its foundational role. The numbering of core files in the prompt has been adjusted (e.g., `systemPatterns.md` is now 3, `techPatterns.md` is 4, `progress.md` is 5). **UPDATED**: The prompt now includes an instruction to ensure the `{project_dir}` exists and create it if necessary before writing new files, specifically mentioning the `create_directory` tool. It also clarifies that `list_files` should be used on the `{project_dir}` directory and that `create_file` should write files under `{project_dir}`.
    *   Requirement Gatherer (REVISED): Its system prompt now includes an explicit instruction to use the `set_project` tool if no project name is provided.
    *   Coder (REVISED): The `NEW_PR_SYSTEM_PROMPT` now refers to the "base branch" instead of a specific branch name like "main".
    *   Other agents: System prompts are accessed by the agent's graph logic (e.g., in custom `call_model` implementations). The Tester agent features enhanced prompt management (e.g., its graph logic in `src/tester/graph.py` now directly uses `agent_config.system_prompt` for formatting its system message). **UPDATED**: The Tester agent's `SYSTEM_PROMPT` in `src/tester/prompts.py` now includes a `{project_path}` placeholder. Its `test-agent-system-prompt.md` has been updated with a new "Workflow" section detailing steps like checking for project directory, verifying required files (`projectRequirements.md`, `techPatterns.md`, `systemPatterns.md`, `testingContext.md`, `projectbrief.md`, `codingContext.md`, `progress.md`), analyzing files, generating tests, and saving them to `project_path/tests`. It also removes previous rules about linking tests to requirement IDs and completion verification. The Code Reviewer agent has `PR_REVIEW_PROMPT`. The Architect agent has `architect_system_prompt` (REVISED to include a dedicated "Summarize" step using its new `summarize` tool before finalization).
6.  **Configuration Management (REVISED):** Agents have configurable parameters, including LLM models, system prompts, and memory settings.
    *   `MemoryConfiguration` (`common.components.memory.MemoryConfiguration`).
    *   Common `AgentConfiguration` (`src/common/configuration.py`).
    *   Agent-specific `Configuration` dataclasses subclass `AgentConfiguration`.
    *   Architect: `src/architect/configuration.py`'s `Configuration` class no longer defines `use_human_ai`.
    *   Code Reviewer: `CodeReviewerInstanceConfig` dataclass.
    *   Task Manager (`src/task_manager/configuration.py` - REVISED): `Configuration` class includes `use_stub: bool`, `use_human_ai: bool`, and `task_manager_system_prompt: str`.
    *   Orchestrator (`src/orchestrator/configuration.py` - REVISED): `SubAgentConfig` and its subclasses (`RequirementsAgentConfig`, `ArchitectAgentConfig`, `TaskManagerAgentConfig`) now include a `stub_messages: MessageWheel` field, allowing dynamic cycling messages for stubbed agent responses. The `coder_new_pr_agent` and `coder_change_request_agent` in `OrchestratorConfiguration` now default to specific `MessageWheel` instances for their stub messages. **UPDATED**: A new `TesterAgentConfig` dataclass is introduced, subclassing `SubAgentConfig`, with `use_stub: bool = True` and `config: TesterConfiguration`. The `tester_agent` field in `OrchestratorConfiguration` now uses `TesterAgentConfig` as its type. **UPDATED**: A new `github_base_branch: str = "main"` field has been added to `Configuration`.

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
    *   Orchestrator (REVISED): Uses direct tools `requirements`, `architect`, `task_manager` (NEW), `coder_new_pr`, `coder_change_request`, `tester`, `code_reviewer` (which invoke sub-graphs/stubs), `memorize` (for memory persistence), and `summarize` (now from `common.tools.summarize`). The `requirements`, `architect`, and `task_manager` tools now update the Orchestrator's state with the `project` object returned by the sub-agent. The `coder_new_pr` and `coder_change_request` tools now return the content of the last message from the sub-agent's result, rather than a summary. **UPDATED**: The `tester` tool now passes the Orchestrator's `project` state to the Tester agent's state.
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools from `AgentGraph`.
    *   Requirement Gatherer: Uses `create_memorize_tool` and `human_feedback` tool. Its `summarize` tool is now from `common.tools.summarize`. A new `set_project` tool is available.
    *   Tester: Custom `upsert_memory` tool removed. **UPDATED**: Now includes `common.tools.summarize`, `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file` in its toolset.
    *   Code Reviewer: Uses GitHub tools.
    *   Architect (NEW, REVISED): Uses `create_memorize_tool`, `create_recall_tool`, `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`, and a new `summarize` tool (now from `common.tools.summarize`). `use_human_ai` removed from its config.
    *   Task Manager (REVISED): Uses `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`. Now also uses the `summarize` tool (from `common.tools.summarize`).
    *   Coder (REVISED): **UPDATED**: Now includes the `get_latest_pr_workflow_run` tool.
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
        *   `tester_agent` (type `SubAgentConfig`) **UPDATED**: Now of type `TesterAgentConfig`.
        *   `code_reviewer_agent` (type `SubAgentConfig`)
        *   **UPDATED**: A new `github_base_branch: str = "main"` field has been added.
    *   These sub-agent configurations (e.g., `SubAgentConfig`, `ArchitectAgentConfig`, `TaskManagerAgentConfig` (NEW), also defined/imported in this module) typically allow specifying whether to use a full agent or a stub, and can contain agent-specific nested configurations.
    *   **UPDATED**: `SubAgentConfig` now includes `stub_messages: MessageWheel = MessageWheel(["I finished the task."])`. Its subclasses (`RequirementsAgentConfig`, `ArchitectAgentConfig`, `TaskManagerAgentConfig`) now default `stub_messages` to specific `model_*_messages` instances. The `coder_new_pr_agent` and `coder_change_request_agent` in `OrchestratorConfiguration` are now initialized with `SubAgentConfig` instances that explicitly set their `stub_messages` to `model_coder_new_pr_messages` and `model_coder_change_request_messages` respectively.
    *   **UPDATED**: A new `TesterAgentConfig` dataclass is introduced, subclassing `SubAgentConfig`, with `use_stub: bool = True` and `config: TesterConfiguration = field(default_factory=TesterConfiguration)`.
    *   As an example of nested configuration, the `ArchitectAgentConfig` contains a nested `config: architect.configuration.Configuration` field, and this nested Architect configuration is what reflects changes like the removal of `use_human_ai` from the Architect's own configuration file. The new `TaskManagerAgentConfig` similarly contains a nested `config: task_manager.configuration.Configuration`.
*   **State (`src/orchestrator/state.py` - REVISED):** Added `summary: str = ""` field to its `State` dataclass. A new `project: Optional[Project] = None` field has been added to store the active project information.
*   **Graph (`src/orchestrator/graph.py` - REVISED):**
    *   The graph structure has been refactored to use a `ToolNode` for invoking all agent-specific tasks and other utilities.
    *   The `_create_orchestrate` node is renamed to `_create_orchestrator`.
    *   The previous delegation logic (`_create_delegate_to` and individual agent node creators like `_create_requirements_node`, `_create_architect_node`, etc.) has been removed.
    *   The LLM is now bound with a new set of tools (see Orchestrator Tools under Key Concepts or Tools section below). This now includes a `task_manager` tool. The `summarize` tool is now imported from `common.tools`.
    *   **UPDATED**: All sub-agent stub initializations (e.g., `RequirementsGathererStub`, `ArchitectStub`, `TaskManagerStub`, `CoderNewPRStub`, `CoderChangeRequestStub`, `TesterStub`, `CodeReviewerStub`) now pass the `stub_messages` from their respective agent configurations (`self._agent_config.<agent_name>_agent.stub_messages`) to the stub constructors.
    *   **UPDATED**: The `maybe_mock_github` function, used to get GitHub tools, now receives `base_branch=self._agent_config.github_base_branch`, allowing the Orchestrator to use a configurable base branch for GitHub interactions.
    *   Conditional logic (`_create_orchestrate_condition`) routes from the main `orchestrator` (model call) node to the `ToolNode` if tool calls are present, or to `END` if a `summary` is available in the state, otherwise back to the `orchestrator` node.
    *   Sub-agent graphs (or their stubs, including for Task Manager) are passed to tool factory functions which create the tools bound to the Orchestrator's LLM.
*   **Stubs (`src/orchestrator/stubs/__init__.py` - REVISED):**
    *   **UPDATED**: The `MessageWheel` class (for cycling through predefined messages) is now defined at the top level of this module.
    *   **UPDATED**: The `StubGraph` base class now has a `_stub_messages` attribute, initialized via its constructor, and its `run_fn` now uses `self._stub_messages.next()` to retrieve the next message. This ensures each stub instance maintains its own message sequence.
    *   **UPDATED**: Predefined `MessageWheel` instances (`model_requirements_messages`, `model_architect_messages`, `model_task_manager_messages`, `model_coder_new_pr_messages`, `model_coder_change_request_messages`, `model_tester_messages`, `model_code_reviewer_messages`) are now defined globally in this module.
    *   The `StubGraph` base class's `run_fn` is now expected to return a dictionary that includes a `summary` field. The graph built by `StubGraph` now adds an edge from its "run" node to `END`.
    *   `RequirementsGathererStub`, `ArchitectStub`, `CoderNewPRStub`, `CoderChangeRequestStub` are updated to align with this, providing a `summary` in their output. `RequirementsGathererStub` now also returns a `project_name`.
    *   `TesterStub` (NEW class, subclasses `StubGraph`): Replaces the previous simple `stubs.tester` function.
    *   `CodeReviewerStub` (NEW class, subclasses `StubGraph`): Replaces the previous simple `stubs.reviewer` function.
    *   `TaskManagerStub` (NEW class, subclasses `StubGraph`): Provides a stub for the Task Manager agent.
    *   **UPDATED**: All specific `*Stub` classes (`RequirementsGathererStub`, `ArchitectStub`, `TaskManagerStub`, `CoderNewPRStub`, `CoderChangeRequestStub`, `TesterStub`, `CodeReviewerStub`) now accept a `stub_messages` argument in their `__init__` and pass it to the `super().__init__` call, allowing their responses to be dynamically controlled by the Orchestrator's configuration.
    *   The old simple stub functions (`stubs.tester`, `stubs.reviewer`, `stubs.memorizer`) have been removed.
*   **Tools (`src/orchestrator/tools.py` - REVISED):**
    *   The `Delegate` tool has been removed.
    *   The `store_memory` tool has been effectively replaced by the `memorize` tool. Its `origin` parameter's type hint is updated to include `code_reviewer`.
    *   New tool factory functions are introduced:
        *   `create_requirements_tool(agent_config, requirements_graph)`: Creates the `requirements` tool. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result.
        *   `create_architect_tool(agent_config, architect_graph)`: Creates the `architect` tool. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result.
        *   `create_task_manager_tool(agent_config, task_manager_graph)` (NEW): Creates the `task_manager` tool. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result.
        *   `create_coder_new_pr_tool(agent_config, coder_new_pr_graph)`: Creates the `coder_new_pr` tool.
        *   `create_coder_change_request_tool(agent_config, coder_change_request_graph)`: Creates the `coder_change_request` tool.
        *   `create_tester_tool(agent_config, tester_graph)`: Creates the `tester` tool. **UPDATED**: This tool now passes the Orchestrator's `project` state to the Tester agent's state.
        *   `create_code_reviewer_tool(agent_config, code_reviewer_graph)`: Creates the `code_reviewer` tool.
    *   These tools take `content` (and other injected args like `tool_call_id`, `state`, `config`), invoke the respective sub-graph (or stub), and return the `summary` from the sub-graph's result as the tool's output.
    *   **UPDATED**: The `coder_new_pr` and `coder_change_request` tools now return `result["messages"][-1].content` (the content of the last message) instead of `result["summary"]`.
    *   The `summarize` tool implementation has been removed from this file, as it is now centralized in `src/common/tools/summarize.py`.
*   **Prompts (`src/orchestrator/prompts.py` and `src/orchestrator/memory/` - REVISED):**
    *   `src/orchestrator/prompts.py`: The static `ORCHESTRATOR_SYSTEM_PROMPT` string definition has been removed. The `get_prompt()` function continues to load prompt content from markdown files.
    *   `src/orchestrator/memory/absolute.md`, `process.md`, `project_states.md`, `team.md`: These markdown files, which constitute the Orchestrator's system prompt, have been significantly updated to reflect the new toolset (direct agent invocation tools including `task_manager`, `memorize`, `summarize`) and the refined operational workflow (e.g., explicit instruction to use the `summarize` tool when no tasks are pending). `project_states.md` now includes a "Create tasks" step and an updated Mermaid flowchart. `team.md` now includes a section for the "Task Manager" agent.

#### 5.2. Architect (`src/architect/`) (REWORKED, REVISED)
*   **Configuration (`src/architect/configuration.py` - REVISED):**
    *   The `use_human_ai: bool = False` field has been removed.
*   **State (`src/architect/state.py` - REVISED):** Added `summary: str = ""` field. A new `project: Project` field has been added to store the active project information.
*   **Graph (`src/architect/graph.py` - REVISED):**
    *   The Architect's graph now includes `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`, and a `summarize` tool (now imported from `common.tools`) in its set of available tools.
    *   The `call_model` function now formats the system prompt with `project_dir=state.project.path`. It also prints formatted messages using `common.utils.format_message`.
*   **Tools (`src/architect/tools.py` - REVISED):**
    *   The `summarize` tool implementation has been removed from this file, as it is now centralized in `src/common/tools/summarize.py`.
    *   The `read_file`, `create_file`, and `list_files` tools have been removed from this file, as they are now centralized in `src/common/tools/`.
*   **Prompts (`src/architect/prompts.py` - REVISED):**
    *   The Architect's system prompt (`architect_system_prompt`) has been updated to include a new "Summarize" step. This step instructs the agent to write a `summary` of the architecture and call its `summarize` tool before proceeding to the "Finalize" step. The prompt now dynamically references the active project directory (`{project_dir}`). **UPDATED**: The prompt's description of the core project files and their interdependencies (including the Mermaid flowchart and numbered list) has been updated. `projectRequirements.md` is now explicitly listed as a core file and is positioned as an intermediary document between `projectbrief.md` and `systemPatterns.md`/`techPatterns.md`. The description of `projectbrief.md` is now more focused on its foundational role. The numbering of core files in the prompt has been adjusted (e.g., `systemPatterns.md` is now 3, `techPatterns.md` is 4, `progress.md` is 5). **UPDATED**: The prompt now includes an instruction to ensure the `{project_dir}` exists and create it if necessary before writing new files, explicitly mentioning the `create_directory` tool. It also clarifies that `list_files` should be used on the `{project_dir}` directory and that `create_file` should write files under `{project_dir}`.

#### 5.3. Coder (`src/coder/`)
*   **State (`src/coder/state.py` - REVISED):**
    *   Changed from `TypedDict` to `@dataclass(kw_only=True)`.
    *   Added `summary: str = ""` field.
*   **Graph (`src/coder/graph.py` - UPDATED):** Accesses state messages via `state.messages` instead of `state["messages"]` due to state being a dataclass. **UPDATED**: The `coder_new_pr_config` and `coder_change_request_config` now include the `get_latest_pr_workflow_run` tool in their `allowed_tools` list.
*   **Prompts (`src/coder/prompts.py` - UPDATED):** The `NEW_PR_SYSTEM_PROMPT` has been updated to refer to the "base branch" instead of "main" for repository interactions.

#### 5.4. Code Reviewer (`src/code_reviewer/`) (REVISED)
*   **State (`src/code_reviewer/state.py` - REVISED):** Added `summary: str = ""` field.
*   **Tool Naming:** Referred to as `code_reviewer` in Orchestrator's tools and stubs.

#### 5.5. Tester (`src/tester/`) (REWORKED)
*   **State (`src/tester/state.py` - REVISED):** Added `summary: str = ""` field. **UPDATED**: A new `project: Project` field has been added to store the active project information.
*   **Graph (`src/tester/graph.py` - REVISED):**
    *   The internal `_create_call_model` function, responsible for preparing and invoking the LLM, now explicitly accepts the agent's `Configuration` (as `agent_config`).
    *   The system prompt used in `_create_call_model` is now directly sourced from `agent_config.system_prompt`, improving how the configured prompt is passed and utilized within the graph's execution logic. **UPDATED**: The `call_model` function now formats the system prompt with `project_path=state.project.path`.
    *   **UPDATED**: The `__init__` method now adds `common.tools.summarize`, `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, and `common.tools.read_file` to the agent's set of available tools.
*   **Prompts (`src/tester/prompts.py` - REVISED):**
    *   **UPDATED**: The `SYSTEM_PROMPT` now includes a `Project Path: {project_path}` placeholder.
    *   **UPDATED**: The `test-agent-system-prompt.md` content has been significantly updated:
        *   The "Process" section has been replaced by a "Workflow" section.
        *   The new "Workflow" section outlines steps: `CHECK if project directory exists at the provided path project_path`, `VERIFY all required project files are present` (listing `projectRequirements.md`, `techPatterns.md`, `systemPatterns.md`, `testingContext.md`, `projectbrief.md`, `codingContext.md`, `progress.md`), `ANALYZE all files to understand requirements and constraints`, `GENERATE executable tests based on project requirements`, and `SAVE generated tests to project_path/tests` directory.
        *   The "Completion Verification" section has been removed.
        *   The "Key Rules" have been updated, specifically removing the rule to "ENSURE each test links to a specific requirement ID".

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`) (REVISED)
*   **State (`src/requirement_gatherer/state.py` - REVISED):** Added `summary: str = ""` field. A new `project: Optional[Project] = None` field has been added to store the active project information.
*   **Graph (`src/requirement_gatherer/graph.py` - REVISED):** The conditional logic in `_create_gather_requirements` for routing to the tool node is updated to `if state.messages and state.messages[-1].tool_calls:`. The `summarize` tool is now imported from `common.tools`. The `set_project` tool has been added to the agent's toolset.
*   **Tools (`src/requirement_gatherer/tools.py` - REVISED):** The `summarize` tool implementation has been removed from this file, as it is now centralized in `src/common/tools/summarize.py`. A new `set_project` tool is introduced to set the project name and initialize the `Project` object in the state.
*   **Prompts (`src/requirement_gatherer/prompts.py` - REVISED):** The prompt has been updated to include a new step `0. **Project name**` which instructs the agent to ask for the project name and use the `set_project` tool if it's not provided.

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
*   **State (`src/task_manager/state.py` - REVISED):** Added `summary: str = ""` field. (Used by `TaskManagerStub` and consistent with other agents). A new `project: Project` field has been added to store the active project information.
*   **Tools:** Uses `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`. The Orchestrator uses a `task_manager` tool to invoke this agent. Now also uses the `summarize` tool (from `common.tools.summarize`).
*   **Prompts (`src/task_manager/prompts.py` - UPDATED):** Contains `SYSTEM_PROMPT` used by the agent. This prompt has been significantly updated to include:
    *   **Revised Task Splitting Guidelines:** Tasks now sized for 4-6 hours (previously 6-14 hours). Stricter rules for splitting tasks (>6 hours). Each task *must* result in a buildable and runnable deliverable, even initialization tasks (e.g., "hello world"). Avoid partial/non-functional components.
    *   **New Testing Requirements Section:** Mandates that every functional task includes tests (unit, integration, edge cases). Test implementation is not optional and time for it must be factored into estimation.
    *   **New CI/CD Requirements Section:** Mandates GitHub Actions workflow setup for tests early in the project. Specifies CI configuration details (running tests on PRs/pushes, reporting failures, linting). Outlines mandatory task sequencing for the project plan: Repository initialization FIRST, Basic project setup SECOND, CI/CD setup THIRD, Core feature implementation FOURTH, with follow-up CI/CD improvements throughout.
    *   **Expanded `task.md` Metadata Schema:** The `details` field is now a "Comprehensive numbered list of all steps" formatted as a recipe, including implementation, test, CI/CD integration, and verification steps. New fields added for contextual information: `contextualInformation`, `technicalRequirements`, `securityConsiderations`, `relatedFeatureContext`, `systemPatternGuidance`, `testingRequirements`. **UPDATED**: The `technicalRequirements` field now refers to `techPatterns.md`. The `securityConsiderations` field has been removed. The `relatedFeatureContext` field has been renamed to `relatedCodingContext` and now refers to `codingContext.md`.
    *   **Strengthened `roadmap.md` Guidelines:** Emphasizes including *ALL* tasks without exception, performing validation steps to ensure no tasks are missing, and logging task counts. Reinforces task sequencing (repo init -> project setup -> CI -> features) and scheduling periodic CI/CD improvement tasks.
    *   **Revised Step-by-Step Instructions:**
        *   **Step 2 (Tasks Creation):** Now explicitly requires extracting and including *all* relevant context from input files (e.g., `projectRequirements.md`, `techContext.md`, `securityContext.md`, `featuresContext.md`, `systemPatterns.md`, `testingContext.md`) directly into each task, prohibiting external file references. Details field must be a numbered, specific, actionable list covering implementation, testing, CI/CD, and verification. Tasks must produce buildable/runnable deliverables. **UPDATED**: References to `techContext.md` changed to `techPatterns.md`. References to `featuresContext.md` changed to `codingContext.md`. Instructions for extracting `securityContext.md` have been removed.
        *   **Step 3 (Planning Creation):** Now explicitly requires counting tasks, ensuring *every single* task is included in the roadmap, verifying counts, and scheduling tasks in the *correct sequence* (repo init -> project setup -> CI -> features), with CI/CD tasks scheduled *after* prerequisites.
    *   **New Detailed Guidelines Sections:**
        *   `Context Extraction Guidelines`: Principles for specific, focused, accurate extraction.
        *   `Task-Specific Document Extraction Guidelines`: Detailed instructions for extracting information from `TestingContext.md`, `TechContext.md`, `SecurityContext.md`, `FeatureContext.md`. **UPDATED**: `TechContext.md Extraction` heading changed to `techPatterns.md Extraction`. `SecurityContext.md Extraction` section has been removed. `FeatureContext.md Extraction` heading changed to `codingContext.md Extraction`.
        *   `CI/CD Task Creation Guidelines`: Instructions for creating CI/CD tasks, their sequencing, and evolution.
        *   `Details Field Format`: Example and rules for the `details` field.
        *   `Test Creation Guidelines`: Guidance on specific test cases, edge cases, positive/negative scenarios, mocking, and testing levels. **UPDATED**: References to `techContext.md` changed to `techPatterns.md`.
        *   `Functional Deliverable Guidelines`: Ensures each task produces a buildable, runnable deliverable, from "hello world" for initialization to integrated features.
        *   `GitHub Actions CI Configuration Guidelines`: Details for configuring CI workflows.
    *   **Updated Technical Guardrails:** Reinforces that tasks must be self-contained, no external file references, mandatory test implementation, required CI setup regardless of input, CI/CD setup after repo init/basic setup, every task must result in a buildable/runnable deliverable, and task sequencing must follow logical order. **UPDATED**: Guardrails implicitly updated to align with the removal of `securityContext.md` and the renaming of `featuresContext.md` to `codingContext.md`.
    *   The prompt now dynamically references the active project name (`{project_name}`) and path (`{project_path}`). **UPDATED**: The prompt now explicitly states that it will receive input documents in `{project_path}` and the project name is `{project_name}`. It also includes a new mandatory instruction to write a `summary` of the created tasks and call the `summarize` tool. The prompt now states that it will verify "all seven required files" (previously "eight").

## 6. Testing Framework (`tests/`) (UPDATED)

*   **`tests/datasets/requirement_gatherer_dataset.py` (UPDATED):**
    *   The dataset name has been updated to `"Requirement-gatherer-dataset-human-ai"`.
    *   A new `FIRST_MESSAGE` constant has been added, providing a detailed initial project description for the agent.
    *   The input content for the human message in the dataset examples now uses `FIRST_MESSAGE`.
    *   The expected output content has been updated to `"Requirements are confirmed"`.
*   **`tests/integration_tests/test_orchestrator.py` (UPDATED):**
    *   Tests updated to reflect the Orchestrator's new tool usage (e.g., `memorize` instead of `store_memory`, and direct agent tool calls like `code_reviewer` instead of generic `Delegate`).
*   **`tests/integration_tests/test_requirement_gatherer.py` (UPDATED):**
    *   The test setup now explicitly imports `Configuration` as `GathererConfig` from `requirement_gatherer.configuration`.
    *   An `agent_config = GathererConfig(use_human_ai=True)` is now passed to the `RequirementsGraph` constructor.
    *   The `client.aevaluate` call now uses `create_async_graph_caller_for_gatherer(graph)` instead of `create_async_graph_caller(graph)`.
    *   The `num_repetitions` for evaluation has been reduced from `4` to `1`.
*   **Smoke Tests (NEW - UPDATED):**
    *   **`tests/smoke/langgraph_dev/`**: Contains a smoke test for the `langgraph dev` CLI and its UI.
        *   **Purpose**: Verifies basic end-to-end functionality of launching `langgraph dev`, interacting with the LangGraph Studio UI for the `agent_template` graph, and ensuring it reaches an expected state (e.g., a human interrupt).
        *   **Technology**: Node.js, TypeScript, Puppeteer.
        *   **Execution**:
            1.  Launches the `langgraph dev` server for the AI Nexus project.
            2.  Uses Puppeteer to open a browser and navigate to the LangGraph Studio (`https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8080`).
            3.  Waits for the `agent_template` graph to be listed and then selects it.
            4.  Inputs a test message (e.g., "I want to build a website").
            5.  Submits the message and waits for the graph to process.
            6.  Asserts that the graph execution pauses for a human interrupt by verifying the presence of an 'Interrupt' label and subsequently either a 'Continue' or 'Resume' button in the UI.
        *   **Artifacts**: Produces `langgraph-test-result.png` (a screenshot of the UI state) which is uploaded by the CI workflow.
        *   **Configuration**: Requires `GOOGLE_API_KEY` (via `.env` file at project root) for the `langgraph dev` server.
*   **`tests/scenarios/fibonacci.py` (NEW):** A new test scenario demonstrating the orchestration of multiple agents (using stubbed responses for most, and a real Coder agent) to create a Rust Fibonacci iterator library. This scenario showcases the dynamic stub message feature. **UPDATED**: The `OrchestratorConfiguration` in this scenario now explicitly sets `github_base_branch="fibonacci-base"`. **UPDATED**: Now defines a `BASE_BRANCH` constant and updates stub messages for `requirements_agent` and `task_manager_agent` to reflect the scenario's specific requirements. Includes logging for execution flow.
*   **`tests/scenarios/__init__.py` (NEW):** Defines `BASE_BRANCHES` list for centralized management of base branch names used in testing scenarios.
*   **`tests/testing/__init__.py` (UPDATED):**
    *   A new helper function `create_async_graph_caller_for_gatherer` has been added. This function is specifically designed for the requirement gatherer evaluation, expecting the final output to be a `ToolMessage` with the name "summarize" and returning its content.
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
*   **Project Maintenance Scripts (UPDATED):**
    *   The `generate_project_memory.sh`, `update_project_memory_from_pr.sh`, and `update_project_readmes.sh` scripts now use the `gemini-2.5-flash-preview-05-20` model for their API calls.
*   **Dependency Management (`pyproject.toml` - UPDATED):**
    *   Dependency version specifiers have been changed from `>=` (greater than or equal to) to `~=` (compatible release, e.g., `~=1.2.3` implies `>=1.2.3` and `<1.3.0`). This change restricts updates to patch versions for the specified minor versions of main and development dependencies, aiming to enhance build stability.
    *   The `[tool.setuptools]` `packages` list within `pyproject.toml` has also been reformatted for improved readability. **UPDATED**: The `packages` list now includes `scenarios`.
*   **LangSmith Tracing (NEW aspect for demo):**
    *   The demo script (`src/demo/orchestrate.py`) now integrates LangSmith tracing, providing a trace URL for each run. This includes user identification and run metadata.
*   **New/Updated Utility Files:**
    *   `src/common/state.py` (NEW): Defines the `Project` dataclass for managing project ID, name, and path.
    *   `src/common/utils/__init__.py` (UPDATED): Includes a new `format_message` utility function for printing actor-labeled messages.
    *   **UPDATED**: `src/common/logging.py` (NEW): Provides a centralized `get_logger` utility for consistent log formatting and dynamic log level control via the `LOG_LEVEL` environment variable.
*   **Project Directory:** A new `projects/` directory has been added to store project-specific files.
*   `.gitignore` (UPDATED): Now excludes all files and directories under `projects/`. **UPDATED**: Also excludes files with the `.pem` extension.
*   **Demo Configuration:** The demo script (`src/demo/orchestrate.py`) now configures `task_manager_agent` with `use_stub=False` and `coder_new_pr_agent`, `coder_change_request_agent` with `use_stub=True`. **UPDATED**: The demo script now configures the `tester_agent` with `use_stub=False` and passes `TesterConfiguration()`.
*   **GitHub Branch Management Scripts (NEW):**
    *   `tests/scenarios/setup_github.py`: A utility script to create specified base branches in a GitHub repository if they do not already exist, using GitHub App authentication.
    *   `tests/scenarios/cleanup_github.py`: A utility script to delete branches in a GitHub repository that are not part of a predefined list of base branches, using GitHub App authentication.
*   **Environment Variables (UPDATED):**
    *   `.env.example`: Now includes `LOG_LEVEL=INFO` to configure the default logging level.
*   (Other workflow aspects like `pytest.ini` setup as previously described, or minor updates not impacting core logic)

## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/
│   └── rules/
│       └── read-project-memories.mdc
├── .env.example                   # UPDATED: Added LOG_LEVEL
├── .gitignore                    # UPDATED: Added projects/*, *.pem
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
├── projects/                     # NEW: Directory for project-specific files
│   └── .gitkeep                  # NEW
├── project_memories/
│   ├── PRD.md
│   └── global.md
├── pyproject.toml                # UPDATED: Dependency constraints changed to `~=`; package list reformatted; `scenarios` package added.
├── pytest.ini                    # UPDATED: Minor formatting
├── scripts/
│   └── generate_project_memory.sh
│   └── update_project_memory_from_pr.sh
│   └── update_project_readmes.sh
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
│   │   ├── graph.py              # UPDATED: Added common.tools.summarize, common.tools.create_directory, common.tools.create_file, common.tools.list_files, common.tools.read_file to the agent's toolset; call_model uses state.project.path and prints formatted messages.
│   │   ├── prompts.py            # UPDATED: System prompt includes new "Summarize" step and use of summarize tool; uses {project_dir}. UPDATED: Prompt's description of core files and their flow (Mermaid, numbered list) updated to include projectRequirements.md as an intermediary and adjusted numbering. UPDATED: Prompt now includes instruction to ensure {project_dir} exists and create it if necessary, using create_directory, and clarifies list_files and create_file usage.
│   │   ├── state.py              # UPDATED: summary field added; project field added.
│   │   └── tools.py              # UPDATED: Removed 'summarize', 'read_file', 'create_file', 'list_files' tools (now in common)
│   ├── code_reviewer/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── lg_server.py
│   │   ├── prompts.py
│   │   ├── state.py              # UPDATED: summary field added
│   │   └── system_prompt.md
│   ├── coder/
│   │   ├── __init__.py
│   │   ├── graph.py              # UPDATED: Minor state access change (state.messages). UPDATED: `coder_new_pr_config` and `coder_change_request_config` now include `get_latest_pr_workflow_run` tool.
│   │   ├── lg_server.py
│   │   ├── mocks.py
│   │   ├── prompts.py            # UPDATED: NEW_PR_SYSTEM_PROMPT updated to use "base branch".
│   │   ├── state.py              # UPDATED: Now a dataclass, summary field added
│   │   ├── tools.py
│   │   └── README.md
│   ├── common/
│   │   ├── components/
│   │   │   ├── github_mocks.py   # UPDATED: `maybe_mock_github` function now accepts an optional `base_branch` argument. Added mocks for `create_issue_comment` and `get_latest_pr_workflow_run`. Updated existing mocks to return empty string instead of raising NotImplementedError.
│   │   │   ├── github_tools.py   # UPDATED: Added `create_issue_comment` and `get_latest_pr_workflow_run` tools. Modified `_run` methods of `CreatePullRequestReviewComment`, `GetPullRequestDiff`, `GetPullRequestHeadBranch` to call their `_arun` counterparts.
│   │   │   └── memory.py
│   │   ├── configuration.py
│   │   ├── graph.py
│   │   ├── logging.py            # NEW: Logging utilities
│   │   ├── state.py              # NEW: Defines Project dataclass
│   │   ├── tools/                # ADDED
│   │   │   ├── __init__.py       # ADDED: Imports create_directory, create_file, list_files, read_file, summarize
│   │   │   ├── create_directory.py # NEW: Centralized create_directory tool
│   │   │   ├── create_file.py    # NEW: Centralized create_file tool
│   │   │   ├── list_files.py     # NEW: Centralized list_files tool (moved from src/task_manager/tools.py)
│   │   │   ├── read_file.py      # NEW: Centralized read_file tool
│   │   │   └── summarize.py      # ADDED: Centralized summarize tool
│   │   └── utils/
│   │       └── __init__.py       # UPDATED: Added format_message function
│   ├── demo/
│   │   └── orchestrate.py        # MOVED & RENAMED from src/orchestrator/test.py; UPDATED to use create_runnable_config and compiled_graph.ainvoke. UPDATED: Imports TaskManagerAgentConfig, TaskManagerConfiguration, TesterAgentConfig, TesterConfiguration; configures task_manager_agent and tester_agent; prints task_manager tool calls. UPDATED: Integrates LangSmith tracing (prints trace URL, uses @traceable). The demo script's configuration for the Orchestrator now sets `use_stub=False` by default for the Requirements, Architect, Coder New PR, and Coder Change Request agents. The Task Manager agent remains configured with `use_stub=True` in the demo. UPDATED: `task_manager_agent` `use_stub` changed to `False`, `coder_new_pr_agent` and `coder_change_request_agent` `use_stub` changed to `True`. `tester_agent` `use_stub` changed to `False`.
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration. Defines OrchestratorConfiguration including fields for sub-agent configs (e.g., ArchitectAgentConfig, TaskManagerAgentConfig (NEW), TesterAgentConfig (NEW), SubAgentConfig for coders, reviewer). SubAgentConfig and its subclasses now include `stub_messages`. Coder agent configs now default to specific `MessageWheel` instances. Added `github_base_branch` field.
│   │   ├── graph.py              # UPDATED: Major refactor to use ToolNode, direct agent tool calls (requirements, architect, task_manager (NEW), coder_new_pr, coder_change_request, tester, code_reviewer), memorize, and common.tools.summarize. Removed Delegate pattern. Sub-agent stubs now initialized with `stub_messages`. `maybe_mock_github` now called with `base_branch` from agent config.
│   │   ├── memory/
│   │   │   ├── absolute.md       # UPDATED: Reflects new tools and workflow
│   │   │   ├── process.md        # UPDATED: Reflects new tools and workflow
│   │   │   ├── project_states.md # UPDATED: Reflects new tools, workflow (incl. task creation), includes Mermaid diagram
│   │   │   └── team.md           # UPDATED: Reflects new tools (direct calls, memorize, summarize), includes Task Manager agent
│   │   ├── prompts.py            # UPDATED: Static ORCHESTRATOR_SYSTEM_PROMPT string removed, get_prompt() loads from memory files.
│   │   ├── state.py              # UPDATED: summary field added; project field added.
│   │   ├── stubs/
│   │   │   └── __init__.py       # UPDATED: StubGraph base class modified (returns summary, END edge, uses `_stub_messages`). MessageWheel class moved to top-level. All specific *Stub classes now accept and pass `stub_messages` to super(). Predefined `model_*_messages` instances added. RequirementsGathererStub, ArchitectStub, CoderNewPRStub, CoderChangeRequestStub updated. New TesterStub, CodeReviewerStub, TaskManagerStub (NEW) classes. Old simple stub functions removed. Imports TaskManagerState. RequirementsGathererStub now returns project_name.
│   │   ├── tools.py              # UPDATED: Delegate tool removed. store_memory effectively replaced by memorize. New tool factories (create_requirements_tool, etc.) for direct agent invocation, including create_task_manager_tool (NEW). `coder_new_pr` and `coder_change_request` tools now return `result["messages"][-1].content`. Removed 'summarize' tool (now in common). Imports TaskManagerGraph, TaskManagerState. Requirements, Architect, and Task Manager tools now update the project state. Tester tool now passes project state.
│   │   └── utils.py              # ADDED: Contains utility functions like split_model_and_provider.
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py
│   │   ├── graph.py              # UPDATED: Renamed to RequirementsGraph, uses AgentConfiguration, new AgentGraph init; helpers receive agent_config; memorize tool now created via create_memorize_tool(self._agent_config); minor conditional logic update in _create_gather_requirements; uses common.tools.summarize. Added set_project tool.
│   │   ├── prompts.py            # UPDATED: Prompt includes instruction for set_project tool.
│   │   ├── state.py              # UPDATED: summary field added; project field added.
│   │   └── tools.py              # UPDATED: Removed 'summarize' tool (now in common). Added set_project tool.
│   ├── task_manager/
│   │   ├── configuration.py      # UPDATED: Added use_stub, use_human_ai fields; uses prompts.SYSTEM_PROMPT.
│   │   ├── graph.py              # UPDATED: call_model uses project_name and project_path in prompt and prints formatted messages. UPDATED: Added common.tools.summarize, common.tools.create_directory, common.tools.create_file, common.tools.list_files, common.tools.read_file to the agent's toolset.
│   │   ├── prompts.py            # UPDATED: System prompt significantly updated with stricter task splitting, mandatory testing/CI/CD requirements, expanded task metadata, and reinforced roadmap/sequencing rules. Uses {project_name} and {project_path}. UPDATED: Prompt's list of required files, file descriptions, task metadata schema, and context extraction guidelines updated to reflect techContext.md -> techPatterns.md, featuresContext.md -> codingContext.md, and removal of securityContext.md. UPDATED: Prompt now explicitly states input document location and project name, and includes a mandatory instruction to write a summary and call the summarize tool. The prompt now states it will verify "all seven required files".
│   │   └── state.py              # UPDATED: summary field added; project field added.
│   └── tester/
│       ├── __init__.py
│       ├── configuration.py
│       ├── deprecated/
│       │   ├── deprecated-test-agent-system-prompt.md
│       │   └── test-agent-analyze-requirements-workflow-stage.md
│       ├── graph.py              # UPDATED: call_model uses project_path in prompt. __init__ adds common.tools.summarize, common.tools.create_directory, common.tools.create_file, common.tools.list_files, common.tools.read_file to the agent's toolset.
│       ├── prompts.py            # UPDATED: SYSTEM_PROMPT includes {project_path}.
│       ├── state.py              # UPDATED: New WorkflowStage enum, State includes workflow_stage, summary field added, project field added.
│       ├── test-agent-system-prompt.md # UPDATED: Content changed to new "Workflow" section (check/verify files, analyze, generate, save tests) and updated "Key Rules" (removed linking to requirement ID).
│       ├── test-agent-testing-workflow-stage.md
│       └── tools.py
└── tests/
    ├── datasets/
    │   ├── coder_dataset.py
    │   ├── requirement_gatherer_dataset.py # UPDATED: Dataset name, FIRST_MESSAGE, input/output content updated.
    │   └── task_manager_dataset.py
    ├── integration_tests/
    │   ├── test_architect_agent.py
    │   ├── test_coder.py
    │   ├── eval_coder.py
    │   ├── test_graph.py
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py    # UPDATED: Tests reflect new Orchestrator tool usage (e.g., memorize, direct agent calls like code_reviewer).
    │   ├── test_requirement_gatherer.py # UPDATED: Uses create_async_graph_caller_for_gatherer, passes agent_config to RequirementsGraph, num_repetitions reduced.
    │   ├── test_task_manager.py
    │   ├── test_tester_agent.py
    │   └── inputs/
    │       └── api_rust/
    │           ├── featuresContext.md
    │           ├── progress.md
    │           ├── projectRequirements.md
    │           ├── securityContext.md
    │           ├── systemPatterns.md
    │           ├── techContext.md
    │           └── testingContext.md
    ├── scenarios/                  # NEW
    │   ├── __init__.py             # NEW: Defines BASE_BRANCHES for scenarios.
    │   ├── cleanup_github.py       # NEW: Script to cleanup GitHub branches for scenarios.
    │   ├── fibonacci.py            # NEW: Adds a new test scenario for a Rust Fibonacci iterator. UPDATED: OrchestratorConfiguration now explicitly sets `github_base_branch="fibonacci-base"`. UPDATED: Now defines a `BASE_BRANCH` constant and updates stub messages for `requirements_agent` and `task_manager_agent` to reflect the scenario's specific requirements. Includes logging for execution flow.
    │   └── setup_github.py         # NEW: Script to setup GitHub branches for scenarios.
    ├── smoke/                      # ADDED
    │   └── langgraph_dev/          # ADDED
    │       ├── .gitignore          # ADDED
    │       ├── package.json        # ADDED
    │       ├── src/                # ADDED
    │       │   └── index.ts        # ADDED
    │       └── tsconfig.json       # ADDED
    ├── testing/
    │   ├── __init__.py             # UPDATED: Added create_async_graph_caller_for_gatherer helper function.
    │   ├── evaluators.py
    │   └── formatter.py
    └── unit_tests/
        └── test_configuration.py
