# Project Planning: Task Timer CLI

## Team and Capacity

-   **Team Size**: 2 engineers/agents
-   **Hours Per Engineer Per Week**: 40 hours
-   **Total Weekly Capacity**: 80 hours

With a team of 2 engineers, we can parallelize work across two main streams, allowing tasks with no dependencies on each other to be worked on concurrently by different engineers. However, tasks assigned to the same engineer must be completed sequentially. Dependencies between tasks, regardless of assignee, must be respected, meaning a task cannot start until all its prerequisites are finished.

## Sprint Plan

Each sprint is planned for a duration of 1 week, with a capacity of 80 hours. Tasks are assigned based on milestone priority and dependencies, filling sprint capacity by pulling tasks from the next milestone if the current one's tasks are insufficient.

### Sprint 1: Core Timer Functionality (Milestone 1)

-   **Focus**: Implementing the fundamental timer start, status, and stop commands, including basic UI elements and notifications.
-   **Capacity**: 80 hours
-   **Tasks**:
    -   S01-T01: Setup Rust Project (8 hrs) - Engineer 1
    -   S01-T02: Implement Start Command Logic (10 hrs) - Engineer 2
    -   S01-T03: Add Progress Bar to Timer (8 hrs) - Engineer 1
    -   S01-T04: Implement Desktop Notifications (8 hrs) - Engineer 2
    -   S01-T05: Add Configurable Sound Alerts (8 hrs) - Engineer 1
    -   S01-T06: Implement Status Command (8 hrs) - Engineer 2
    -   S01-T07: Implement Stop Command Logic (8 hrs) - Engineer 1
    -   S01-T08: Add Stop Reason Tracking (6 hrs) - Engineer 2
    -   S01-T09: Implement Session Notes (6 hrs) - Engineer 1
    -   S01-T10: Test Timer Core Logic (10 hrs) - Engineer 2
-   **Sprint Velocity**: 80 hours

### Sprint 2: Session Management (Milestone 2)

-   **Focus**: Setting up session data storage and implementing pause/resume functionality.
-   **Capacity**: 80 hours
-   **Tasks**:
    -   S02-T01: Setup Session Storage (SQLite) (10 hrs) - Engineer 1
    -   S02-T02: Implement Session Data Structure (8 hrs) - Engineer 2
    -   S02-T04: Implement Pause Command Logic (8 hrs) - Engineer 2
    -   S02-T09: Implement Session Tags and Categories (8 hrs) - Engineer 1
    -   S02-T05: Implement Resume Command Logic (8 hrs) - Engineer 1
    -   S02-T06: Add Auto-Pause Detection (12 hrs) - Engineer 2
    -   S02-T07: Implement Maximum Pause Duration (8 hrs) - Engineer 1
    -   S02-T10: Test Session Management (12 hrs) - Engineer 2
    -   S02-T03: Save Session Data to DB (10 hrs) - Engineer 1
    -   S02-T08: Add Pause Reason Tracking (6 hrs) - Engineer 2
-   **Sprint Velocity**: 90 hours (This indicates potential spillover into the next sprint or need for scope adjustment/efficiency gain)

### Sprint 3: Configuration and Customization (Milestone 3)

-   **Focus**: Implementing configuration loading and custom timer settings, along with basic clear command functionality.
-   **Capacity**: 80 hours
-   **Tasks**:
    -   S03-T01: Setup Configuration Management (8 hrs) - Engineer 1
    -   S03-T06: Implement Clear Command Basic Logic (6 hrs) - Engineer 2
    -   S03-T05: Implement Per-Project Configuration (8 hrs) - Engineer 1
    -   S03-T07: Add Selective Clearing (8 hrs) - Engineer 2
    -   S03-T04: Implement Custom Break Schedules (8 hrs) - Engineer 1
    -   S03-T08: Implement Data Export Before Clearing (8 hrs) - Engineer 2
    -   S03-T03: Implement Pomodoro Variations (8 hrs) - Engineer 1
    -   S03-T02: Implement Custom Session Durations (8 hrs) - Engineer 2
    -   S03-T09: Implement Archive Functionality (6 hrs) - Engineer 1
-   **Sprint Velocity**: 68 hours (Remaining capacity will be used for buffer or pulled tasks if any fit dependencies)

### Sprint 4: Statistics and Insights (Milestone 4)

-   **Focus**: Implementing basic statistics reporting and data export capabilities.
-   **Capacity**: 80 hours
-   **Tasks**:
    -   S04-T01: Implement Stats Command Basic Structure (8 hrs) - Engineer 2
    -   S04-T06: Implement Report Generation Command (6 hrs) - Engineer 2
    -   S04-T02: Calculate Daily/Weekly/Monthly Summaries (8 hrs) - Engineer 1
    -   S04-T07: Implement Report Export (CSV/JSON) (8 hrs) - Engineer 2
    -   S04-T04: Analyze Productive Time Periods (6 hrs) - Engineer 1
    -   S04-T08: Implement Customizable Report Templates (8 hrs) - Engineer 2
    -   S04-T03: Calculate Success Rate (6 hrs) - Engineer 1
    -   S04-T05: Analyze Common Interruption Patterns (6 hrs) - Engineer 2
    -   S05-T01: Update DB Schema for Tasks (8 hrs) - Engineer 1 (Pulled from M5)
    -   S05-T02: Implement Task Creation Command (8 hrs) - Engineer 2 (Pulled from M5)
-   **Sprint Velocity**: 74 hours

### Sprint 5: Task Integration (Milestone 5)

-   **Focus**: Implementing core task management features and linking sessions to tasks.
-   **Capacity**: 80 hours
-   **Tasks**:
    -   S04-T09: Implement Burndown Charts Logic (6 hrs) - Engineer 2 (Remaining from M4)
    -   S05-T03: Implement Task Editing Command (8 hrs) - Engineer 1
    -   S05-T04: Implement Task Deletion Command (8 hrs) - Engineer 2
    -   S05-T05: Associate Sessions with Tasks (8 hrs) - Engineer 1
    -   S05-T06: Implement Task Priorities and Deadlines (8 hrs) - Engineer 2
    -   S05-T07: Implement Task Scheduling Command (8 hrs) - Engineer 1
    -   S05-T09: Implement Task Dependencies Logic (8 hrs) - Engineer 2
    -   S05-T08: Implement Estimated Pomodoros Tracking (6 hrs) - Engineer 2
    -   S05-T10: Implement Task Listing/Filtering (12 hrs) - Engineer 1
    -   S06-T01: Setup Git Integration Library (8 hrs) - Engineer 1 (Pulled from M6)
-   **Sprint Velocity**: 80 hours

### Sprint 6: External Integration (Milestone 6 - Part 1)

-   **Focus**: Setting up foundational external integration components, including feature flags and secure storage.
-   **Capacity**: 80 hours
-   **Tasks**:
    -   S06-T14: Add Feature Flags for Integrations (8 hrs) - Engineer 1
    -   S06-T09: Setup Basic RESTful API Server (8 hrs) - Engineer 2
    -   S06-T05: Setup Calendar Integration Libraries (8 hrs) - Engineer 1
    -   S06-T10: Implement API Endpoint for Status (6 hrs) - Engineer 2
    -   S06-T13: Implement Secure Credential Storage (8 hrs) - Engineer 1
    -   S06-T15: Implement Graceful Network Failure Handling (8 hrs) - Engineer 2
    -   S06-T06: Implement Google Calendar Auth Flow (8 hrs) - Engineer 1
    -   S06-T11: Implement API Endpoint for Session History (8 hrs) - Engineer 1
-   **Sprint Velocity**: 62 hours

### Sprint 7: External Integration (Milestone 6 - Part 2) & Project Completion (Milestone 9)

-   **Focus**: Completing external integrations and finalizing the project with testing, documentation, and polish.
-   **Capacity**: 80 hours
-   **Tasks**:
    -   S06-T02: Implement Auto-Commit Messages (6 hrs) - Engineer 1
    -   S06-T03: Implement Branch-Specific Time Tracking (8 hrs) - Engineer 1
    -   S06-T04: Implement PR/Issue Time Logging (6 hrs) - Engineer 1
    -   S06-T08: Block Calendar During Sessions (6 hrs) - Engineer 2
    -   S06-T12: Implement Webhook Support (6 hrs) - Engineer 2
    -   S06-T07: Sync Sessions with Google Calendar (8 hrs) - Engineer 2
    -   S09-T01: Cross-Platform Testing (12 hrs) - Engineer 2
    -   S09-T02: Write User Documentation (8 hrs) - Engineer 1
    -   S09-T03: Performance Testing and Optimization (12 hrs) - Engineer 2
    -   S09-T04: Final Review and Polish (8 hrs) - Engineer 1
-   **Sprint Velocity**: 86 hours (Slightly over, indicates potential for spillover into the next sprint or need for minor scope adjustment/efficiency gain)

## Gantt Chart

```mermaid
%%{init: {
    'theme': 'default',
    'themeVariables': {
        'cText': '#333',
        'sectionBkgColor': '#e6f3ff',
        'sectionBkgColor2': '#fffde7'
    }
}}
%%
gantt
    title Task Timer CLI Project Timeline
    dateFormat YYYY-MM-DD
    axisFormat %a
    excludes    weekends

    section Sprint 1 (Milestone 1)
    Setup Rust      :crit, S01-T01, 2025-05-12, 1d
    Start Logic     :active, S01-T02, 2025-05-13, 1d 2h
    Progress Bar    :crit, S01-T03, 2025-05-13, 1d
    Notifications   :active, S01-T04, 2025-05-14, 1d
    Sound Alerts    :crit, S01-T05, 2025-05-14, 1d
    Status Cmd      :active, S01-T06, 2025-05-15, 1d
    Stop Logic      :crit, S01-T07, 2025-05-15, 1d
    Stop Reason     :active, S01-T08, 2025-05-16, 6h
    Session Notes   :crit, S01-T09, 2025-05-16, 6h
    Test Timer      :active, S01-T10, 2025-05-16, 2h, 2025-05-19, 8h

    section Sprint 2 (Milestone 2)
    Test Timer      :active, S01-T10_2, 2025-05-19, 8h
    Setup DB        :crit, S02-T01, 2025-05-19, 1d 2h
    Data Struct     :active, S02-T02, after S01-T10_2, 1d
    Pause Logic     :active, S02-T04, after S02-T02, 1d
    Tags/Cats       :crit, S02-T09, after S02-T01, 1d
    Resume Logic    :crit, S02-T05, after S02-T09, 1d
    Auto-Pause      :active, S02-T06, after S02-T04, 1d 4h
    Max Pause       :crit, S02-T07, after S02-T05, 1d
    Test Session    :active, S02-T10, after S02-T06, 1d 4h
    Save Session    :crit, S02-T03, after S02-T07, 1d 2h
    Pause Reason    :active, S02-T08, after S02-T10, 6h

    section Sprint 3 (Milestone 3)
    Save Session    :crit, S02-T03_2, 2025-05-26, 2h
    Pause Reason    :active, S02-T08_2, 2025-05-26, 6h
    Setup Config    :crit, S03-T01, after S02-T03_2, 1d
    Clear Basic     :active, S03-T06, after S02-T08_2, 6h
    Proj Config     :crit, S03-T05, after S03-T01, 1d
    Sel. Clearing   :active, S03-T07, after S03-T06, 1d
    Custom Breaks   :crit, S03-T04, after S03-T05, 1d
    Export Clear    :active, S03-T08, after S03-T07, 1d
    Pomodoro Vars   :crit, S03-T03, after S03-T04, 1d
    Custom Dur      :active, S03-T02, after S03-T08, 1d
    Archive Func    :crit, S03-T09, after S03-T03, 6h

    section Sprint 4 (Milestone 4)
    Stats Basic     :active, S04-T01, 2025-06-02, 1d
    Report Cmd      :active, S04-T06, after S04-T01, 6h
    Daily/Weekly    :crit, S04-T02, 2025-06-02, 1d
    Report Export   :active, S04-T07, after S04-T06, 1d
    Prod. Times     :crit, S04-T04, after S04-T02, 6h
    Report Templ.   :active, S04-T08, after S04-T07, 1d
    Success Rate    :crit, S04-T03, after S04-T04, 6h
    Interrupt. P.   :active, S04-T05, after S04-T08, 6h
    Update DB Sch.  :crit, S05-T01, after S04-T03, 1d
    Task Creation   :active, S05-T02, after S04-T05, 1d
    Burndown Logic  :active, S04-T09, after S05-T02, 6h

    section Sprint 5 (Milestone 5)
    Task Editing    :crit, S05-T03, 2025-06-09, 1d
    Task Deletion   :active, S05-T04, 2025-06-09, 1d
    Assoc. Sess.    :crit, S05-T05, after S05-T03, 1d
    Priorities/D.   :active, S05-T06, after S05-T04, 1d
    Task Sched.     :crit, S05-T07, after S05-T05, 1d
    Task Depend.    :active, S05-T09, after S05-T06, 1d
    Est. Pomodoros  :active, S05-T08, after S05-T09, 6h
    Task Listing    :crit, S05-T10, after S05-T07, 1d 4h
    Setup Git Lib   :crit, S06-T01, after S05-T10, 1d
    Setup Cal Lib   :active, S06-T05, after S05-T08, 1d

    section Sprint 6 (Milestone 6 - Part 1)
    Task Listing    :crit, S05-T10_2, 2025-06-16, 4h
    Setup Git Lib   :crit, S06-T01_2, after S05-T10_2, 1d
    Setup Cal Lib   :active, S06-T05_2, 2025-06-16, 8h
    Feature Flags   :crit, S06-T14, after S06-T01_2, 1d
    Setup API       :active, S06-T09, after S06-T05_2, 1d
    Secure Cred.    :crit, S06-T13, after S06-T14, 1d
    API Status      :active, S06-T10, after S06-T09, 6h
    Network Fail.   :active, S06-T15, after S06-T10, 1d
    Google Auth     :crit, S06-T06, after S06-T13, 1d
    API Session     :crit, S06-T11, after S06-T06, 1d
    Sync Calendar   :active, S06-T07, after S06-T15, 1d

    section Sprint 7 (M6 Rem. & Milestone 9)
    Auto-Commit     :crit, S06-T02, 2025-06-23, 6h
    Branch Track.   :crit, S06-T03, after S06-T02, 1d
    PR/Issue Log    :crit, S06-T04, after S06-T03, 6h
    User Docs       :crit, S09-T02, after S06-T04, 1d
    Block Calendar  :active, S06-T08, 2025-06-23, 6h
    Webhook Support :active, S06-T12, after S06-T08, 6h
    Cross-Platform  :active, S09-T01, after S06-T12, 1d 4h
    Final Review    :crit, S09-T04, after S09-T02, 1d
    Performance     :active, S09-T03, after S09-T01, 1d 4h
```

## Parallel Work Streams

Work is divided between two engineers, allowing for parallel execution of tasks that do not have dependencies on each other within a sprint. The general division of work is as follows:

-   **Engineer 1**: Focuses on core timer logic enhancements, data storage setup and management, configuration handling, reporting analysis logic, task database schema, and the setup and core implementation of Git and Calendar integrations.
-   **Engineer 2**: Concentrates on user interface elements (progress bar, notifications, sounds), command-line argument parsing, status and stop command details, pause/resume logic implementation, clear command filtering and export, statistics command structure and export formats, task command implementation, and the setup and core implementation of the API and Webhook integrations.

This split aims to minimize bottlenecks and maximize throughput by allowing engineers to work on different parts of the application concurrently. Dependencies are explicitly managed in the task breakdown and sprint planning to ensure a logical flow of development.

## Risk Management

-   **Risk**: Slippage in early sprints (especially Sprint 1 and 2) due to unforeseen complexity in core timer logic or data storage, impacting all downstream dependencies and the overall timeline.
    -   **Mitigation**: Closely monitor progress in the initial sprints. Conduct frequent code reviews and testing to identify issues early. Be prepared to re-evaluate task estimates and potentially adjust scope or allocate additional buffer time if significant delays are encountered.

-   **Risk**: Underestimation of the effort required for implementing platform-specific features (like auto-pause detection) or complex integrations (like Google Calendar OAuth flow, secure credential storage, or graceful network failure handling).
    -   **Mitigation**: Allocate dedicated time for research or spikes before committing to full implementation for tasks identified as potentially high-risk or requiring platform-specific knowledge. Prioritize implementing robust error handling and testing for integration points.

-   **Risk**: With a team size of 2, the absence of a single engineer for an extended period could significantly impact the sprint velocity and overall project timeline.
    -   **Mitigation**: Foster a culture of good documentation and knowledge sharing. Ensure that code is clean, well-commented, and follows team standards to facilitate potential handoffs if necessary. Plan for tasks to be as independent as possible within the constraints of the project.

-   **Risk**: Dependencies between tasks within the External Integration milestone (Milestone 6) could create bottlenecks, particularly where multiple features rely on common foundational components (like feature flags, secure storage, or network handling).
    -   **Mitigation**: Prioritize the implementation of foundational M6 tasks early in the sprint (as reflected in the plan). Conduct integration testing frequently as components are completed to identify and address dependency issues proactively.
