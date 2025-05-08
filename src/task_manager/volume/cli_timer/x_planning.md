# CLI Timer Project Plan

## Sprint Planning

This project will be implemented over 2 sprints, based on a team capacity of 80 hours per week (2 engineers * 40 hours/engineer).

### Team Capacity

-   **Team Size**: 2 Engineers
-   **Hours Per Engineer Per Week**: 40 hours
-   **Total Team Capacity Per Week**: 80 hours

The plan below allocates tasks to maximize parallelization between the two engineers while respecting task dependencies. Tasks are assigned to sprints based on milestone priority and pulled forward where necessary to fill capacity and manage dependencies.

### Sprint 1 (Week of 2025-05-12)

-   **Capacity**: 80 hours
-   **Milestone Focus**: Primarily Milestone 1 (Core Timer Functionality), with tasks pulled from Milestones 2 & 3 to utilize capacity and manage dependencies.
-   **Tasks**:
    -   **Engineer 1 (40 hours):**
        -   S01-T01: Init Repo & Structure (6h) - *Milestone 1*
        -   S01-T03: Timer Core (Basic) (10h) - *Milestone 1*
        -   S01-T05: Integrate `status` Command (6h) - *Milestone 1*
        -   S02-T03: History File Setup (8h) - *Milestone 2 (Pulled Forward)*
        -   S02-T04: Session Tracking Logic (10h) - *Milestone 2 (Pulled Forward)*
    -   **Engineer 2 (40 hours):**
        -   S01-T02: CLI Parsing (Core Commands) (8h) - *Milestone 1*
        -   S01-T04: Integrate `start` Command (6h) - *Milestone 1*
        -   S01-T06: Integrate `stop` Command (6h) - *Milestone 1*
        -   S03-T01: CLI Parsing (Custom Duration) (6h) - *Milestone 3 (Pulled Forward)*
        -   S03-T03: CLI Parsing (`clear` Command) (6h) - *Milestone 3 (Pulled Forward)*
        -   S03-T04: Implement `clear` Command Logic (8h) - *Milestone 3 (Pulled Forward)*
-   **Sprint Velocity**: 80 hours

### Sprint 2 (Week of 2025-05-19)

-   **Capacity**: 80 hours (Utilizing approximately 32 hours)
-   **Milestone Focus**: Completing remaining tasks from Milestone 2 (Session Management) and Milestone 3 (Configuration and Cleanup).
-   **Tasks**:
    -   **Engineer 1 (16 hours):**
        -   S02-T01: Timer Core (Pause/Resume) (10h) - *Milestone 2*
        -   S03-T02: Integrate Custom Duration (6h) - *Milestone 3*
    -   **Engineer 2 (16 hours):**
        -   S02-T02: Integrate `pause`/`resume` Commands (8h) - *Milestone 2*
        -   S02-T05: Integrate History Writing (8h) - *Milestone 2*
-   **Sprint Velocity**: 32 hours

## Project Timeline (Gantt Chart)

Tasks are scheduled linearly per engineer within each sprint, respecting dependencies. Weekends are excluded. Task names are kept concise for readability.

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
    title CLI Timer Project Timeline
    dateFormat YYYY-MM-DD
    axisFormat %a
    excludes    weekends

    section Sprint 1 (Milestone 1 Focus)
    InitRepoE1      :crit, S01T01E1, 2025-05-12, 6h
    TimerCoreE1     :crit, S01T03E1, after S01T01E1, 10h
    StatusCmdE1     :crit, S01T05E1, after S01T03E1, 6h
    HistoryFileE1   :crit, S02T03E1, after S01T01E1, 8h
    SessionTrackE1  :crit, S02T04E1, after S01T03E1, 8h
    CLIParsingE2    :active, S01T02E2, 2025-05-12, 8h
    StartCmdE2      :active, S01T04E2, after S01T03E1, 6h
    StopCmdE2       :active, S01T06E2, after S01T04E2, 6h
    CustomDurE2     :active, S03T01E2, after S01T06E2, 6h
    ClearCmdE2      :active, S03T03E2, after S03T01E2, 6h

    section Sprint 2 (Milestone 2 & 3 Completion)
    SessionTrackE1_c :crit, S02T04E1_c, 2025-05-19, 2h
    PauseResumeE1   :crit, S02T01E1, after S02T04E1_c, 10h
    IntegrateDurE1  :crit, S03T02E1, after S02T01E1, 6h
    ClearLogicE2    :active, S03T04E2, 2025-05-19, 8h
    PauseResumeC2   :active, S02T02E2, after S03T04E2, S02T01E1, 8h
    HistoryWriteE2  :active, S02T05E2, after S02T02E2, 8h
```

## Parallel Work Streams

Work is divided across two main streams, aligned with engineer assignments:

1.  **Engineer 1:** Focuses on the core timer logic, session state management (including pause/resume), history file setup, and the underlying session tracking logic.
2.  **Engineer 2:** Concentrates on command-line interface parsing for all commands (`start`, `status`, `stop`, `pause`, `resume`, `clear`, custom duration flags) and integrating these commands with the core timer and history writing logic.

Dependencies between these streams are managed within the sprint plan to ensure tasks can be picked up as soon as their prerequisites are met.

## Risk Management

-   **Risk**: Task estimates prove inaccurate.
    -   **Mitigation**: Maintain flexibility in task assignments within a sprint. Conduct daily stand-ups to monitor progress and adjust if tasks are taking significantly longer or shorter than expected. Be prepared to re-scope or move tasks to the next sprint if necessary.
-   **Risk**: Dependencies between tasks cause unexpected delays or blocking.
    -   **Mitigation**: Engineers should communicate proactively when a task is nearing completion that unblocks a colleague. Prioritize tasks that are dependencies for others to finish earlier in the sprint.
-   **Risk**: Absence of one of the two engineers.
    -   **Mitigation**: With a team size of 2, any individual's absence can significantly impact the timeline. Ensure clear documentation for all tasks. If an absence occurs, re-evaluate the current sprint scope and re-allocate tasks if feasible, or adjust the timeline.
-   **Risk**: Ambiguities in requirements or technical details are discovered during implementation.
    -   **Mitigation**: Foster a culture of asking clarifying questions early. If a significant ambiguity is found that impacts the approach, pause implementation and seek clarification before proceeding.
