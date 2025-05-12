## Project Planning - cli_timer

Based on the provided Product Requirements Document (PRD), Technical Stack, and Task Splitting Criteria, the following plan outlines the engineering tasks and a proposed sprint schedule for the `cli_timer` project.

**Project:** cli_timer
**Team Size:** 2 Engineers
**Hours Per Engineer Per Week:** 40 hours
**Weekly Team Capacity:** 80 hours

### Sprint Planning

The project is broken down into 9 one-week sprints. Tasks are assigned to sprints based on their associated milestone, priority, and dependencies. Higher priority tasks and tasks from earlier milestones are prioritized. To maximize team capacity, tasks from subsequent milestones are pulled into earlier sprints if their dependencies are met and capacity is available.

**Sprint 1 (80 hours)**
*   **Milestones:** Core Timer Functionality (Milestone 1), Session Management (Milestone 2 - initial setup)
*   **Tasks:**
    *   S01-T01: Implement Basic Timer Logic (Engineer 1, 16h)
    *   S02-T04: Setup Session History Storage (Engineer 2, 8h)
    *   S01-T03: Implement Notifications & Sound (Engineer 1, 16h) - *Depends on S01-T01*
    *   S01-T02: Implement CLI Presentation (Engineer 2, 24h) - *Depends on S02-T04, S01-T01*
    *   S01-T05: Implement Stop Command (Engineer 1, 8h) - *Depends on S01-T03*
    *   S01-T04: Implement Status Command (Engineer 2, 8h) - *Depends on S01-T02*
*   **Sprint Velocity:** 80 hours

**Sprint 2 (80 hours)**
*   **Milestones:** Session Management (Milestone 2), Configuration and Customization (Milestone 3 - initial)
*   **Tasks:**
    *   S02-T01: Implement Pause/Resume Logic (Engineer 1, 16h)
    *   S02-T06: Add Session Metadata, Tags, Categories (Engineer 2, 16h)
    *   S02-T03: Implement Pause Reason Tracking (Engineer 1, 8h) - *Depends on S02-T01*
    *   S02-T02: Implement Auto-Pause Detection (Engineer 2, 24h) - *Depends on S02-T01*
    *   S03-T01: Implement Custom Duration Args (Engineer 1, 8h) - *Depends on S02-T03*
    *   S03-T04: Implement Clear Command Basic (Engineer 1, 8h) - *Depends on S03-T01*
*   **Sprint Velocity:** 80 hours

**Sprint 3 (80 hours)**
*   **Milestones:** Configuration and Customization (Milestone 3), Statistics and Insights (Milestone 4 - initial)
*   **Tasks:**
    *   S03-T02: Implement Custom Break Schedules (Engineer 1, 16h)
    *   S03-T03: Implement Per-Project Config (Engineer 2, 24h)
    *   S03-T06: Implement Data Export (Engineer 1, 16h) - *Depends on S03-T02*
    *   S03-T05: Implement Selective Clearing (Engineer 2, 16h) - *Depends on S03-T03*
    *   S04-T01: Implement Stats Basic (Engineer 1, 8h) - *Depends on S03-T06*
*   **Sprint Velocity:** 80 hours

**Sprint 4 (80 hours)**
*   **Milestones:** Configuration and Customization (Milestone 3 - completion), Statistics and Insights (Milestone 4)
*   **Tasks:**
    *   S04-T02: Calculate Daily/Weekly/Monthly Summaries (Engineer 1, 24h)
    *   S03-T07: Implement Archive Functionality (Engineer 2, 16h)
    *   S04-T03: Calculate Success Rates & Patterns (Engineer 1, 16h) - *Depends on S04-T02*
    *   S04-T04: Implement Report Command (Engineer 2, 8h) - *Depends on S03-T07*
    *   S04-T05: Implement Report Export Formats (Engineer 2, 16h) - *Depends on S04-T04*
*   **Sprint Velocity:** 80 hours

**Sprint 5 (80 hours)**
*   **Milestones:** Statistics and Insights (Milestone 4 - completion), Task Integration (Milestone 5 - initial), External Integration (Milestone 6 - initial)
*   **Tasks:**
    *   S04-T07: Implement Burndown Chart Data (Engineer 1, 16h)
    *   S04-T06: Implement Report Templating (Engineer 2, 24h)
    *   S05-T01: Setup SQLite Database (Engineer 1, 16h) - *Depends on S04-T07*
    *   S06-T01: Setup Git Integration (Engineer 2, 16h) - *Depends on S04-T06*
    *   S05-T04: Implement Task Priority/Deadline (Engineer 1, 8h) - *Depends on S05-T01*
*   **Sprint Velocity:** 80 hours

**Sprint 6 (80 hours)**
*   **Milestones:** Task Integration (Milestone 5), External Integration (Milestone 6)
*   **Tasks:**
    *   S05-T02: Implement Task CRUD (Engineer 1, 24h)
    *   S06-T05: Setup Calendar API Client (Engineer 2, 24h)
    *   S05-T07: Implement Task Dependencies (Engineer 1, 16h) - *Depends on S05-T02*
    *   S05-T03: Associate Sessions with Tasks (Engineer 2, 16h) - *Depends on S06-T05*
*   **Sprint Velocity:** 80 hours

**Sprint 7 (80 hours)**
*   **Milestones:** External Integration (Milestone 6)
*   **Tasks:**
    *   S06-T09: Implement REST API Server Setup (Engineer 1, 16h)
    *   S06-T06: Implement Google Calendar Sync (Engineer 2, 24h)
    *   S06-T10: Implement API Endpoints (Engineer 1, 24h) - *Depends on S06-T09*
    *   S06-T07: Implement Block Calendar During Sessions (Engineer 2, 8h) - *Depends on S06-T06*
    *   S06-T08: Implement Log Completed Sessions as Events (Engineer 2, 8h) - *Depends on S06-T07*
*   **Sprint Velocity:** 80 hours

**Sprint 8 (80 hours)**
*   **Milestones:** Task Integration (Milestone 5 - completion), External Integration (Milestone 6)
*   **Tasks:**
    *   S06-T02: Implement Auto-Commit Messages (Engineer 1, 16h)
    *   S05-T06: Implement Estimated Pomodoros (Engineer 2, 8h)
    *   S06-T03: Implement Branch Time Tracking (Engineer 1, 16h) - *Depends on S06-T02*
    *   S05-T05: Implement Daily/Weekly Planning (Engineer 2, 24h) - *Depends on S05-T06*
    *   S06-T04a: Implement PR/Issue Time Logging (Part A) (Engineer 1, 8h) - *Depends on S06-T03*
    *   S06-T12a: Implement Real-time Updates (Part A) (Engineer 2, 8h) - *Depends on S05-T05*
*   **Sprint Velocity:** 80 hours

**Sprint 9 (32 hours)**
*   **Milestones:** External Integration (Milestone 6 - completion)
*   **Tasks:**
    *   S06-T04b: Implement PR/Issue Time Logging (Part B) (Engineer 1, 16h) - *Depends on S06-T04a*
    *   S06-T12b: Implement Real-time Updates (Part B) (Engineer 2, 16h) - *Depends on S06-T12a*
*   **Sprint Velocity:** 32 hours

### Parallel Work Streams

Within each sprint, tasks are assigned to Engineer 1 and Engineer 2 to enable parallel work where dependencies allow. Work streams are generally divided based on the tasks identified and their dependencies, ensuring that prerequisite tasks are completed before dependent tasks begin, even if assigned to different engineers.

### Timeline (Gantt Chart)

The following Gantt chart provides a visual representation of the project timeline across the planned sprints, assuming a start date of **2025-05-12**.

```mermaid
%%{init: {
    'theme': 'default',
    'themeVariables': {
        'cText': '#333',
        'sectionBkgColor': '#e6f3ff',
        'sectionBkgColor2': '#fffde7'
    }
}}

gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    axisFormat %a
    excludes    weekends

    section Week 1
    Timer Logic E1  :crit, S01-T01, 2025-05-12, 2d
    Hist Storage E2 :active, S02-T04, 2025-05-12, 1d
    Notify/Sound E1 :crit, S01-T03, after S01-T01, 2d
    CLI Present E2  :active, S01-T02, after S02-T04, 3d
    Stop Cmd E1     :crit, S01-T05, after S01-T03, 1d
    Status Cmd E2   :active, S01-T04, after S01-T02, 1d

    section Week 2
    Pause/Resume E1 :crit, S02-T01, 2025-05-19, 2d
    Session Meta E2 :active, S02-T06, 2025-05-19, 2d
    Pause Reason E1 :crit, S02-T03, after S02-T01, 1d
    Auto-Pause E2   :active, S02-T02, after S02-T06, 3d
    Custom Dur E1   :crit, S03-T01, after S02-T03, 1d
    Clear Basic E1  :crit, S03-T04, after S03-T01, 1d

    section Week 3
    Custom Break E1 :crit, S03-T02, 2025-05-26, 2d
    Per-Proj Cfg E2 :active, S03-T03, 2025-05-26, 3d
    Data Export E1  :crit, S03-T06, after S03-T02, 2d
    Select Clear E2 :active, S03-T05, after S03-T03, 2d
    Stats Basic E1  :crit, S04-T01, after S03-T06, 1d

    section Week 4
    Daily/Wk Sum E1 :crit, S04-T02, 2025-06-02, 3d
    Archive Func E2 :active, S03-T07, 2025-06-02, 2d
    Succ Rate/Patt E1 :crit, S04-T03, after S04-T02, 2d
    Report Cmd E2   :active, S04-T04, after S03-T07, 1d
    Report Export E2 :active, S04-T05, after S04-T04, 2d

    section Week 5
    Burndown Data E1 :crit, S04-T07, 2025-06-09, 2d
    Report Tmpl E2  :active, S04-T06, 2025-06-09, 3d
    Setup SQLite E1 :crit, S05-T01, after S04-T07, 2d
    Setup Git E2    :active, S06-T01, after S04-T06, 2d
    Task Pri/DL E1  :crit, S05-T04, after S05-T01, 1d

    section Week 6
    Task CRUD E1    :crit, S05-T02, 2025-06-16, 3d
    Calendar API E2 :active, S06-T05, 2025-06-16, 3d
    Task Deps E1    :crit, S05-T07, after S05-T02, 2d
    Assoc Sess E2   :active, S05-T03, after S06-T05, 2d

    section Week 7
    API Server E1   :crit, S06-T09, 2025-06-23, 2d
    GCal Sync E2    :active, S06-T06, 2025-06-23, 3d
    API Endpoints E1 :crit, S06-T10, after S06-T09, 3d
    Block Cal E2    :active, S06-T07, after S06-T06, 1d
    Log Sessions E2 :active, S06-T08, after S06-T07, 1d

    section Week 8
    Auto-Commit E1  :crit, S06-T02, 2025-06-30, 2d
    Est Pomos E2    :active, S05-T06, 2025-06-30, 1d
    Branch Track E1 :crit, S06-T03, after S06-T02, 2d
    Daily/Wk Plan E2 :active, S05-T05, after S05-T06, 3d
    PR/Issue Log A E1 :crit, S06-T04a, after S06-T03, 1d
    Real-time A E2  :active, S06-T12a, after S05-T05, 1d

    section Week 9
    PR/Issue Log B E1 :crit, S06-T04b, 2025-07-07, 2d
    Real-time B E2  :active, S06-T12b, 2025-07-07, 2d
```

### Risk Management

*   **Task Estimation Accuracy:** The current plan relies on estimated task durations. Actual implementation time may vary.
    *   *Mitigation:* Regularly review task completion rates and adjust estimates and future sprint plans as needed. Maintain open communication within the team regarding task progress and blockers.
*   **External Dependencies:** Integration with external systems (e.g., Calendar APIs, GitHub API) and reliance on system-specific features (e.g., auto-pause) may introduce unforeseen challenges.
    *   *Mitigation:* Prioritize the setup and basic integration tasks for external services. Implement robust error handling and fallback mechanisms for external interactions. Thoroughly research platform-specific requirements for features like auto-pause.
*   **Team Capacity Fluctuations:** With a small team size, unexpected absences or reallocations could impact the planned timeline.
    *   *Mitigation:* Foster a collaborative environment where engineers are familiar with different parts of the codebase. Ensure tasks have clear descriptions and acceptance criteria to facilitate potential handovers. Build in small buffers where possible for unexpected delays.
