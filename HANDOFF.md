# HANDOFF.md — Non-Authoritative Session Notes Pointer

`HANDOFF.md` is retained only as a compatibility pointer. It is not a current project-status tracker and must not carry an independent Current Task, Next Action, milestone, sprint, actor, or blocker ledger.

## Resume from canonical state

Resume every new Claude/Codex/agent session from the repository root [`TASKS.md`](./TASKS.md).

Root `TASKS.md` owns:

- Project Status metadata
- Current Milestone and Current Sprint
- Current Task and Current Task Status
- Next Task/Action
- Required Actor and Workflow State
- Blockers/Waits
- canonical task IDs/status markers
- H!veAI task/progress parsing

## Historical handoff material

The former long-form session handoff history remains available in Git history. Additional historical evidence lives in:

- `CHANGELOG_AI.md`
- `DECISIONS.md`
- `docs/audits/`
- `docs/operations/`
- `docs/migration/legacy-task-trackers/`

Do not copy current state back into this file. Doing so would create a second tracker that can drift away from H!veAI's canonical root `TASKS.md`.

## Session-end rule

When a session changes task truth, update root `TASKS.md` in the same branch/PR as the implementation or acceptance evidence. Use `CHANGELOG_AI.md` for chronological engineering history and `DECISIONS.md` for durable decisions.
