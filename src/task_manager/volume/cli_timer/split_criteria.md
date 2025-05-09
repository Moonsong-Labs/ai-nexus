# Task Splitting Criteria

## Flexible Granularity for Small Teams

Each feature from the PRD should be split into engineering tasks that follow these principles:

- **Flexible Time-box**: Aim for tasks that can be completed in 6–14 hours by a senior team member. Only split further if a task exceeds 14 hours, is ambiguous, or blocks parallel work.

- **Right-Sized Granularity**: Only split a feature further if:
  - The task would take more than 14 hours.
  - The task is ambiguous or not independently testable.
  - The task would block multiple people from working in parallel.

- **Parallelization (Team-Aware)**: Split tasks to maximize parallel work only when it will actually speed up delivery or reduce bottlenecks. Be mindful of the available team capacity when planning parallel work.

- **Descriptive, Not Excessive**: Use clear, descriptive names, but avoid creating separate tasks for every minor step unless justified by size or complexity. Only create separate tasks for testing, documentation, or refactoring if they are substantial.

- **Explicit Exceptions (Epics)**: Allow for larger (14–20 hour) tasks if they are well-defined and have a clear plan for mid-way review. Use these sparingly and only when further splitting would add overhead without benefit.

## Additional Rules

- Tasks should be clear, specific, and implementation-ready.
- Include necessary setup/infrastructure tasks as separate items only if they are substantial.
- Explicitly document dependencies between tasks when unavoidable.

## Dependency Management

- Minimize dependencies between tasks to increase parallelization, but be mindful of the team capacity limits.
- Clearly document any unavoidable dependencies in the task definition.
- Consider using feature toggles to allow dependent features to be developed in parallel.

