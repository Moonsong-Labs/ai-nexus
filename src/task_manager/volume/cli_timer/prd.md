# Task Timer CLI – PRD

## Overview
A simple command-line timer to help users focus on tasks using the Pomodoro technique.

## Milestones & Features

### Milestone 1: Core Timer Functionality
- Implement a `start` command that begins a countdown for a fixed work session (default: 25 minutes)
- Implement a `status` command to check the remaining time
- Implement a `stop` command to end the session early

### Milestone 2: Session Management
- Add support for `pause` and `resume` commands
- Add tracking of completed sessions in a local file (e.g. `.tasktimer/history.log`)

### Milestone 3: Configuration and Cleanup
- Allow custom session durations via CLI arguments (e.g. `--work 20 --break 5`)
- Implement a `clear` command to delete session history

