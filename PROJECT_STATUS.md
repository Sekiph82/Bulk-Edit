# PROJECT_STATUS.md — Non-Authoritative Compatibility Pointer

`PROJECT_STATUS.md` is no longer a current-state source of truth.

The only authoritative current project-status tracker for Bulk-Edit and H!veAI is the repository root [`TASKS.md`](./TASKS.md).

Use root `TASKS.md` for:

- Current Milestone
- Current Sprint
- Current Task
- Current Task Status
- Next Task/Action
- Required Actor
- Workflow State
- Blockers/Waits
- canonical task IDs and checkbox statuses
- H!veAI progress/task counts

This file must not duplicate or independently redefine those fields. If this file conflicts with root `TASKS.md`, root `TASKS.md` wins.

## Historical status sources

- `CHANGELOG_AI.md` contains chronological engineering/session history and historical claims.
- `DECISIONS.md` contains durable architecture/product/process decisions.
- Git history preserves prior versions of this file and the former long-form production-status narrative.
- `docs/migration/legacy-task-trackers/` contains retired H!veAI control-plane artifacts preserved for provenance only.

## Current resume rule

Agents and maintainers must resume from root `TASKS.md`, not from this compatibility file. The active task and next action are intentionally not repeated here to prevent tracker drift.
