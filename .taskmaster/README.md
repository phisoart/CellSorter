# Task Master - CellSorter Project

Task Master is initialized for the CellSorter project to manage development tasks and track progress.

## Structure

```
.taskmaster/
├── config.json      # Model configuration for AI assistance
├── state.json       # Project state and progress tracking
├── docs/           
│   └── prd.txt     # Product Requirements Document
└── tasks/
    └── tasks.json  # Task definitions and tracking
```

## Current Status

- **Total Tasks**: 12
- **Completed**: 0
- **In Progress**: 0
- **Todo**: 12

## Priority Breakdown

- **High Priority**: 7 tasks (core functionality)
- **Medium Priority**: 4 tasks (enhancements)
- **Low Priority**: 1 task (nice-to-have)

## Task Categories

- **Feature Development**: 9 tasks
- **Infrastructure**: 1 task
- **Testing**: 1 task
- **UI/UX**: 1 task

## Key Development Areas

1. **Image Processing** - Loading and displaying microscopy images
2. **Data Analysis** - CSV parsing and scatter plot visualization
3. **User Interaction** - Cell selection and management
4. **Coordinate System** - Calibration and transformation
5. **Export System** - Protocol generation for hardware
6. **Application Framework** - Main window and session management

## Getting Started

To view current tasks:
```bash
cat .taskmaster/tasks/tasks.json | jq '.tasks[] | {id, title, status, priority}'
```

To check project state:
```bash
cat .taskmaster/state.json | jq '.'
```

## Task Workflow

1. Pick a task from the todo list
2. Update task status to "in_progress"
3. Implement following TDD principles
4. Update task status to "completed"
5. Update state.json with progress

## Next Steps

High-priority tasks to start with:
- TASK-001: Implement Image Loading Module
- TASK-002: Create CSV Parser Module
- TASK-007: Design Main Application Window

These form the foundation for the CellSorter application.