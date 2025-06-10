# AI Nexus Project: Condensed Memory Bank

## 1. Project Overview & Core Mission

**Project Name:** AI Nexus

**Core Mission:** To develop a system for managing and orchestrating a team of AI agents capable of designing, developing, and maintaining technical projects. An initial focus is on an agent named "Cursor" which operates with a memory that resets between sessions, necessitating a robust external "Memory Bank" system for continuity. A specific rule (`.cursor/rules/read-project-memories.mdc`) now configures Cursor to always read all files within the `project_memories/` directory for every interaction, ensuring this core project context is consistently available to it. AI Nexus aims to be a platform for developing and managing such AI agents. The system now includes robust project management capabilities, allowing the tracking and utilization of project names and paths across various agent workflows.

**Key Concepts:**
1.  **Multi-Agent System:** The project involves a team of specialized AI agents (Orchestrator, Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Grumpy, Task Manager (NEW)) working collaboratively. The Orchestrator agent's delegation mechanism to other agents (Architect, Coder, Tester, Code Reviewer, Requirement Gatherer, Task Manager) has been refactored. It now uses direct tool calls for each agent task instead of a generic `Delegate` tool. The Code Reviewer is consistently referred to as "Code Reviewer" (e.g., Orchestrator tool name `code_reviewer`). A `Project` object is now passed and updated across agent states to maintain consistent project context. Agent stubs now support dynamic, cycling messages for more flexible scenario testing. **UPDATED**: Agent states now consistently include an `error` field to track fatal errors, and agent workflows are designed to propagate and react to these errors, preventing infinite loops or runaway processes.
2.  **Externalized Memory (Semantic Memory):** Agents rely on external storage for persistent knowledge, project state, and context. This addresses context loss in AI agents. The primary mechanism is `langmem`, providing semantic search capabilities over stored memories. `AgentGraph` can now automatically initialize and provide `SemanticMemory` and its tools to subclasses based on its configuration. The Tester agent, for instance, now includes logic to read from a `BaseStore` for contextual memories.
3.  **LangGraph Framework:** The primary framework used for building the AI agents, defining their state, and managing their execution flow. **UPDATED**: Agent `call_model` functions are now decorated with a `prechain` mechanism that includes `skip_on_summary_and_tool_errors`, allowing for pre-execution checks to halt processing if a summary is already present or if a tool has encountered consecutive errors beyond a defined threshold.
4.  **Tool-Using Agents:** Agents are equipped with tools to perform actions, interact with systems (like GitHub), and manage their memory.
    *   Orchestrator (REVISED): The `Delegate` tool has been removed. It now uses a set of specific tools:
        *   `requirements`: Invokes the Requirement Gatherer agent/stub. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result. **UPDATED**: The `ToolMessage` returned by this tool now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
        *   `architect`: Invokes the Architect agent/stub. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result. **UPDATED**: The `ToolMessage` returned by this tool now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
        *   `task_manager` (NEW): Invokes the Task Manager agent/stub. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result. **UPDATED**: The `ToolMessage` returned by this tool now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
        *   `coder_new_pr`: Invokes the Coder agent/stub for new pull requests. **UPDATED**: This tool now returns a `Command` with a `ToolMessage` including a `status` field (`"success"` or `"error"`) and its `content` can be the last message from the sub-agent's result or the sub-agent's `error` message.
        *   `coder_change_request`: Invokes the Coder agent/stub for changes to existing pull requests. **UPDATED**: This tool now returns a `Command` with a `ToolMessage` including a `status` field (`"success"` or `"error"`) and its `content` can be the last message from the sub-agent's result or the sub-agent's `error` message.
        *   `tester`: Invokes the Tester agent/stub. **UPDATED**: This tool now passes the Orchestrator's `project` state to the Tester agent's state, and the Orchestrator's `github_tools` to the Tester agent's graph. **UPDATED**: The `ToolMessage` returned by this tool now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message. **UPDATED**: The Orchestrator is explicitly instructed to *never* send coding implementation details (like PR numbers or branch names) to the Tester agent, only product/architecture requirements.
        *   `code_reviewer`: Invokes the Code Reviewer agent/stub. **UPDATED**: The `ToolMessage` returned by this tool now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message. **UPDATED**: This tool now passes the Orchestrator's `project` state to the Code Reviewer agent's state.
        *   `memorize`: (Replaces its previous `store_memory` tool concept) For persisting information, created by `tools.memorize`.
        *   `summarize`: (NEW) For the Orchestrator to output a final summary of its operations, now provided by `common.tools.summarize`.
        *   `get_next_task` (NEW): For retrieving the next task from the project's task planning file. **UPDATED**: Now provided by `orchestrator.tools.create_read_task_planning_tool`, which supports stub responses based on the `task_manager_agent`'s `use_stub` setting.
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools (`manage_memory`, `search_memory`) from the `AgentGraph`-managed `SemanticMemory` instance (via `self.memory.get_tools()`). **UPDATED**: `AgentGraph` now exposes `name`, `checkpointer`, and `store` as properties.
    *   Requirement Gatherer: Uses a custom `memorize` tool (created by `create_memorize_tool`) and `human_feedback` tool. Its `summarize` tool is now provided by `common.tools.summarize`. A new `set_project` tool is available to set the active project name and path. **UPDATED**: The `human_feedback` tool's prompt now includes a `<Product>` section with a `{product}` placeholder, allowing the tool to receive and use a specific product description (e.g., from `human_ai_product` in configuration) to guide its responses. **FIXED**: The `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
    *   Tester: Its custom `upsert_memory` tool has been removed. **UPDATED**: Now includes `common.tools.summarize` and a filtered set of GitHub tools (`set_active_branch`, `create_a_new_branch`, `get_files_from_a_directory`, `create_pull_request`, `create_file`, `update_file`, `read_file`, `delete_file`, `get_latest_pr_workflow_run`). It **no longer includes** `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`.
    *   Code Reviewer: Can use GitHub tools like `get_pull_request_diff` and `create_pull_request_review`. **UPDATED**: When configured for local review, it can use `common.tools.summarize`, `common.tools.list_files`, and `common.tools.read_file`. The internal `DiffHunkFeedback` and `DiffFeedback` Pydantic models have been removed, implying a less structured feedback output format.
    *   Architect (NEW, REVISED): Uses `create_memorize_tool`, `create_recall_tool`, `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`, and a new `summarize` tool (now provided by `common.tools.summarize`) for outputting its final architecture summary. Its `use_human_ai` configuration field has been removed. Its previous `upsert_memory` tool has been removed. **FIXED**: The `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
    *   Task Manager (REVISED): Uses `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`. Now also uses the `summarize` tool (from `common.tools.summarize`).
    *   Coder (REVISED): **UPDATED**: Now includes the `get_latest_pr_workflow_run` tool. The `create_issue_comment` tool is *not* provided to the Coder agent.
    *   General: Tools like `file_dump` can be used by agents. A common `summarize` tool is now available in `src/common/tools/summarize.py` for reuse across agents. New common file system tools (`common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`) are available for reuse. **UPDATED**: New common GitHub tools `common.components.github_tools.create_issue_comment` (for commenting on issues/PRs) and `common.components.github_tools.get_latest_pr_workflow_run` (for fetching workflow run logs) are now available. Agent outputs are now enhanced with formatted, actor-labeled messages for improved clarity.
5.  **System Prompts (REVISED):** Detailed system prompts define each agent's role, behavior, constraints, and interaction protocols. System prompts are now typically part of agent-specific `Configuration` classes.
    *   Orchestrator (REVISED): Its system prompt, dynamically loaded from markdown files in `src/orchestrator/memory/`, has been updated to reflect its new toolset (direct agent calls like `requirements`, `architect`, `task_manager`, `coder_new_pr`, `coder_change_request`, `tester`, `code_reviewer`, plus `memorize`, `summarize`, and `get_next_task`) and refined workflow logic (e.g., using the `summarize` tool when no tasks are pending, and using `get_next_task` to pick tasks). The static `ORCHESTRATOR_SYSTEM_PROMPT` string in `src/orchestrator/prompts.py` has been removed. **UPDATED**: The prompt now states that the `summarize` tool should be called *IF* no tasks are pending, emphasizing the conditional nature. **UPDATED**: The `absolute.md` prompt now states "You MUST NEVER ask clarifying questions." (previously "MUST NOT") and adds new rules: "You MUST respond with 'I'm not sure what to do', if it is unclear which tool to delegate to." and "You MUST reply to pleasantries like 'Hi', 'Thank you', and 'Bye' in a polite manner.". The `team.md` prompt's instructions for the Requirements Gatherer have been updated: "MUST use `requirements` tool with topic set to `content` or `""` if missing." and "MUST delegate to it for when user instructs to start/begin the process, build, or develop and the requirements are missing or require further exploration.". The `prompts.py` prompt now states "If the user has provided an instruction, direct the flow to the appropriate agent based on the project state." (previously "Once you have the topic of the conversation..."). **UPDATED**: The `process.md` prompt now includes a critical instruction: "IMPORTANT when sending a task copy the task received in `get_next_task` AS IS without changing or summarizing it". **UPDATED**: The `project_states.md` prompt's numbered list and Mermaid flowchart have been updated to reflect that the Tester agent's role is to `Write e2e tests given requirements and architecture` (step 6), occurring *before* code review. The workflow now loops back to `Code & Implement` if code review fails. **UPDATED**: The `team.md` prompt's description for the Tester agent has been updated to clarify its role: it `uses the existing requirements to come up with e2e test scenarios`, `MUST delegate to it when needing to create e2e tests for product/architecture requirements`, `MUST send details about product/architecture`, and `NEVER send coding implementation details such as what PRs or branches where created or features coded`.
    *   Task Manager (NEW, REVISED): System prompt defined in `task_manager.configuration.Configuration` via `task_manager_system_prompt` (which defaults to `prompts.SYSTEM_PROMPT` from `src/task_manager/prompts.py`). This prompt has been significantly updated to include stricter guidelines for task splitting (smaller tasks, buildable deliverables), mandatory testing requirements (unit, integration, edge cases), early CI/CD setup (GitHub Actions), expanded task metadata (contextual, technical, security, testing info), and reinforced roadmap creation and task sequencing rules (repo init -> project setup -> CI -> features). The prompt now dynamically references the active project name (`{project_name}`) and path (`{project_path}`). **UPDATED**: The prompt's list of required files has been updated: `techContext.md` is now `techPatterns.md`, `featuresContext.md` is now `codingContext.md`, and `securityContext.md` has been removed from the list. The prompt's internal descriptions and extraction guidelines for these files have been updated accordingly, including the removal of specific security context extraction instructions and the renaming of `relatedFeatureContext` to `relatedCodingContext` in the task metadata schema. The count of "Additional Context Files" has been adjusted from 4-8 to 4-7. **UPDATED**: The prompt now explicitly states that it will receive input documents in `{project_path}` and the project name is `{project_name}`. It also includes a new mandatory instruction to write a `summary` of the created tasks and call the `summarize` tool. The prompt now states that it will verify "all seven required files" (previously "eight"). **NEW**: The prompt now includes a comprehensive "Path Security Constraints" section, strictly confining file operations to the `{project_path}`. **NEW**: A "HOBBY MODE" section has been added, detailing how the agent should behave (single task, no testing, no CI/CD, no roadmap, simplified output) if the user's request contains "HOBBY". The `description` field format for tasks has been updated, replacing the previous `details` field. A new `tasks.json` schema has been introduced for a flat list of tasks. The "Execution Process" and "Technical Guardrails" sections have been extensively updated to reflect HOBBY mode, path security, and new task/roadmap generation rules.
    *   Architect (REVISED): Its system prompt (`architect_system_prompt`) now dynamically references the active project directory (`{project_dir}`). **UPDATED**: The prompt's description of the core project files and their interdependencies (including the Mermaid flowchart and numbered list) has been updated. `projectRequirements.md` is now explicitly listed as a core file and is positioned as an intermediary document between `projectbrief.md` and `systemPatterns.md`/`techPatterns.md`. The description of `projectbrief.md` is now more focused on its foundational role. The numbering of core files in the prompt has been adjusted (e.g., `systemPatterns.md` is now 3, `techPatterns.md` is 4, `progress.md` is 5). **UPDATED**: The prompt now includes an instruction to ensure the `{project_dir}` exists and create it if necessary before writing new files, specifically mentioning the `create_directory` tool. It also clarifies that `list_files` should be used on the `{project_dir}` directory and that `create_file` should write files under `{project_dir}`. **UPDATED**: The prompt for `projectbrief.md` now instructs the Architect to add "This project is for hobby purposes" if it's a hobby/personal project. The "Summarize" step now explicitly requires the Architect to clarify if the project is a 'hobby' project in its summary. **UPDATED**: The prompt for the `memorize` tool now explicitly states to "Pass the `content` to be memorized and the `context` within which it was stated."
    *   Requirement Gatherer: Its system prompt now includes an explicit instruction to use the `set_project` tool if no project name is provided. **UPDATED**: The prompt has been refined to emphasize asking only the most important details, limiting questions for "HOBBY" projects (max 5 questions), and removing previous rules about "Product-first mindset" and "Zero-assumption rule". The Mermaid flowchart and core file table have been simplified by removing `stakeholders.md` and `constraints.md`. The "Clarifying-Question Checklist" has been updated to remove sections on "Users & Personas" and "Business Constraints", and functional requirements have been streamlined (e.g., removing "Business Rules", "State & Lifecycle", "Administration & Configuration"). A new `HUMAN_AI_PRODUCT` constant has been added to `prompts.py` to provide a default product description for the `human_feedback` tool.
    *   Coder (REVISED): The `NEW_PR_SYSTEM_PROMPT` now refers to the "base branch" instead of a specific branch name like "main". **UPDATED**: The `NEW_PR_SYSTEM_PROMPT` now includes an explicit instruction to use the actual branch name returned by the `get_branch_name` tool, as it may differ from the requested branch name.
    *   Code Reviewer: **UPDATED**: A new `LOCAL_REVIEW_PROMPT` has been added for local code review, which includes a `Project Path: {project_path}` placeholder and instructions to read relevant files, summarize, and call the `summarize` tool.
    *   Other agents: System prompts are accessed by the agent's graph logic (e.g., in custom `call_model` implementations). The Tester agent features enhanced prompt management (e.g., its graph logic in `src/tester/graph.py` now directly uses `agent_config.system_prompt` for formatting its system message). **UPDATED**: The Tester agent's `SYSTEM_PROMPT` in `src/tester/prompts.py` now includes a `{project_path}` placeholder. Its `test-agent-system-prompt.md` has been **significantly updated** with a new "Workflow" section detailing steps like checking for project directory, verifying required files (`projectRequirements.md`, `techPatterns.md`, `systemPatterns.md`, `testingContext.md`, `projectbrief.md`, `codingContext.md`, `progress.md`), analyzing files, generating tests, and saving them to `project_path/tests`. It also removes previous rules about linking tests to requirement IDs and completion verification. **CRITICAL UPDATES**: The prompt now includes **absolute prohibitions** against creating application code, business logic, `if __name__` blocks, or any non-test files. It strictly defines what the Tester can create (test functions, assertions, setup/teardown, test data files). It specifies **file restrictions** (only specific test file patterns, never application source code, config, main files, etc.). It introduces **critical assumption rules** (assume application code exists, coder agent creates missing app files, never create app files yourself, create JSON/CSV/TXT for test data, tests call/import existing modules). It emphasizes **end-to-end & acceptance testing** focus, including application interface testing and test scenarios. The "Workflow" section now includes steps to `IDENTIFY` application type, `CREATE a new branch` (`test-agent-*`), `MANDATORY VALIDATION` before creating any file (checking filename, absence of business logic/main blocks, presence of only test functions, non-executability as app, calling existing apps), `VERIFY` tests only reference existing application files, `UPLOAD ONLY TEST FILES` to GitHub using `create_file` or `update_file`, and `CREATE a pull request` from the test branch to `main`. The "Key Rules" are extensively updated to reinforce these restrictions, emphasizing testing only explicit requirements, focusing on acceptance criteria/user workflows, never submitting directly to base branch, always working on a `test-agent-*` branch, using `create_file`/`update_file` for test files, using `create_pull_request`, and strictly prohibiting creation of application source code or non-test files. It also adds a final instruction to reply with PR number and branch name upon completion. The Code Reviewer agent has `PR_REVIEW_PROMPT`. The Architect agent has `architect_system_prompt` (REVISED to include a dedicated "Summarize" step using its new `summarize` tool before finalization).
6.  **Configuration Management (REVISED):** Agents have configurable parameters, including LLM models, system prompts, and memory settings.
    *   `MemoryConfiguration` (`common.components.memory.MemoryConfiguration`).
    *   Common `AgentConfiguration` (`src/common/configuration.py`).
    *   Agent-specific `Configuration` dataclasses subclass `AgentConfiguration`.
    *   Architect: `src/architect/configuration.py`'s `Configuration` class no longer defines `use_human_ai`.
    *   Code Reviewer: `CodeReviewerInstanceConfig` dataclass. **UPDATED**: `CodeReviewerInstanceConfig` now has `github_tools_filter` (renamed from `github_tools`) and a new `other_tools` field. New `local_code_reviewer_config()` function provides a configuration for local code review.
    *   Task Manager (`src/task_manager/configuration.py` - REVISED): `Configuration` class includes `use_stub: bool`, `use_human_ai: bool`, and `task_manager_system_prompt: str`.
    *   Orchestrator (`src/orchestrator/configuration.py` - REVISED): `SubAgentConfig` and its subclasses (`RequirementsAgentConfig`, `ArchitectAgentConfig`, `TaskManagerAgentConfig`) now include a `stub_messages: MessageWheel` field, allowing dynamic cycling messages for stubbed agent responses. The `coder_new_pr_agent` and `coder_change_request_agent` in `OrchestratorConfiguration` now default to specific `MessageWheel` instances for their stub messages. **UPDATED**: A new `TesterAgentConfig` dataclass is introduced, subclassing `SubAgentConfig`, with `use_stub: bool = True` and `config: TesterConfiguration`. The `tester_agent` field in `OrchestratorConfiguration` now uses `TesterAgentConfig` as its type. **UPDATED**: A new `CodeReviewerAgentConfig` dataclass is introduced, subclassing `SubAgentConfig`, with `use_stub: bool = True` and `stub_messages` defaulting to `model_code_reviewer_messages`. The `reviewer_agent` field in `OrchestratorConfiguration` now uses `CodeReviewerAgentConfig` as its type. **UPDATED**: A new `github_base_branch: str = "main"` field has been added to `Configuration`. **UPDATED**: The `default_factory` for `coder_new_pr_agent`, `coder_change_request_agent`, and `reviewer_agent` fields in `OrchestratorConfiguration` has been fixed to ensure fresh default instances are created (using `lambda: SubAgentConfig(...)`).
    *   Requirement Gatherer (`src/requirement_gatherer/configuration.py` - **UPDATED**): `Configuration` class now defaults `use_human_ai` to `True` (previously `False`). A new `human_ai_product: Optional[str] = None` field has been added. A `__post_init__` method ensures `human_ai_product` defaults to `prompts.HUMAN_AI_PRODUCT` if `use_human_ai` is `True` and `human_ai_product` is `None`, and raises an error if `human_ai_product` is set while `use_human_ai` is `False`.

## 2. The Memory Bank System (Shift from Conceptual to `langmem`)

The original "Memory Bank" concept described a system of structured Markdown files (`memory-bank/`) for agent knowledge persistence. This concept, detailed in `project_memories/global.md`, served as the initial design principle for externalized memory.

**Current Implementation (`langmem` and `AgentGraph` integration):** The project has integrated the `langmem` library to provide a robust and queryable semantic memory system.
*   **`MemoryConfiguration` (`common.components.memory.MemoryConfiguration`):** A dedicated dataclass to hold memory settings.
*   **`AgentConfiguration` (`common.configuration.AgentConfiguration` - NEW, replaces `BaseConfiguration`):** Now embeds a `MemoryConfiguration` instance.
*   **`SemanticMemory` (`common.components.memory.SemanticMemory` - REVISED):**
    *   Its constructor now accepts `memory_config: Optional[MemoryConfiguration]`.
*   **`AgentGraph` (`common.graph.AgentGraph` - REVISED):**
    *   Can automatically initialize a `SemanticMemory` instance.
    *   **UPDATED**: Now exposes `name`, `checkpointer`, and `store` as properties.
*   **Storage:** Memories are stored in a `BaseStore`.
*   **Namespace:** Memories are namespaced.
*   **Tools:**
    *   Orchestrator (REVISED): Uses direct tools `requirements`, `architect`, `task_manager` (NEW), `coder_new_pr`, `coder_change_request`, `tester`, `code_reviewer` (which invoke sub-graphs/stubs), `memorize` (for memory persistence), `summarize` (now from `common.tools.summarize`), and `get_next_task` (NEW). The `requirements`, `architect`, and `task_manager` tools now update the Orchestrator's state with the `project` object returned by the sub-agent. The `coder_new_pr` and `coder_change_request` tools now return the content of the last message from the sub-agent's result, rather than a summary. **UPDATED**: The `tester` tool now passes the Orchestrator's `project` state to the Tester agent's state, and the Orchestrator's `github_tools` to the Tester agent's graph. **UPDATED**: All sub-agent invocation tools (`requirements`, `architect`, `task_manager`, `coder_new_pr`, `coder_change_request`, `tester`, `code_reviewer`) now return a `Command` object that updates the Orchestrator's state with a `ToolMessage` that includes a `status` (`"success"` or `"error"`) and the sub-agent's `summary` or `error` content. **UPDATED**: The `code_reviewer` tool now passes the Orchestrator's `project` state to the Code Reviewer agent's state. **UPDATED**: The `get_next_task` tool is now provided by `orchestrator.tools.create_read_task_planning_tool`, which supports stub responses based on the `task_manager_agent`'s `use_stub` setting.
    *   Agents based on `AgentGraph` (like `AgentTemplateGraph`): Can get memory tools from `AgentGraph`.
    *   Requirement Gatherer: Uses `create_memorize_tool` and `human_feedback` tool. Its `summarize` tool is now from `common.tools.summarize`. A new `set_project` tool is available. **UPDATED**: The `human_feedback` tool's prompt now includes a `<Product>` section with a `{product}` placeholder, allowing the tool to receive and use a specific product description (e.g., from `human_ai_product` in configuration) to guide its responses. **FIXED**: The `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
    *   Tester: Custom `upsert_memory` tool removed. **UPDATED**: Now includes `common.tools.summarize` and a filtered set of GitHub tools (`set_active_branch`, `create_a_new_branch`, `get_files_from_a_directory`, `create_pull_request`, `create_file`, `update_file`, `read_file`, `delete_file`, `get_latest_pr_workflow_run`). It **no longer includes** `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`.
    *   Code Reviewer: Uses GitHub tools. **UPDATED**: When configured for local review, it can use `common.tools.summarize`, `common.tools.list_files`, and `common.tools.read_file`.
    *   Architect (NEW, REVISED): Uses `create_memorize_tool`, `create_recall_tool`, `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`, and a new `summarize` tool (now from `common.tools.summarize`). `use_human_ai` removed from its config. **FIXED**: The `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
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
*   **UPDATED**: All `AgentGraph`-based agents now utilize a `prechain` mechanism on their `call_model` functions, incorporating `skip_on_summary_and_tool_errors` to manage workflow execution based on summary presence or consecutive tool errors.
*   **UPDATED**: Agent states (e.g., `State` dataclasses) now consistently include an `error: str = ""` field to track fatal errors, building upon the new `AgentState` base.
*   **UPDATED**: The Code Reviewer agent now also uses the `AgentGraph` pattern.

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
        *   `coder_new_pr_agent` (type `SubAgentConfig`) **UPDATED**: `default_factory` fixed to `lambda: SubAgentConfig(stub_messages=model_coder_new_pr_messages)`.
        *   `coder_change_request_agent` (type `SubAgentConfig`) **UPDATED**: `default_factory` fixed to `lambda: SubAgentConfig(stub_messages=model_coder_change_request_messages)`.
        *   `tester_agent` (type `SubAgentConfig`) **UPDATED**: Now of type `TesterAgentConfig`.
        *   `code_reviewer_agent` (type `SubAgentConfig`) **UPDATED**: Now of type `CodeReviewerAgentConfig`. `default_factory` fixed to `lambda: SubAgentConfig(stub_messages=model_code_reviewer_messages)`.
        *   **UPDATED**: A new `github_base_branch: str = "main"` field has been added.
    *   These sub-agent configurations (e.g., `SubAgentConfig`, `ArchitectAgentConfig`, `TaskManagerAgentConfig` (NEW), also defined/imported in this module) typically allow specifying whether to use a full agent or a stub, and can contain agent-specific nested configurations.
    *   **UPDATED**: `SubAgentConfig` now includes `stub_messages: MessageWheel = MessageWheel(["I finished the task."])` and its attributes have detailed docstrings. Its subclasses (`RequirementsAgentConfig`, `ArchitectAgentConfig`, `TaskManagerAgentConfig`) now default `stub_messages` to specific `model_*_messages` instances. The `coder_new_pr_agent` and `coder_change_request_agent` in `OrchestratorConfiguration` are now initialized with `SubAgentConfig` instances that explicitly set their `stub_messages` to `model_coder_new_pr_messages` and `model_coder_change_request_messages` respectively.
    *   **UPDATED**: A new `TesterAgentConfig` dataclass is introduced, subclassing `SubAgentConfig`, with `use_stub: bool = True` and `config: TesterConfiguration = field(default_factory=TesterConfiguration)`.
    *   **NEW**: A new `CodeReviewerAgentConfig` dataclass is introduced, subclassing `SubAgentConfig`, with `use_stub: bool = True` and `stub_messages` defaulting to `model_code_reviewer_messages`.
    *   As an example of nested configuration, the `ArchitectAgentConfig` contains a nested `config: architect.configuration.Configuration` field, and this nested Architect configuration is what reflects changes like the removal of `use_human_ai` from the Architect's own configuration file. The new `TaskManagerAgentConfig` similarly contains a nested `config: task_manager.configuration.Configuration`.
*   **State (`src/orchestrator/state.py` - REVISED):** Added `summary: str = ""` field to its `State` dataclass. A new `project: Optional[Project] = None` field has been added to store the active project information. **UPDATED**: A new `error: str = ""` field has been added to track fatal errors.
*   **Graph (`src/orchestrator/graph.py` - REVISED):**
    *   The graph structure has been refactored to use a `ToolNode` for invoking all agent-specific tasks and other utilities.
    *   The `_create_orchestrate` node is renamed to `_create_orchestrator`.
    *   The previous delegation logic (`_create_delegate_to` and individual agent node creators like `_create_requirements_node`, `_create_architect_node`, etc.) has been removed.
    *   The LLM is now bound with a new set of tools (see Orchestrator Tools under Key Concepts or Tools section below). This now includes a `task_manager` tool. The `summarize` tool is now imported from `common.tools`. **UPDATED**: The `get_next_task` tool has been added to the Orchestrator's toolset. **UPDATED**: The `get_next_task` tool is now provided by `tools.create_read_task_planning_tool`, initialized with `self._agent_config.task_manager_agent.use_stub`.
    *   **UPDATED**: The `code_reviewer_graph` initialization now conditionally uses `stubs.CodeReviewerStub` if `self._agent_config.reviewer_agent.use_stub` is `True`, otherwise it uses `code_reviewer.graph.CodeReviewerGraph` with `code_reviewer.graph.github_code_reviewer_config()` as its configuration.
    *   **UPDATED**: All sub-agent stub initializations (e.g., `RequirementsGathererStub`, `ArchitectStub`, `TaskManagerStub`, `CoderNewPRStub`, `CoderChangeRequestStub`, `TesterStub`, `CodeReviewerStub`) now pass the `stub_messages` from their respective agent configurations (`self._agent_config.<agent_name>_agent.stub_messages`) to the stub constructors.
    *   **UPDATED**: The `maybe_mock_github` function, used to get GitHub tools, now receives `base_branch=self._agent_config.github_base_branch`, allowing the Orchestrator to use a configurable base branch for GitHub interactions. The `TesterAgentGraph` is now initialized with `github_tools`.
    *   Conditional logic (`_create_orchestrate_condition`) routes from the main `orchestrator` (model call) node to the `ToolNode` if tool calls are present, or to `END` if a `summary` or `error` is available in the state, otherwise back to the `orchestrator` node. **UPDATED**: The condition for routing to `ToolNode` now explicitly checks if the last message is an `AIMessage` with tool calls.
    *   Sub-agent graphs (or their stubs, including for Task Manager) are passed to tool factory functions which create the tools bound to the Orchestrator's LLM.
    *   **UPDATED**: The `orchestrator` function (model call) is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
*   **Stubs (`src/orchestrator/stubs/__init__.py` - REVISED):**
    *   **UPDATED**: The `MessageWheel` class (for cycling through predefined messages) is now defined at the top level of this module.
    *   **UPDATED**: The `StubGraph` base class now has a `_stub_messages` attribute, initialized via its constructor, and its `run_fn` now uses `self._stub_messages.next()` to retrieve the next message. This ensures each stub instance maintains its own message sequence.
    *   **UPDATED**: Predefined `MessageWheel` instances (`model_requirements_messages`, `model_architect_messages`, `model_task_manager_messages`, `model_coder_new_pr_messages`, `model_coder_change_request_messages`, `model_tester_messages`, `model_code_reviewer_messages`) are now defined globally in this module. `model_code_reviewer_messages` has been simplified to `"""The code looks good, I approve."""`.
    *   The `StubGraph` base class's `run_fn` is now expected to return a dictionary that includes a `summary` field. The graph built by `StubGraph` now adds an edge from its "run" node to `END`.
    *   `RequirementsGathererStub`, `ArchitectStub`, `CoderNewPRStub`, `CoderChangeRequestStub` are updated to align with this, providing a `summary` in their output. `RequirementsGathererStub` now also returns a `project_name` and the `project` object itself.
    *   `TesterStub` (NEW class, subclasses `StubGraph`): Replaces the previous simple `stubs.tester` function.
    *   `CodeReviewerStub` (NEW class, subclasses `StubGraph`): Replaces the previous simple `stubs.reviewer` function.
    *   `TaskManagerStub` (NEW class, subclasses `StubGraph`): Provides a stub for the Task Manager agent.
    *   **UPDATED**: All specific `*Stub` classes (`RequirementsGathererStub`, `ArchitectStub`, `TaskManagerStub`, `CoderNewPRStub`, `CoderChangeRequestStub`, `TesterStub`, `CodeReviewerStub`) now accept a `stub_messages` argument in their `__init__` and pass it to the `super().__init__` call, allowing their responses to be dynamically controlled by the Orchestrator's configuration.
    *   The old simple stub functions (`stubs.tester`, `stubs.reviewer`, `stubs.memorizer`) have been removed.
*   **Tools (`src/orchestrator/tools.py` - REVISED):**
    *   The `Delegate` tool has been removed.
    *   The `store_memory` tool has been effectively replaced by the `memorize` tool. Its `origin` parameter's type hint is updated to include `code_reviewer`.
    *   New tool factory functions are introduced:
        *   `create_requirements_tool(agent_config, requirements_graph)`: Creates the `requirements` tool. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result. **UPDATED**: The `ToolMessage` returned now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
        *   `create_architect_tool(agent_config, architect_graph)`: Creates the `architect` tool. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result. **UPDATED**: The `ToolMessage` returned now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
        *   `create_task_manager_tool(agent_config, task_manager_graph)` (NEW): Creates the `task_manager` tool. This tool now returns a `Command` to update the Orchestrator's state with the `project` information from the sub-agent's result. **UPDATED**: The `ToolMessage` returned now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
        *   `create_coder_new_pr_tool(agent_config, coder_new_pr_graph)`: Creates the `coder_new_pr` tool. **UPDATED**: This tool now returns a `Command` with a `ToolMessage` including a `status` field (`"success"` or `"error"`) and its `content` can be the last message from the sub-agent's result or the sub-agent's `error` message.
        *   `create_coder_change_request_tool(agent_config, coder_change_request_graph)`: Creates the `coder_change_request` tool. **UPDATED**: This tool now returns a `Command` with a `ToolMessage` including a `status` field (`"success"` or `"error"`) and its `content` can be the last message from the sub-agent's result or the sub-agent's `error` message.
        *   `create_tester_tool(agent_config, tester_graph)`: Creates the `tester` tool. **UPDATED**: This tool now passes the Orchestrator's `project` state to the Tester agent's state, and the Orchestrator's `github_tools` to the Tester agent's graph. **UPDATED**: The `ToolMessage` returned now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
        *   `create_code_reviewer_tool(agent_config, code_reviewer_graph)`: Creates the `code_reviewer` tool. **UPDATED**: The `code_reviewer_graph` parameter type hint is now `CodeReviewerGraph`. **UPDATED**: This tool now passes the Orchestrator's `project` state to the Code Reviewer agent's state. **UPDATED**: The `ToolMessage` returned now includes a `status` field (`"success"` or `"error"`) and its `content` can be the sub-agent's `summary` or `error` message.
    *   These tools take `content` (and other injected args like `tool_call_id`, `state`, `config`), invoke the respective sub-graph (or stub), and return the `summary` from the sub-graph's result as the tool's output.
    *   **UPDATED**: The `coder_new_pr` and `coder_change_request` tools now return `result["messages"][-1].content` (the content of the last message) instead of `result["summary"]`.
    *   The `summarize` tool implementation has been removed from this file, as it is now centralized in `src/common/tools/summarize.py`.
    *   **UPDATED**: The `create_read_task_planning_tool` function (for the `get_next_task` tool) has been moved here from `src/common/tools/read_task_planning.py`. It now takes the Orchestrator's state as input and raises errors instead of returning error strings.
*   **Prompts (`src/orchestrator/prompts.py` and `src/orchestrator/memory/` - REVISED):**
    *   `src/orchestrator/prompts.py`: The static `ORCHESTRATOR_SYSTEM_PROMPT` string definition has been removed. The `get_prompt()` function continues to load prompt content from markdown files. **UPDATED**: The prompt now states "If the user has provided an instruction, direct the flow to the appropriate agent based on the project state." (previously "Once you have the topic of the conversation...").
    *   `src/orchestrator/memory/absolute.md`, `process.md`, `project_states.md`, `team.md`: These markdown files, which constitute the Orchestrator's system prompt, have been significantly updated to reflect the new toolset (direct agent invocation tools including `task_manager`, `memorize`, `summarize`, `get_next_task`) and the refined operational workflow (e.g., explicit instruction to use the `summarize` tool when no tasks are pending, and using `get_next_task` to determine the next task). `project_states.md` now includes a "Create tasks" step and an updated Mermaid flowchart that includes a "Get task" step. `team.md` now includes a section for the "Task Manager" agent and clarifies that the Coder agent uses tasks from the `task_manager` and that the Orchestrator should use `get_next_task` to retrieve task content for the Coder. **UPDATED**: The instruction to call the `summarize` tool when no tasks are pending has been rephrased to emphasize it is a conditional action ("IF no tasks are pending"). **UPDATED**: `absolute.md` now states "You MUST NEVER ask clarifying questions." (previously "MUST NOT") and adds new rules: "You MUST respond with 'I'm not sure what to do', if it is unclear which tool to delegate to." and "You MUST reply to pleasantries like 'Hi', 'Thank you', and 'Bye' in a polite manner.". **UPDATED**: `process.md` now includes the instruction: "IMPORTANT when sending a task copy the task received in `get_next_task` AS IS without changing or summarizing it". **UPDATED**: The `project_states.md` prompt's numbered list and Mermaid flowchart have been updated to reflect that the Tester agent's role is to `Write e2e tests given requirements and architecture` (step 6), occurring *before* code review. The workflow now loops back to `Code & Implement` if code review fails. **UPDATED**: The `team.md` prompt's description for the Tester agent has been updated to clarify its role: it `uses the existing requirements to come up with e2e test scenarios`, `MUST delegate to it when needing to create e2e tests for product/architecture requirements`, `MUST send details about product/architecture`, and `NEVER send coding implementation details such as what PRs or branches where created or features coded`.

#### 5.2. Architect (`src/architect/`) (REWORKED, REVISED)
*   **Configuration (`src/architect/configuration.py` - REVISED):**
    *   The `use_human_ai: bool = False` field has been removed.
*   **State (`src/architect/state.py` - REVISED):** Added `summary: str = ""` field. A new `project: Project` field has been added to store the active project information. **UPDATED**: A new `error: str = ""` field has been added to track fatal errors.
*   **Graph (`src/architect/graph.py` - REVISED):**
    *   The Architect's graph now includes `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`, and a `summarize` tool (now imported from `common.tools`) in its set of available tools.
    *   The `call_model` function now formats the system prompt with `project_dir=state.project.path`. It also prints formatted messages using `common.utils.format_message`.
    *   **UPDATED**: The `_create_call_model` function is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
*   **Tools (`src/architect/tools.py` - REVISED):**
    *   The `summarize` tool implementation has been removed from this file, as it is now centralized in `src/common/tools/summarize.py`.
    *   The `read_file`, `create_file`, and `list_files` tools have been removed from this file, as they are now centralized in `src/common/tools/`.
    *   **FIXED**: The `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
*   **Prompts (`src/architect/prompts.py` - REVISED):**
    *   The Architect's system prompt (`architect_system_prompt`) has been updated to include a new "Summarize" step. This step instructs the agent to write a `summary` of the architecture and call its `summarize` tool before proceeding to the "Finalize" step. The prompt now dynamically references the active project directory (`{project_dir}`). **UPDATED**: The prompt's description of the core project files and their interdependencies (including the Mermaid flowchart and numbered list) has been updated. `projectRequirements.md` is now explicitly listed as a core file and is positioned as an intermediary document between `projectbrief.md` and `systemPatterns.md`/`techPatterns.md`. The description of `projectbrief.md` is now more focused on its foundational role. The numbering of core files in the prompt has been adjusted (e.g., `systemPatterns.md` is now 3, `techPatterns.md` is 4, `progress.md` is 5). **UPDATED**: The prompt now includes an instruction to ensure the `{project_dir}` exists and create it if necessary before writing new files, explicitly mentioning the `create_directory` tool. It also clarifies that `list_files` should be used on the `{project_dir}` directory and that `create_file` should write files under `{project_dir}`. **UPDATED**: The prompt for `projectbrief.md` now instructs the Architect to add "This project is for hobby purposes" if it's a hobby/personal project. The "Summarize" step now explicitly requires the Architect to clarify if the project is a 'hobby' project in its summary. **UPDATED**: The prompt for the `memorize` tool now explicitly states to "Pass the `content` to be memorized and the `context` within which it was stated."

#### 5.3. Coder (`src/coder/`)
*   **State (`src/coder/state.py` - REVISED):**
    *   Changed from `TypedDict` to `@dataclass(kw_only=True)`.
    *   Added `summary: str = ""` field. **UPDATED**: A new `error: str = ""` field has been added to track fatal errors.
*   **Graph (`src/coder/graph.py` - UPDATED):** Accesses state messages via `state.messages` instead of `state["messages"]` due to state being a dataclass. **UPDATED**: The `coder_new_pr_config` and `coder_change_request_config` now include the `get_latest_pr_workflow_run` tool in their `allowed_tools` list. **UPDATED**: The `CallModel` class has been refactored into a function `_create_call_model`, which is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
*   **Prompts (`src/coder/prompts.py` - UPDATED):** The `NEW_PR_SYSTEM_PROMPT` has been updated to refer to the "base branch" instead of "main" for repository interactions. **UPDATED**: The `NEW_PR_SYSTEM_PROMPT` now includes an explicit instruction to use the actual branch name returned by the `get_branch_name` tool, as it may differ from the requested branch name.

#### 5.4. Code Reviewer (`src/code_reviewer/`) (REVISED)
*   **Architecture:** **UPDATED**: Now uses the `AgentGraph` pattern, with `CodeReviewerGraph` subclassing `common.graph.AgentGraph`.
*   **Configuration (`src/code_reviewer/graph.py` - UPDATED):**
    *   `CodeReviewerInstanceConfig` now has `github_tools_filter` (renamed from `github_tools`) and a new `other_tools: List[Tool]` field.
    *   New `local_code_reviewer_config()` function provides a configuration for local code review, specifying `common.tools.summarize`, `common.tools.list_files`, and `common.tools.read_file` as `other_tools`.
*   **State (`src/code_reviewer/state.py` - REVISED):** Added `summary: str = ""` field. **UPDATED**: A new `project: Optional[Project] = None` field has been added to store the active project information. **UPDATED**: A new `error: str = ""` field has been added to track fatal errors.
*   **Graph (`src/code_reviewer/graph.py` - REVISED):**
    *   The internal `DiffHunkFeedback` and `DiffFeedback` Pydantic models have been removed.
    *   The `CallModel` class now formats the system prompt with `project_path` from `state.project` and returns `project` in the state.
    *   The `graph_builder` function has been renamed to `_graph_builder` and is now used internally by `CodeReviewerInstanceConfig`.
*   **Tool Naming:** Referred to as `code_reviewer` in Orchestrator's tools and stubs.
*   **Prompts (`src/code_reviewer/prompts.py` - UPDATED):**
    *   **NEW**: A `LOCAL_REVIEW_PROMPT` has been added for local code review, which includes a `Project Path: {project_path}` placeholder and instructions to read relevant files, summarize, and call the `summarize` tool.

#### 5.5. Tester (`src/tester/`) (REWORKED)
*   **State (`src/tester/state.py` - REVISED):** Added `summary: str = ""` field. **UPDATED**: A new `project: Project` field has been added to store the active project information. **UPDATED**: A new `error: str = ""` field has been added to track fatal errors.
*   **Graph (`src/tester/graph.py` - REVISED):**
    *   The internal `_create_call_model` function, responsible for preparing and invoking the LLM, now explicitly accepts the agent's `Configuration` (as `agent_config`).
    *   The system prompt used in `_create_call_model` is now directly sourced from `agent_config.system_prompt`, improving how the configured prompt is passed and utilized within the graph's execution logic. **UPDATED**: The `call_model` function now formats the system prompt with `project_path=state.project.path`.
    *   **UPDATED**: The `__init__` method now accepts `github_tools: List[Tool]` and passes it to the instance. It also includes `common.tools.summarize` and a filtered set of GitHub tools (`set_active_branch`, `create_a_new_branch`, `get_files_from_a_directory`, `create_pull_request`, `create_file`, `update_file`, `read_file`, `delete_file`, `get_latest_pr_workflow_run`) in the agent's set of available tools. It **no longer includes** `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, and `common.tools.read_file`.
    *   **NEW**: `get_tester_github_tools()` and `filter_github_tools()` helper functions are added to manage the specific GitHub tools required by the Tester agent.
    *   **UPDATED**: The direct export of `graph = TesterAgentGraph().compiled_graph` has been removed from this file.
    *   **UPDATED**: The `_create_call_model` function is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
*   **`src/tester/lg_server.py` (NEW FILE):** This new file is responsible for setting up the Tester agent's graph for the LangGraph server. It initializes GitHub tools using `maybe_mock_github` and `get_github_tools`, then creates and compiles the `TesterAgentGraph` instance, passing the initialized `github_tools`. It exports the compiled graph as `graph`.
*   **`src/tester/__init__.py` (UPDATED):** The `graph` import path has been updated from `tester.graph` to `tester.lg_server`.
*   **Prompts (`src/tester/prompts.py` - REVISED):**
    *   **UPDATED**: The `SYSTEM_PROMPT` now includes a `Project Path: {project_path}` placeholder.
    *   **UPDATED**: The `test-agent-system-prompt.md` content has been **significantly updated**:
        *   It now explicitly states the Tester Agent specializes in **end-to-end (e2e) and acceptance testing** and **ONLY creates test files, never application or configuration code**.
        *   A new **"ABSOLUTE PROHIBITIONS"** section lists forbidden actions (creating business logic, `if __name__` blocks, executable applications, application functionality, application imports, non-test files).
        *   A new **"YOU CAN ONLY CREATE"** section specifies allowed outputs (test functions, assertions, setup/teardown, test data files).
        *   "Output Requirements" are refined to emphasize e2e/acceptance tests only, and explicitly state **NEVER create, modify, or upload any application source code**.
        *   New **"File Restrictions"** detail allowed test file patterns and explicitly forbidden file types (application source code, config, main files, etc.), and prohibit creating "dummy" application files or fixtures.
        *   New **"CRITICAL ASSUMPTION RULES"** state that the agent should assume application code already exists, that the coder agent will create missing application files, and that the Tester should never create application files itself.
        *   "Test Focus" is clarified to be "End-to-End & Acceptance Testing" and "Application Interface Testing".
        *   "Test Scenarios" are expanded to include user acceptance criteria, complete feature flows, and real-world usage.
        *   "Test Structure" and "Test Completeness" sections are updated to align with e2e testing frameworks and realistic scenarios.
        *   The "Role" section is heavily revised to reinforce the agent's strict focus on e2e/acceptance tests, black-box testing, and the absolute prohibition against creating application code or non-test files, including mandatory filename verification.
        *   The "Workflow" section is updated to include: `IDENTIFY` application type, `CREATE a new branch` (`test-agent-*`), `MANDATORY VALIDATION BEFORE CREATING ANY FILE` (a series of self-check questions), `VERIFY` tests only reference existing application files, `UPLOAD ONLY TEST FILES` to GitHub using `create_file` or `update_file`, and `CREATE a pull request` from the test branch to `main`.
        *   The "Workflow Checklist" and "Key Rules" are updated to reflect these new, stricter guidelines, emphasizing acceptance criteria, user workflows, and the absolute prohibition on creating application source code. It also adds a final instruction to reply with the PR number and branch name upon completion.

#### 5.6. Requirement Gatherer (`src/requirement_gatherer/`) (REVISED)
*   **Configuration (`src/requirement_gatherer/configuration.py` - UPDATED):**
    *   `use_human_ai: bool = True` (default changed from `False` to `True`).
    *   `human_ai_product: Optional[str] = None` (NEW field).
    *   A `__post_init__` method has been added to handle the default value of `human_ai_product` based on `use_human_ai` and to raise a `ValueError` if `human_ai_product` is set when `use_human_ai` is `False`.
*   **State (`src/requirement_gatherer/state.py` - REVISED):** Added `summary: str = ""` field. A new `project: Optional[Project] = None` field has been added to store the active project information. **UPDATED**: A new `error: str = ""` field has been added to track fatal errors.
*   **Graph (`src/requirement_gatherer/graph.py` - REVISED):** The conditional logic in `_create_gather_requirements` for routing to the tool node is updated to `if state.messages and state.messages[-1].tool_calls:`. The `summarize` tool is now imported from `common.tools`. The `set_project` tool has been added to the agent's toolset. **UPDATED**: The `_create_call_model` function is now decorated with `@prechain(skip_on_summary_and_tool_errors())`. **UPDATED**: The condition for routing to `ToolNode` now explicitly checks if the last message is an `AIMessage` with tool calls. The condition for `END` now includes `state.error`.
*   **Tools (`src/requirement_gatherer/tools.py` - REVISED):** The `summarize` tool implementation has been removed from this file, as it is now centralized in `src/common/tools/summarize.py`. A new `set_project` tool is introduced to set the project name and initialize the `Project` object in the state. **UPDATED**: The `human_feedback` tool's prompt template has been updated to include a `<Product>` section with a `{product}` placeholder, and its `ai_user.ainvoke` call now passes `agent_config.human_ai_product` to format this section, ensuring the AI's responses are guided by the specified product context. New rubric, instructions, and reminder lines have been added to reinforce adherence to the product definition. **FIXED**: The `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
*   **Prompts (`src/requirement_gatherer/prompts.py` - REVISED):** The prompt has been updated to include a new step `0. **Project name**` which instructs the agent to ask for the project name and use the `set_project` tool if it's not provided. **UPDATED**: The prompt's description of the agent has been softened from "relentlessly curious" to "smart and curious". New "IMPORTANT" rules have been added to limit questions for "HOBBY" projects (max 5 questions) and to focus on the most important details. The numbering of operating principles has been adjusted due to the removal of "Product-first mindset" and "Zero-assumption rule". The Mermaid flowchart and "Core File" table have been simplified by removing `stakeholders.md` and `constraints.md`. The "Clarifying-Question Checklist" has been updated with new "IMPORTANT" notes and has removed sections on "Users & Personas" and "Business Constraints". The "Functional Requirements" section has been streamlined by removing "Business Rules", "State & Lifecycle", and "Administration & Configuration". New "IMPORTANT" instructions have been added at the end to emphasize reducing questions and adhering to the 5-question limit for hobby projects. A new `HUMAN_AI_PRODUCT` constant has been added, providing a default product description for the `human_feedback` tool.

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
*   **State (`src/task_manager/state.py` - REVISED):** Added `summary: str = ""` field. (Used by `TaskManagerStub` and consistent with other agents). A new `project: Project` field has been added to store the active project information. **UPDATED**: A new `error: str = ""` field has been added to track fatal errors.
*   **Tools:** Uses `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`. The Orchestrator uses a `task_manager` tool to invoke this agent. Now also uses the `summarize` tool (from `common.tools.summarize`).
*   **Prompts (`src/task_manager/prompts.py` - UPDATED):** Contains `SYSTEM_PROMPT` used by the agent. This prompt has been significantly updated to include:
    *   **NEW**: "Path Security Constraints" section, strictly confining file operations to the `{project_path}`.
    *   **NEW**: "HOBBY MODE" section, detailing behavior for single-task, no-testing, no-CI/CD, no-roadmap projects if "HOBBY" is in the user's request. This includes specific task structure, implementation sequence, and deliverable requirements (e.g., "Beyond Hello World").
    *   **Revised Task Splitting Guidelines:** Tasks now sized for 4-6 hours of work. Stricter rules for splitting tasks (>6 hours). Each task *must* result in a buildable and runnable deliverable, even initialization tasks (e.g., "hello world"). Avoid partial/non-functional components.
    *   **New Testing Requirements Section:** Mandates that every functional task includes tests (unit, integration, edge cases). Test implementation is not optional and time for it must be factored into estimation.
    *   **New CI/CD Requirements Section:** Mandates GitHub Actions workflow setup for tests early in the project. Specifies CI configuration details (running tests on PRs/pushes, reporting failures, linting). Outlines mandatory task sequencing for the project plan: Repository initialization FIRST, Basic project setup SECOND, CI/CD setup THIRD, Core feature implementation FOURTH, with follow-up CI/CD improvements throughout.
    *   **Expanded `task.md` Metadata Schema:** The `details` field is now removed. The `description` field is expanded to include a "General Description" and "High-Level Steps" (replacing the previous `details` field). New fields added for contextual information: `contextualInformation`, `technicalRequirements`, `securityConsiderations`, `relatedFeatureContext`, `systemPatternGuidance`, `testingRequirements`. **UPDATED**: The `technicalRequirements` field now refers to `techPatterns.md`. The `securityConsiderations` field has been removed. The `relatedFeatureContext` field has been renamed to `relatedCodingContext` and now refers to `codingContext.md`. `dependencies` is now `(empty for HOBBY mode)`. `testingRequirements` now distinguishes between Normal and HOBBY mode.
    *   **Strengthened `roadmap.md` Guidelines:** Emphasizes including *ALL* tasks without exception, performing validation steps to ensure no tasks are missing, and logging task counts. Reinforces task sequencing (repo init -> project setup -> CI -> features) and scheduling periodic CI/CD improvement tasks. **UPDATED**: `roadmap.md` creation is now explicitly "Normal Mode Only" and skipped in HOBBY mode.
    *   **NEW**: `tasks.json` schema introduced for a flat list of all engineering tasks.
    *   **Revised Step-by-Step Instructions (`Execution Process`):**
        *   **Step 1 (Project Validation and Analysis):** Now includes "Check for HOBBY Mode" and specific instructions for HOBBY mode regarding context extraction.
        *   **Step 2 (Tasks Creation):** Now explicitly requires extracting and including *all* relevant context from input files (e.g., `projectRequirements.md`, `techContext.md`, `securityContext.md`, `featuresContext.md`, `systemPatterns.md`, `testingContext.md`) directly into each task, prohibiting external file references. Details field is replaced by `description` with `General description` and `High-level steps`. Tasks must produce buildable/runnable deliverables. **UPDATED**: References to `techContext.md` changed to `techPatterns.md`. References to `featuresContext.md` changed to `codingContext.md`. Instructions for extracting `securityContext.md` have been removed. Now includes detailed instructions for creating tasks in both HOBBY and Normal modes.
        *   **Step 3 (Planning Creation):** Now explicitly states "HOBBY Mode: Skip this step entirely - do not create roadmap.md". For Normal Mode, it reinforces counting tasks, ensuring *every single* task is included in the roadmap, verifying counts, and scheduling tasks in the *correct sequence* (repo init -> project setup -> CI -> features), with CI/CD tasks scheduled *after* prerequisites.
    *   **New Detailed Guidelines Sections:**
        *   `Context Extraction Guidelines`: Principles for specific, focused, accurate extraction.
        *   **NEW**: `Task Self-Containment Requirements`: Critical rules for tasks to be completely self-contained with no external references or variables.
        *   `Task-Specific Document Extraction Guidelines`: Detailed instructions for extracting information from `TestingContext.md`, `TechContext.md`, `SecurityContext.md`, `FeatureContext.md`. **UPDATED**: `TechContext.md Extraction` heading changed to `techPatterns.md Extraction`. `SecurityContext.md Extraction` section has been removed. `FeatureContext.md Extraction` heading changed to `codingContext.md Extraction`. `Include relevant code examples or patterns provided` changed to `Describe relevant patterns and architectural approaches using natural language (never include actual code)`.
        *   `CI/CD Task Creation Guidelines`: Instructions for creating CI/CD tasks, their sequencing, and evolution.
        *   `Details Field Format` section removed, replaced by `Description Field Format`.
        *   `Test Creation Guidelines`: Guidance on specific test cases, edge cases, positive/negative scenarios, mocking, and testing levels. **UPDATED**: References to `techContext.md` changed to `techPatterns.md`.
        *   `Functional Deliverable Guidelines`: Ensures each task produces a buildable, runnable deliverable, from "hello world" for initialization to integrated features. **UPDATED**: Now distinguishes between "Normal Mode Deliverable Requirements" and "HOBBY Mode Deliverable Requirements`.
        *   `GitHub Actions CI Configuration Guidelines`: Details for configuring CI workflows. **UPDATED**: Now describes workflow configuration requirements using natural language specifications (never actual YAML code).
    *   **Updated Technical Guardrails:** Reinforces that tasks must be self-contained, no external file references, mandatory test implementation, required CI setup regardless of input, CI/CD setup after repo init/basic setup, every task must result in a buildable/runnable deliverable, and task sequencing must follow logical order. **UPDATED**: Guardrails implicitly updated to align with the removal of `securityContext.md` and the renaming of `featuresContext.md` to `codingContext.md`. **NEW**: Includes strict security rules for path access, explicit instructions to never include `{project_path}`, `{project_name}`, or variables in task details, and to never include actual code in task definitions. Distinguishes guardrails for Normal vs. HOBBY mode.
    *   The prompt now dynamically references the active project name (`{project_name}`) and path (`{project_path}`). **UPDATED**: The prompt now explicitly states that it will receive input documents in `{project_path}` and the project name is `{project_name}`. It also includes a new mandatory instruction to write a `summary` of the created tasks and call the `summarize` tool. The prompt now states that it will verify "all seven required files" (previously "eight").
*   **Graph (`src/task_manager/graph.py` - UPDATED):** The `call_model` function now includes logic to dynamically determine `project_name` and `project_path` from `state.project` (handling both dict and Project object types), with hardcoded defaults for `use_stub=True`. These values are then used to format the system prompt. **UPDATED**: The `_create_call_model` function is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.

## 6. Testing Framework (`tests/`) (UPDATED)

*   **NEW**: `tests/datasets/__init__.py`: Placeholder file.
*   **NEW**: `tests/datasets/orchestrator_dataset.py`: New dataset for orchestrator tool usage evaluation, including `uuid4_generator` for deterministic UUIDs and `create_orchestrator_tool_usage_dataset` function.
*   **NEW**: `tests/evaluations/__init__.py`: Placeholder file.
*   **NEW**: `tests/evaluations/orchestrator/__init__.py`: Placeholder file.
*   **NEW**: `tests/evaluations/orchestrator/test_tools.py`: New asynchronous test `test_correctness` for orchestrator tool usage, using LangSmith evaluation with a custom `tool_usage_correctness` evaluator that calculates precision, recall, and F1-score based on missing and extra tool calls.
*   **`tests/datasets/requirement_gatherer_dataset.py` (UPDATED):**
    *   The dataset name has been updated to `"Requirement-gatherer-dataset-human-ai"`.
    *   A new `FIRST_MESSAGE` constant has been added, providing a detailed initial project description for the agent.
    *   The input content for the human message in the dataset examples now uses `FIRST_MESSAGE`.
    *   The expected output content has been updated to `"Requirements are confirmed"`.
    *   **UPDATED**: Minor formatting change in the `outputs` dictionary.
*   **NEW**: `tests/scenarios/fibonacci/eval.py`: A new evaluation script designed to verify the output of the Fibonacci scenario runs. It performs the following steps:
    *   Clones the GitHub repository associated with the scenario run to a temporary directory (`/tmp/ai-nexus/{run_id}`) using a GitHub App installation token for authentication.
    *   Checks out the specific branch (`run["branch"]`) created by the Coder agent.
    *   Verifies the presence of `Cargo.toml` in the cloned repository.
    *   Copies Rust test files from `tests/scenarios/fibonacci/tests/` into the cloned repository's `tests/` directory.
    *   Executes `cargo check` to ensure the generated Rust code is syntactically correct and compiles.
    *   Executes `cargo test` to run the copied unit tests against the generated Fibonacci library.
    *   Logs success or failure based on the execution of these steps.
*   **`tests/scenarios/fibonacci/run.py` (RENAMED & UPDATED):** This file was `tests/scenarios/fibonacci.py`. It is now `tests/scenarios/fibonacci/run.py`. It is a new test scenario demonstrating the orchestration of multiple agents (using stubbed responses for most, and a real Coder agent) to create a Rust Fibonacci iterator library. This scenario showcases the dynamic stub message feature. **UPDATED**: The `OrchestratorConfiguration` in this scenario now explicitly sets `github_base_branch="fibonacci-base"`. **UPDATED**: Now defines a `BASE_BRANCH` constant (imported from `tests/scenarios/fibonacci/__init__.py`) and updates stub messages for `requirements_agent` and `task_manager_agent` to reflect the scenario's specific requirements. Includes logging for execution flow. **NEW**: The scenario now includes a concept of a "run" with structured metadata (`ScenarioRun` TypedDict) including `run_name`, `run_id`, `pr_number`, and `branch`. It extracts the PR number and branch name from the Coder agent's output using an LLM (`google_genai:gemini-2.0-flash`) and persists this run metadata to a JSON file (e.g., `tests/scenarios/fibonacci/scenario_runs/{run_id}.json`). The `RunnableConfig` for the Orchestrator now includes `run_name` and `run_id`. This scenario now includes more specific `stub_messages` for the `architect_agent` and `task_manager_agent` to guide them towards creating a Rust library with `Cargo.toml` and `src/lib.rs` exporting a `Fibonacci` struct implementing `Iterator`. The initial `HumanMessage` content has also been updated to be more detailed. This scenario's output is now designed to be evaluated by `tests/scenarios/fibonacci/eval.py`. **UPDATED**: The `requirements_agent`, `architect_agent`, `task_manager_agent`, `coder_new_pr_agent`, and `coder_change_request_agent` are now configured with `use_stub=False`. Specifically, the `requirements_agent` now includes a `config` with `use_human_ai=True` and a `human_ai_product` description for a hobby Rust Fibonacci project. The `reviewer_agent` is now explicitly typed as `CodeReviewerAgentConfig` and configured with `use_stub=False`. The `tester_agent` is now explicitly typed as `TesterAgentConfig` and configured with `use_stub=False`.
*   **NEW**: `tests/scenarios/fibonacci/tests/scenario_eval_tests.rs`: Contains Rust unit tests (`test_fibonacci`) to verify the correctness of the `Fibonacci` iterator implementation generated by the Coder agent in the scenario.
*   **NEW**: `tests/scenarios/fibonacci/__init__.py`: A new `__init__.py` file has been added to `tests/scenarios/fibonacci/`, making it a Python package. It defines `BASE_BRANCH = "fibonacci-base"`.
*   **NEW**: `tests/scenarios/stack/` (NEW SCENARIO): A new end-to-end test scenario for building a Rust stack library.
    *   **`tests/scenarios/stack/__init__.py` (NEW FILE):** Defines `BASE_BRANCH = "stack-base"`.
    *   **`tests/scenarios/stack/run.py` (NEW FILE):**
        *   Demonstrates an orchestrated AI workflow for creating a Rust stack library.
        *   Configures the Orchestrator with `github_base_branch="stack-base"`.
        *   Sets `requirements_agent`, `architect_agent`, `task_manager_agent`, `reviewer_agent`, and `tester_agent` to `use_stub=True` with specific `MessageWheel` messages.
        *   Sets `coder_new_pr_agent` and `coder_change_request_agent` to `use_stub=False` (using real Coder agent).
        *   Includes logic to handle human interrupts during the workflow.
        *   Extracts the PR number and branch name from the Coder agent's output using an LLM (`google_genai:gemini-2.0-flash`) and persists the scenario run metadata (including `run_name`, `run_id`, `pr_number`, `branch`) to a JSON file in `tests/scenarios/stack/scenario_runs/{run_id}.json`.
        *   Utilizes `InMemorySaver` and `InMemoryStore` for graph state management.
        *   Ensures LangSmith tracing is completed using `wait_for_all_tracers()`. **UPDATED**: The `reviewer_agent` is now explicitly typed as `CodeReviewerAgentConfig`. The `tester_agent` is now explicitly typed as `TesterAgentConfig`.
*   **`tests/scenarios/__init__.py` (NEW):** Defines `BASE_BRANCHES` list for centralized management of base branch names used in testing scenarios.
*   **`tests/scenarios/cleanup_github.py` (UPDATED):** Now utilizes the centralized GitHub App authentication utility (`common.utils.github.app_get_client_from_credentials()`) instead of implementing authentication logic directly.
*   **`tests/scenarios/setup_github.py` (UPDATED):** Now utilizes the centralized GitHub App authentication utility (`common.utils.github.app_get_client_from_credentials()`) instead of implementing authentication logic directly.
*   **`tests/integration_tests/test_architect_agent.py` (UPDATED):**
    *   Tests updated to reflect the Orchestrator's new tool usage (e.g., `memorize` instead of `store_memory`, and direct agent tool calls like `code_reviewer` instead of generic `Delegate`).
    *   **UPDATED**: The graph compilation now directly uses `ArchitectGraph(checkpointer=memory_saver, store=memory_store).compiled_graph`.
*   **`tests/integration_tests/test_orchestrator.py` (UPDATED):**
    *   Tests updated to reflect the Orchestrator's new tool usage (e.g., `memorize` instead of `store_memory`, and direct agent tool calls like `code_reviewer` instead of generic `Delegate`).
*   **`tests/integration_tests/test_semantic_memory.py` (RENAMED from `tests/integration_tests/test_graph.py`, UPDATED):**
    *   Tests the `AgentTemplateGraph`'s semantic memory capabilities, including memory storage and dumping.
    *   **UPDATED**: Tests now explicitly enable memory usage (`use_memory=True`) in the `Configuration`.
    *   **UPDATED**: The `test_memory_dump` function no longer uses a temporary directory; instead, it expects the memory dump file to be created in the current working directory or its subdirectories.
    *   **UPDATED**: The instruction given to the agent for dumping memories has been adjusted to be more generic, no longer specifying a target directory.
*   **`tests/integration_tests/test_requirement_gatherer.py` (UPDATED):**
    *   The test setup now explicitly imports `Configuration` as `GathererConfig` from `requirement_gatherer.configuration`.
    *   An `agent_config = GathererConfig(use_human_ai=True)` is now passed to the `RequirementsGraph` constructor. **UPDATED**: The `test_requirement_gatherer_ends_with_summarize_tool_call` test now explicitly sets `human_ai_product` in the `GathererConfig` and changes the initial `test_input` content to `"Start!"`. A `recursion_limit: 100` has been added to the `config`. **UPDATED**: The `test_requirement_gatherer_ends_with_summarize_tool_call` test now uses `{"role": "human", "content": "Start!"}` as input. It also includes new assertions to verify tool call counts using `collections.Counter`: `human_feedback` is called 1-5 times, `memorize` is called at least as many times as `human_feedback`, and `set_project` is called exactly once. **UPDATED**: New assertions added to verify the correctness of the `memorize` tool by comparing the arguments passed to the tool with the content and context of the actually stored memories.
    *   The `client.aevaluate` call now uses `create_async_graph_caller_for_gatherer(graph)` instead of `create_async_graph_caller(graph)`.
    *   The `num_repetitions` for evaluation has been reduced from `4` to `1`.
    *   **NEW**: A new asynchronous test `test_requirement_gatherer_ends_with_summarize_tool_call` has been added. This test verifies that the `RequirementsGraph` successfully invokes the `summarize` tool, asserting that the second-to-last message in the graph's output is a `ToolMessage` with the name "summarize".
*   **`tests/graph_tests/graph_node/test_orchestrator.py` (UPDATED):**
    *   **UPDATED**: The `normalize_whitespace` helper function has been renamed to `_normalize_whitespace`.
    *   **NEW**: Added `test_tool_call_coder_with_full_task` asynchronous test. This test verifies that the Orchestrator correctly forwards the full, unsummarized task content (obtained via `read_task_planning`) to the `coder_new_pr` tool, ensuring no modification or summarization of the task.
    *   **NEW**: A new asynchronous test `test_does_not_call_tester_with_coder_details` has been added. This test verifies that the Orchestrator does not pass coding implementation details (like PR numbers or branch names) to the `tester` tool when delegating.
*   **NEW**: `tests/graph_tests/single_graph/test_code_reviewer.py`: New asynchronous tests verifying the Code Reviewer agent's tool invocation logic, including scenarios for no tool calls, listing files in a project directory, and reading source code files while ignoring non-code files like `README.md`.
*   **`tests/integration_tests/test_task_manager.py` (UPDATED):**
    *   The `call_model` function and `test_task_manager_with_project_path` now explicitly add a `Project` object to the state dictionary for testing, providing explicit project context during task manager operations.
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
*   **`tests/testing/__init__.py` (UPDATED):**
    *   A new helper function `create_async_graph_caller_for_gatherer` has been added. This function is specifically designed for the requirement gatherer evaluation, expecting the final output to be a `ToolMessage` with the name "summarize" and returning its content.
    *   **UPDATED**: Minor formatting changes.
*   **NEW**: `tests/testing/inputs.py`: New utility file providing `decode_base_message` and `decode_base_messages` functions to transform message dictionaries to `BaseMessage` objects.
*   **NEW**: `tests/testing/utils.py`: A new utility file providing helper functions for testing, including `get_list_diff` for comparing lists (e.g., tool calls) and `round_to` for rounding numbers. **NEW**: Added `get_tool_args_with_names` function to extract tool call arguments from messages. The `get_tool_messages_count` function has been removed.
*   **NEW**: `tests/unit_tests/architect.py`: New asynchronous tests verifying architecture creation workflows, including file generation for project structures. **UPDATED**: Enhanced unit tests with more detailed assertions to ensure correct tool usage (e.g., `recall`, `create_directory`, `memorize`, `create_file`, `list_files`, `summarize` tool call counts), memory storage, and file creation behavior. Specifically, it now verifies that the `memorize` tool is called with matching `content` and `context` arguments to the stored memories.
*   **NEW**: `tests/unit_tests/common/test_chain.py`: New unit tests added to verify the functionality of `common.chain.prechain` and `common.chain.skip_on_summary_and_tool_errors`, specifically testing error propagation and summary-based skipping in agent workflows. **UPDATED**: `AIMessage` construction in tests now explicitly uses `tool_calls` list.
*   **NEW**: `tests/unit_tests/common.py`: New comprehensive unit tests for `common.tools.read_file`, `common.tools.list_files`, `common.tools.create_directory`, and `common.tools.create_file`, ensuring correct functionality and error handling across various scenarios.
*   **NEW**: `tests/unit_tests/test_orchestrator.py`: New unit tests for Orchestrator tool calls, verifying correct tool delegation based on input messages (e.g., no tool call for "Hi", `requirements` for "build a website", `architect` after requirements are gathered).
*   (Other test files as previously described, or minor updates not impacting core logic)

## 7. Development Workflow & Tools (from `README.md` & `project_memories/PRD.md`) (UPDATED)

*   **`Makefile` (UPDATED):**
    *   Changed `demo` target to `demo-%` (e.g., `make demo-ai`, `make demo-human`) for explicit mode selection when running the demo orchestration script (`src/demo/orchestrate.py`).
*   **`README.md` (UPDATED):**
    *   Updated "Local Demo" instructions to use the new `make demo-ai` and `make demo-human` commands.
*   **CI/CD (GitHub Actions - `.github/workflows/`):**
    *   **UPDATED**: All jobs within `checks.yml`, `compile-check.yml`, and `graph-checks.yml` now use a refined `actions/checkout` configuration (`ref: ${{ github.event.pull_request.head.ref || github.ref }}` and `repository: ${{ github.event.pull_request.head.repo.full_name || github.repository }}`) to correctly checkout the code for pull requests originating from forks, ensuring CI runs on the correct branch and repository.
    *   `checks.yml` (UPDATED):
        *   Includes jobs for linting, type checking, unit tests, and integration tests.
        *   **New `smoke-test` job**:
            *   Runs on `ubuntu-latest`.
            *   Checks out the code.
            *   Creates an `.env` file with `GOOGLE_API_KEY=${{ secrets.GEMINI_API_KEY }}` at the project root.
            *   Installs `uv` and Python dependencies (`make deps`).
            *   Navigates to `tests/smoke/langgraph_dev`, installs Node.js dependencies (`npm i`), and runs the smoke test (`npm test`).
            *   Uploads `tests/smoke/langgraph_dev/langgraph-test-result.png` as an artifact with a 10-day retention period if the test runs (regardless of pass/fail).
        *   **UPDATED**: The `test_unit` job now includes `GOOGLE_API_KEY: ${{ secrets.GEMINI_API_KEY }}` in its environment variables.
    *   `compile-check.yml` (UPDATED): Ensures the LangGraph graphs can be compiled.
    *   `graph-checks.yml` (UPDATED): Ensures the LangGraph graphs can be compiled and their structure is valid.
    *   `run_common_tests.yml` (NEW): A new workflow to run common unit tests on `push` to `main`, `pull_request` to `main`, and `workflow_dispatch`.
    *   `update_project_memory.yml`: (As previously described)
*   **Project Maintenance Scripts (UPDATED):**
    *   The `generate_project_memory.sh`, `update_project_memory_from_pr.sh`, and `update_project_readmes.sh` scripts now use the `gemini-2.5-flash-preview-05-20` model for their API calls.
*   **Dependency Management (`pyproject.toml` - UPDATED):**
    *   Dependency version specifiers have been changed from `>=` (greater than or equal to) to `~=` (compatible release, e.g., `~=1.2.3` implies `>=1.2.3` and `<1.3.0`). This change restricts updates to patch versions for the specified minor versions of main and development dependencies, aiming to enhance build stability.
    *   The `[tool.setuptools]` `packages` list within `pyproject.toml` has also been reformatted for improved readability. **UPDATED**: The `packages` list now includes `scenarios`.
*   **LangSmith Tracing (NEW aspect for demo):**
    *   The demo script (`src/demo/orchestrate.py`) now integrates LangSmith tracing, providing a trace URL for each run. This includes user identification and run metadata. **UPDATED**: Scenario runs (e.g., `tests/scenarios/fibonacci/run.py`) now also explicitly set `run_name` and `run_id` in `RunnableConfig` and use `wait_for_all_tracers()` for complete tracing. **NEW**: `src/common/__init__.py` now includes `BaseMessageEncoder` for JSON serialization of `BaseMessage`, `RunTree`, `BaseModel`, `EvaluationResult`, and `Client` objects, supporting LangSmith tracing.
*   **New/Updated Utility Files:**
    *   `src/common/chain.py` (NEW): Defines `prechain` decorator and `skip_on_summary_and_tool_errors` function for advanced control flow and error handling in agent chains.
    *   `src/common/state.py` (NEW): Defines the `Project` dataclass for managing project ID, name, and path. **UPDATED**: Now also defines `AgentState` as a base dataclass for all agent states, including `messages`, `summary`, and `error` fields.
    *   `src/common/utils/__init__.py` (UPDATED): Includes a new `format_message` utility function for printing actor-labeled messages.
    *   **NEW**: `src/common/utils/github.py`: Provides centralized utility functions for GitHub App authentication and API client retrieval.
        *   `app_get_integration()`: Authenticates and returns a `GithubIntegration` object using `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, and `GITHUB_REPOSITORY` environment variables. It can read the private key from a file path or directly from the environment variable.
        *   `app_get_installation()`: Retrieves the GitHub App installation for the repository.
        *   `app_get_client_from_credentials()`: A convenience function that combines the above to return an authenticated `github.Github` client instance.
    *   **UPDATED**: `src/common/logging.py` (NEW): Provides a centralized `get_logger` utility for consistent log formatting and dynamic log level control via the `LOG_LEVEL` environment variable.
*   **Project Directory:** A new `projects/` directory has been added to store project-specific files. **NEW**: A `scenario_runs/` directory will be created under `tests/scenarios/fibonacci/` to store scenario run outputs.
*   `.gitignore` (UPDATED): Now excludes all files and directories under `projects/`. **UPDATED**: Also excludes files with the `.pem` extension. **UPDATED**: Also excludes `scenario_runs`.
*   **Demo Configuration:** The demo script (`src/demo/orchestrate.py`) now configures `task_manager_agent` with `use_stub=False` and `coder_new_pr_agent`, `coder_change_request_agent` with `use_stub=True`. **UPDATED**: The demo script now configures the `coder_new_pr_agent` with `use_stub=False` (previously `True`), the `tester_agent` with `use_stub=False` and passes `TesterConfiguration()`, and the `reviewer_agent` with `use_stub=False`.
*   **GitHub Branch Management Scripts (NEW):**
    *   `tests/scenarios/setup_github.py`: A utility script to create specified base branches in a GitHub repository if they do not already exist, using GitHub App authentication. **UPDATED**: Now utilizes the centralized GitHub App authentication utility (`common.utils.github.app_get_client_from_credentials()`) instead of implementing authentication logic directly.
    *   `tests/scenarios/cleanup_github.py`: A utility script to delete branches in a GitHub repository that are not part of a predefined list of base branches, using GitHub App authentication. **UPDATED**: Now utilizes the centralized GitHub App authentication utility (`common.utils.github.app_get_client_from_credentials()`) instead of implementing authentication logic directly.
*   **Environment Variables (UPDATED):**
    *   `.env.example`: Now includes `LOG_LEVEL=INFO` to configure the default logging level.
    *   **NEW**: `GITHUB_APP_ID`: Required for GitHub App authentication.
    *   **NEW**: `GITHUB_APP_PRIVATE_KEY`: Required for GitHub App authentication (can be a file path or the key content).
    *   **NEW**: `GITHUB_REPOSITORY`: Required for GitHub App authentication (specifies the target repository).
*   (Other workflow aspects like `pytest.ini` setup as previously described, or minor updates not impacting core logic)

## 8. Overall Project Structure Summary

```
ai-nexus/
├── .cursor/
│   └── rules/
│       └── read-project-memories.mdc
├── .env.example                   # UPDATED: Added LOG_LEVEL
├── .gitignore                    # UPDATED: Added projects/*, *.pem, scenario_runs
├── .vscode/
│   └── launch.json
├── .github/
│   └── workflows/
│       ├── checks.yml            # UPDATED: Added smoke-test job; test_unit job now includes GOOGLE_API_KEY env var.
│       ├── compile-check.yml
│       ├── graph-checks.yml      # UPDATED: The `actions/checkout` step has been updated to support pull requests from forks.
│       ├── run_common_tests.yml  # NEW: Workflow to run common unit tests
│       └── update_project_memory.yml
├── Makefile                      # UPDATED: Changed demo target to demo-% (e.g., demo-ai, demo-human).
├── README.md                     # UPDATED: Local demo instructions updated.
├── agent_memories/
│   └── grumpy/
├── langgraph.json                # UPDATED: `tester` graph path changed to `./src/tester/lg_server.py:graph`. ADDED: `code_reviewer_local` entry.
├── projects/                     # NEW: Directory for project-specific files
│   └── .gitkeep                  # NEW
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
│   │   ├── graph.py              # UPDATED: Added common.tools.summarize, common.tools.create_directory, common.tools.create_file, common.tools.list_files, common.tools.read_file to the agent's toolset; call_model uses state.project.path and prints formatted messages. UPDATED: `_create_call_model` is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
│   │   ├── prompts.py            # UPDATED: System prompt includes new "Summarize" step and use of summarize tool; uses {project_dir}. UPDATED: Prompt's description of core files and their flow (Mermaid, numbered list) updated to include projectRequirements.md as an intermediary and adjusted numbering. UPDATED: Prompt now includes instruction to ensure {project_dir} exists and create it if necessary, using create_directory, and clarifies list_files and create_file usage. UPDATED: Prompt for projectbrief.md now instructs to add hobby sentence; summarize step requires clarifying if hobby project. UPDATED: The prompt for the `memorize` tool now explicitly states to "Pass the `content` to be memorized and the `context` within which it was stated."
│   │   ├── state.py              # UPDATED: summary field added; project field added. UPDATED: `error` field added.
│   │   └── tools.py              # UPDATED: Removed 'summarize', 'read_file', 'create_file', 'list_files' tools (now in common). **FIXED**: `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
│   ├── code_reviewer/
│   │   ├── __init__.py           # UPDATED: Added `graph_local` to `__all__`.
│   │   ├── graph.py              # UPDATED: `DiffHunkFeedback` and `DiffFeedback` classes removed. `CodeReviewerInstanceConfig` updated (renamed `github_tools` to `github_tools_filter`, added `other_tools`). NEW: `local_code_reviewer_config()` function. NEW: `CodeReviewerGraph` class (subclasses `AgentGraph`). `CallModel` now formats prompt with `project_path` and returns `project` in state. `graph_builder` renamed to `_graph_builder`.
│   │   ├── lg_server.py          # UPDATED: Added `graph_local` and included in `__all__`.
│   │   ├── prompts.py            # UPDATED: Added `LOCAL_REVIEW_PROMPT`.
│   │   ├── state.py              # UPDATED: summary field added. UPDATED: `error` field added. ADDED: `project` field.
│   │   └── system_prompt.md
│   ├── coder/
│   │   ├── __init__.py
│   │   ├── graph.py              # UPDATED: Minor state access change (state.messages). UPDATED: `coder_new_pr_config` and `coder_change_request_config` now include `get_latest_pr_workflow_run` tool. UPDATED: `CallModel` class removed, `_create_call_model` function now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
│   │   ├── lg_server.py
│   │   ├── mocks.py
│   │   ├── prompts.py            # UPDATED: NEW_PR_SYSTEM_PROMPT updated to use "base branch". UPDATED: NEW_PR_SYSTEM_PROMPT now includes instruction to use actual branch name from `get_branch_name` tool.
│   │   ├── state.py              # UPDATED: Now a dataclass, summary field added. UPDATED: `error` field added.
│   │   ├── tools.py
│   │   └── README.md
│   ├── common/
│   │   ├── __init__.py           # UPDATED: Added BaseMessageEncoder for JSON serialization.
│   │   ├── chain.py              # NEW: Defines prechain and skip_on_summary_and_tool_errors for control flow.
│   │   ├── components/
│   │   │   ├── github_mocks.py   # UPDATED: `maybe_mock_github` function now accepts an optional `base_branch` argument. Added mocks for `create_issue_comment` and `get_latest_pr_workflow_run`. Updated existing mocks to return empty string instead of raising NotImplementedError.
│   │   │   ├── github_tools.py   # UPDATED: Added `create_issue_comment` and `get_latest_pr_workflow_run` tools. Modified `_run` methods of `CreatePullRequestReviewComment`, `GetPullRequestDiff`, `GetPullRequestHeadBranch` to call their `_arun` counterparts.
│   │   │   └── memory.py
│   │   ├── configuration.py
│   │   ├── graph.py              # UPDATED: Added name, checkpointer, store properties.
│   │   ├── logging.py            # NEW: Logging utilities
│   │   ├── state.py              # NEW: Defines Project dataclass. UPDATED: Now also defines `AgentState` base dataclass.
│   │   ├── tools/                # ADDED
│   │   │   ├── __init__.py       # UPDATED: Imports create_directory, create_file, list_files, read_file, summarize. `create_read_task_planning_tool` removed.
│   │   │   ├── create_directory.py # NEW: Centralized create_directory tool
│   │   │   ├── create_file.py    # NEW: Centralized create_file tool
│   │   │   ├── list_files.py     # NEW: Centralized list_files tool (moved from src/task_manager/tools.py)
│   │   │   ├── read_file.py      # NEW: Centralized read_file tool
│   │   │   ├── read_task_planning.py # DELETED
│   │   │   └── summarize.py      # ADDED: Centralized summarize tool
│   │   ├── utils/
│   │   │   ├── __init__.py       # UPDATED: Added format_message function
│   │   │   └── github.py         # NEW: Centralized GitHub App authentication utilities
│   ├── demo/
│   │   └── orchestrate.py        # MOVED & RENAMED from src/orchestrator/test.py; UPDATED to use create_runnable_config and compiled_graph.ainvoke. UPDATED: Imports TaskManagerAgentConfig, TaskManagerConfiguration, TesterAgentConfig, TesterConfiguration; configures task_manager_agent and tester_agent; prints task_manager tool calls. UPDATED: Integrates LangSmith tracing (prints trace URL, uses @traceable). The demo script's configuration for the Orchestrator now sets `use_stub=False` by default for the Requirements, Architect, Coder New PR, and Coder Change Request agents. The Task Manager agent remains configured with `use_stub=True` in the demo. UPDATED: `task_manager_agent` `use_stub` changed to `False`, `coder_new_pr_agent` `use_stub` changed to `False` (previously `True`), and `coder_change_request_agent` `use_stub` changed to `True`. `tester_agent` `use_stub` changed to `False`. UPDATED: `reviewer_agent` `use_stub` changed to `False`.
│   ├── grumpy/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: Subclasses AgentConfiguration. Defines OrchestratorConfiguration including fields for sub-agent configs (e.g., ArchitectAgentConfig, TaskManagerAgentConfig (NEW), TesterAgentConfig (NEW), SubAgentConfig for coders, reviewer). SubAgentConfig and its subclasses now include `stub_messages`. Coder agent configs now default to specific `MessageWheel` instances. Added `github_base_branch` field. NEW: `CodeReviewerAgentConfig` dataclass. `reviewer_agent` field type changed to `CodeReviewerAgentConfig`. `default_factory` for `coder_new_pr_agent`, `coder_change_request_agent`, `reviewer_agent` fixed.
│   │   ├── graph.py              # UPDATED: Major refactor to use ToolNode, direct agent tool calls (requirements, architect, task_manager (NEW), coder_new_pr, coder_change_request, tester, code_reviewer), memorize, and common.tools.summarize. Removed Delegate pattern. Sub-agent stubs now initialized with `stub_messages`. `maybe_mock_github` now called with `base_branch` from agent config. `TesterAgentGraph` is now initialized with `github_tools`. UPDATED: The `get_next_task` tool is now provided by `tools.create_read_task_planning_tool`, initialized with `self._agent_config.task_manager_agent.use_stub`. UPDATED: `_create_orchestrator` is now decorated with `@prechain(skip_on_summary_and_tool_errors())`. `_create_orchestrate_condition` now checks for `AIMessage` and `state.error`. UPDATED: `code_reviewer_graph` initialization now conditionally uses `CodeReviewerStub` if `self._agent_config.reviewer_agent.use_stub` is `True`, otherwise it uses `code_reviewer.graph.CodeReviewerGraph` with `code_reviewer.graph.github_code_reviewer_config()`.
│   │   ├── memory/
│   │   │   ├── absolute.md       # UPDATED: Reflects new tools and workflow. UPDATED: `summarize` tool call instruction changed to "IF no tasks are pending". NEW: Added "You MUST NEVER ask clarifying questions.", "You MUST respond with 'I'm not sure what to do', if it is unclear which tool to delegate to.", "You MUST reply to pleasantries like 'Hi', 'Thank you', and 'Bye' in a polite manner.".
│   │   │   ├── process.md        # UPDATED: Reflects new tools and workflow, includes instruction to use `get_next_task`. UPDATED: `summarize` tool call instruction changed to "IF nothing is pending". **UPDATED**: Added "IMPORTANT when sending a task copy the task received in `get_next_task` AS IS without changing or summarizing it".
│   │   │   ├── project_states.md # UPDATED: Reflects new tools, workflow (incl. task creation, pick a task), includes Mermaid diagram with "Get task" step. UPDATED: Reflects new workflow for testing (writing e2e tests before review, loop back to code & implement on review fail).
│   │   │   ├── team.md           # UPDATED: Reflects new tools (direct calls, memorize, summarize, get_next_task), includes Task Manager agent, clarifies Coder's input from Task Manager and Orchestrator's use of `get_next_task`. UPDATED: Requirements Gatherer instructions updated. UPDATED: Reflects Tester's updated role (e2e tests from requirements/architecture, never send coding implementation details).
│   │   ├── prompts.py            # UPDATED: Static ORCHESTRATOR_SYSTEM_PROMPT string removed, get_prompt() loads from memory files. UPDATED: Prompt logic changed to "If the user has provided an instruction...".
│   │   ├── state.py              # UPDATED: summary field added; project field added. UPDATED: `error` field added.
│   │   ├── stubs/
│   │   │   └── __init__.py       # UPDATED: StubGraph base class modified (returns summary, END edge, uses `_stub_messages`). MessageWheel class moved to top-level. All specific *Stub classes now accept and pass `stub_messages` to super(). Predefined `model_*_messages` instances added. RequirementsGathererStub, ArchitectStub, CoderNewPRStub, CoderChangeRequestStub updated. New TesterStub, CodeReviewerStub, TaskManagerStub (NEW) classes. Old simple stub functions removed. Imports TaskManagerState. RequirementsGathererStub now returns project_name and `project` object. UPDATED: `model_code_reviewer_messages` simplified.
│   │   ├── tools.py              # UPDATED: Delegate tool removed. store_memory effectively replaced by memorize. New tool factories (create_requirements_tool, etc.) for direct agent invocation, including create_task_manager_tool (NEW). `coder_new_pr` and `coder_change_request` tools now return `result["messages"][-1].content`. Removed 'summarize' tool (now in common). Imports TaskManagerGraph, TaskManagerState. Requirements, Architect, and Task Manager tools now update the project state. Tester tool now passes project state and github_tools. UPDATED: The `create_read_task_planning_tool` function (for the `get_next_task` tool) has been moved here from `src/common/tools/read_task_planning.py`. It now takes the Orchestrator's state as input and raises errors instead of returning error strings. UPDATED: All sub-agent invocation tools now return `Command` with `ToolMessage` including `status` and `error` content. UPDATED: `create_code_reviewer_tool` now passes `project` to `CodeReviewerState` and its `code_reviewer_graph` parameter type hint is `CodeReviewerGraph`.
│   │   └── utils.py              # ADDED: Contains utility functions like split_model_and_provider.
│   ├── requirement_gatherer/
│   │   ├── __init__.py
│   │   ├── configuration.py      # UPDATED: `use_human_ai` defaults to `True`. Added `human_ai_product: Optional[str]` field and `__post_init__` logic to set default `human_ai_product` or raise error.
│   │   ├── graph.py              # UPDATED: Renamed to RequirementsGraph, uses AgentConfiguration, new AgentGraph init; helpers receive agent_config; memorize tool now created via create_memorize_tool(self._agent_config); minor conditional logic update in _create_gather_requirements; uses common.tools.summarize. Added set_project tool. UPDATED: `_create_call_model` is now decorated with `@prechain(skip_on_summary_and_tool_errors())`. `_create_gather_requirements` now checks for `AIMessage` and `state.error`.
│   │   ├── prompts.py            # UPDATED: Prompt includes instruction for set_project tool. UPDATED: Prompt text refined (e.g., "smart and curious"), new IMPORTANT rules added (e.g., limit questions for HOBBY projects), rule numbering adjusted, Mermaid flowchart and Core File table simplified (removed stakeholders.md, constraints.md), checklist sections removed/renamed, functional requirements streamlined. NEW: `HUMAN_AI_PRODUCT` constant added.
│   │   ├── state.py              # UPDATED: summary field added; project field added. UPDATED: `error` field added.
│   │   └── tools.py              # UPDATED: Removed 'summarize' tool (now in common). Added set_project tool. UPDATED: `human_feedback` tool's prompt template now includes a `<Product>` section with a `{product}` placeholder, and its `ai_user.ainvoke` call now passes `agent_config.human_ai_product` to format this section, ensuring the AI's responses are guided by the specified product context. New rubric, instructions, and reminder lines have been added to reinforce adherence to the product definition. **FIXED**: `memorize` tool now correctly accesses `user_id` from `config["configurable"]["user_id"]`.
│   ├── task_manager/
│   │   ├── configuration.py      # UPDATED: Added use_stub, use_human_ai fields; uses prompts.SYSTEM_PROMPT.
│   │   ├── graph.py              # UPDATED: call_model uses project_name and project_path in prompt and prints formatted messages. UPDATED: Added common.tools.summarize, common.tools.create_directory, common.tools.create_file, common.tools.list_files, common.tools.read_file to the agent's toolset. UPDATED: `call_model` now handles `use_stub` for project name/path and extracts from `state.project`. UPDATED: `_create_call_model` is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
│   │   ├── prompts.py            # UPDATED: System prompt significantly updated with stricter task splitting, mandatory testing/CI/CD requirements, expanded task metadata, and reinforced roadmap/sequencing rules. Uses {project_name} and {project_path}. UPDATED: Prompt's list of required files, file descriptions, task metadata schema, and context extraction guidelines updated to reflect techContext.md -> techPatterns.md, featuresContext.md -> codingContext.md, and removal of securityContext.md. UPDATED: Prompt now explicitly states input document location and project name, and includes a mandatory instruction to write a summary and call the summarize tool. The prompt now states it will verify "all seven required files". NEW: Added "Path Security Constraints" and "HOBBY MODE" sections. Updated `description` field format and introduced `tasks.json` schema. Updated "Execution Process" and "Technical Guardrails" sections for HOBBY mode and path security.
│   │   └── state.py              # UPDATED: summary field added; project field added. UPDATED: `error` field added.
│   └── tester/
│       ├── __init__.py           # UPDATED: `graph` import changed from `tester.graph` to `tester.lg_server`.
│       ├── configuration.py
│       ├── deprecated/
│       │   ├── deprecated-test-agent-system-prompt.md
│       │   └── test-agent-analyze-requirements-workflow-stage.md
│       ├── graph.py              # UPDATED: `TesterAgentGraph` constructor now accepts `github_tools`. `create_builder` now includes `filtered_github_tools` and removes `common.tools.create_directory`, `common.tools.create_file`, `common.tools.list_files`, `common.tools.read_file`. New helper functions `get_tester_github_tools` and `filter_github_tools` added. `call_model` uses project_path in prompt. Direct `graph` export removed. UPDATED: `_create_call_model` is now decorated with `@prechain(skip_on_summary_and_tool_errors())`.
│       ├── lg_server.py          # NEW: File for LangGraph server setup for Tester agent, initializes and passes GitHub tools to TesterAgentGraph.
│       ├── prompts.py            # UPDATED: SYSTEM_PROMPT includes {project_path}.
│       ├── state.py              # UPDATED: New WorkflowStage enum, State includes workflow_stage, summary field added, project field added. UPDATED: `error` field added.
│       ├── test-agent-system-prompt.md # UPDATED: Content significantly changed with absolute prohibitions, file restrictions, critical assumption rules, focus on e2e/acceptance testing, updated workflow (including branch creation, mandatory validation, GitHub uploads, PR creation), and stricter key rules.
│       ├── test-agent-testing-workflow-stage.md
│       └── tools.py
└── tests/
    ├── datasets/
    │   ├── __init__.py           # NEW: Placeholder file.
    │   ├── coder_dataset.py
    │   ├── orchestrator_dataset.py # NEW: New dataset for orchestrator tool usage evaluation.
    │   ├── requirement_gatherer_dataset.py # UPDATED: Dataset name, FIRST_MESSAGE, input/output content updated. UPDATED: Minor formatting in outputs.
    │   └── task_manager_dataset.py
    ├── evaluations/
    │   ├── __init__.py           # NEW: Placeholder file.
    │   └── orchestrator/         # NEW: Directory for orchestrator evaluations.
    │       ├── __init__.py       # NEW: Placeholder file.
    │       └── test_tools.py     # NEW: New asynchronous test for orchestrator tool usage correctness.
    ├── graph_tests/
    │   ├── graph_node/
    │   │   └── test_orchestrator.py # UPDATED: `normalize_whitespace` helper function renamed to `_normalize_whitespace`. **NEW**: Added `test_tool_call_coder_with_full_task` to verify Orchestrator forwards full task content to Coder. **NEW**: Added `test_does_not_call_tester_with_coder_details` to verify Orchestrator does not send coding implementation details to Tester.
    │   └── single_graph/
    │       └── test_code_reviewer.py # NEW: New asynchronous tests verifying the Code Reviewer agent's tool invocation logic, including scenarios for no tool calls, listing files in a project directory, and reading source code files while ignoring non-code files like `README.md`.
    ├── integration_tests/
    │   ├── test_architect_agent.py # UPDATED: Graph compilation now uses `ArchitectGraph(...).compiled_graph`.
    │   ├── test_coder.py
    │   ├── eval_coder.py
    │   ├── test_graph.py
    │   ├── test_grumpy_agent.py
    │   ├── test_orchestrator.py    # UPDATED: Tests reflect new Orchestrator tool usage (e.g., memorize, direct agent calls like code_reviewer).
    │   ├── test_semantic_memory.py # RENAMED from `tests/integration_tests/test_graph.py`, UPDATED: Tests the `AgentTemplateGraph`'s semantic memory capabilities, including memory storage and dumping. **UPDATED**: Tests now explicitly enable memory usage (`use_memory=True`) in the `Configuration`. **UPDATED**: The `test_memory_dump` function no longer uses a temporary directory; instead, it expects the memory dump file to be created in the current working directory or its subdirectories. **UPDATED**: The instruction given to the agent for dumping memories has been adjusted to be more generic, no longer specifying a target directory.
    │   ├── test_requirement_gatherer.py # UPDATED: Uses create_async_graph_caller_for_gatherer, passes agent_config to RequirementsGraph, num_repetitions reduced. UPDATED: `test_requirement_gatherer_ends_with_summarize_tool_call` now explicitly sets `human_ai_product` in config and changes initial input. NEW: Added test_requirement_gatherer_ends_with_summarize_tool_call to verify summarize tool call. UPDATED: `test_requirement_gatherer_ends_with_summarize_tool_call` now includes assertions for `human_feedback` (1-5 calls), `memorize` (at least as many as `human_feedback`), and `set_project` (exactly 1 call), and uses `collections.Counter`. **UPDATED**: New assertions added to verify the correctness of the `memorize` tool by comparing the arguments passed to the tool with the content and context of the actually stored memories.
    │   ├── test_task_manager.py    # UPDATED: Tests now provide explicit project context during task manager operations.
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
    │   ├── cleanup_github.py       # UPDATED: Now uses `common.utils.github` for authentication.
    │   ├── fibonacci/              # NEW: Directory for fibonacci scenario
    │   │   ├── __init__.py         # NEW: Defines BASE_BRANCH for fibonacci scenario.
    │   │   ├── eval.py             # NEW: Evaluation script for Fibonacci scenario runs.
    │   │   ├── run.py              # RENAMED from tests/scenarios/fibonacci.py; UPDATED: Adds concept of a scenario "run" with structured metadata (run_name, run_id, pr_number, branch), extracts PR details using LLM, and persists run results to JSON in `scenario_runs/` directory. RunnableConfig now includes run_name and run_id. Stub messages and initial prompt updated for Rust Fibonacci library. Now evaluated by `eval.py`. **UPDATED**: The `requirements_agent`, `architect_agent`, `task_manager_agent`, `coder_new_pr_agent`, and `coder_change_request_agent` are now configured with `use_stub=False`. Specifically, the `requirements_agent` now includes a `config` with `use_human_ai=True` and a `human_ai_product` description for a hobby Rust Fibonacci project. The `reviewer_agent` is now explicitly typed as `CodeReviewerAgentConfig` and configured with `use_stub=False`. The `tester_agent` is now explicitly typed as `TesterAgentConfig` and configured with `use_stub=False`.
    │   │   ├── scenario_runs/      # NEW: Directory for scenario run outputs (implicitly created by run.py)
    │   │   └── tests/
    │   │       └── scenario_eval_tests.rs # NEW: Rust unit tests for Fibonacci implementation.
    │   ├── stack/                  # NEW: Directory for stack scenario
    │   │   ├── __init__.py         # NEW: Defines BASE_BRANCH for stack scenario.
    │   │   ├── run.py              # NEW: New E2E test scenario for building a Rust stack library, including Orchestrator configuration with stubbed agents, real Coder agent, interrupt handling, LLM-based PR info extraction, and JSON persistence of run results. **UPDATED**: The `reviewer_agent` is now explicitly typed as `CodeReviewerAgentConfig`. The `tester_agent` is now explicitly typed as `TesterAgentConfig`.
    │   │   └── scenario_runs/      # NEW: Directory for scenario run outputs (implicitly created by run.py)
    │   └── setup_github.py         # UPDATED: Now uses `common.utils.github` for authentication.
    ├── smoke/                      # ADDED
    │   └── langgraph_dev/          # ADDED
    │       ├── .gitignore          # ADDED
    │       ├── package.json        # ADDED
    │       ├── src/                # ADDED
    │       │   └── index.ts        # ADDED
    │       └── tsconfig.json       # ADDED
    ├── testing/
    │   ├── __init__.py             # UPDATED: Added create_async_graph_caller_for_gatherer helper function. UPDATED: Minor formatting.
    │   ├── evaluators.py
    │   ├── formatter.py
    │   ├── inputs.py               # NEW: New utility file for decoding message dictionaries.
    │   └── utils.py                # UPDATED: New utility file providing helper functions for testing, including `get_list_diff` and `round_to`. **UPDATED**: Added `get_tool_args_with_names` function to extract tool call arguments from messages. `get_tool_messages_count` removed.
    ├── unit_tests/
    │   ├── architect.py            # NEW: New asynchronous tests verifying architecture creation workflows, including file generation for project structures. **UPDATED**: Enhanced unit tests with more detailed assertions to ensure correct tool usage (e.g., `recall`, `create_directory`, `memorize`, `create_file`, `list_files`, `summarize` tool call counts), memory storage, and file creation behavior. Specifically, it now verifies that the `memorize` tool is called with matching `content` and `context` arguments to the stored memories.
    │   ├── common/
    │   │   └── test_chain.py       # NEW: Unit tests for common.chain (prechain, skip_on_summary_and_tool_errors). UPDATED: AIMessage construction in tests now explicitly uses `tool_calls` list.
    │   ├── common.py               # NEW: New comprehensive unit tests for `common.tools.read_file`, `common.tools.list_files`, `common.tools.create_directory`, and `common.tools.create_file`.
    │   ├── test_configuration.py
    │   └── test_orchestrator.py    # NEW: New unit tests for Orchestrator tool calls.
```
