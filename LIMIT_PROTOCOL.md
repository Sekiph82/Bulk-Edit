# LIMIT_PROTOCOL.md — Checkpoint and Resume Protocol

This repository uses root `TASKS.md` as the only authoritative current-state tracker for H!veAI and agent resume behavior.

## Trigger

Use this protocol when the user says `checkpoint`, `limit`, `dur`, `finish session`, `oturumu bitir`, or when context/time is running low.

## Checkpoint steps

1. Stop starting new work and finish only the current safe atomic unit.
2. Run relevant tests when feasible.
3. Read root `TASKS.md` and update it only when task truth actually changed:
   - Current Milestone
   - Current Sprint
   - Current Task
   - Current Task Status
   - Next Task/Action
   - Required Actor
   - Workflow State
   - Blockers/Waits
   - matching canonical task row status
4. Keep Project Status labels plain text and parser-safe. Never bold the labels.
5. Keep evidence/notes as ordinary bullets. Only genuine canonical task rows may use `[x]`, `[~]`, `[!]`, or `[ ]`.
6. Append meaningful engineering/session history to `CHANGELOG_AI.md` when warranted.
7. Append durable architecture/product/process decisions to `DECISIONS.md` when warranted.
8. Commit/push only when appropriate to the task, branch, and production-deploy safety policy.

## Resume steps

1. Read `CLAUDE.md` or `AGENTS.md` as applicable.
2. Read root `TASKS.md`.
3. Resume from its Current Task, Next Task/Action, Required Actor, Workflow State, and Blockers/Waits.
4. Read `CHANGELOG_AI.md`, `DECISIONS.md`, audits, or Git history only when historical context is needed.

`PROJECT_STATUS.md` and `HANDOFF.md` are compatibility pointers only. They must not be used as independent resume ledgers.

## Safety

- Do not manufacture acceptance evidence at checkpoint time.
- Do not promote `[~]`, `[!]`, or `[ ]` to `[x]` only because implementation code exists.
- Owner-only Etsy live actions remain blocked until explicitly authorized and actually verified.
- Never expose secrets while recording checkpoint evidence.
