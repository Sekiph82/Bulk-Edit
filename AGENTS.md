# Bulk-Edit Agent Instructions

## H!veAI canonical tracking contract

Before doing project work, read the repository root `TASKS.md`.

The root `TASKS.md` is the only authoritative current project-status tracker consumed by H!veAI. GitHub repository metadata and the latest commit are the other project-truth inputs. Files under `docs/migration/legacy-task-trackers/` are historical artifacts only.

Do not create, revive, or update `.hiveai/PROJECT.json`, `.hiveai/TASKS.md`, `.hiveai/RULES.md`, `.hiveai/EVENTS.jsonl`, or any equivalent competing current-state ledger.

When work changes project state:

1. Update the plain-text `## Project Status` fields in root `TASKS.md`.
2. Update the matching canonical task row using exactly one parser-safe status marker: `[x]`, `[~]`, `[!]`, or `[ ]`.
3. Keep evidence and explanatory notes as ordinary bullets, never extra checkbox rows unless they are genuine independently tracked tasks with stable IDs.
4. Update `## Blockers/Waits` when a blocker appears or clears.
5. Commit the `TASKS.md` state change with the implementation/acceptance evidence it describes.

Parser-sensitive Project Status labels must not be Markdown-bolded. The canonical labels are:

- `Current Milestone:`
- `Current Sprint:`
- `Current Task:`
- `Current Task Status:`
- `Next Task/Action:`
- `Required Actor:`
- `Workflow State:`

Canonical task rows must use `- [status] TASK-ID — Title`.

Builder/agent self-reports are claims, not acceptance evidence. Do not promote a task to `[x]` without the level of source, test, production, audit, or owner evidence required by that task.

## Repository safety

- Read-only/audit-only work may not mutate repository or production state.
- Subagents inherit every restriction from the parent task.
- Never expose or commit secrets, OAuth values, authorization headers, cookies, raw environment values, or database URLs.
- Etsy live writes/tests are owner-run unless the owner explicitly authorizes that exact action.
- Merging to `main` deploys production, including docs-only merges. Prefer a reviewed PR and do not merge casually.
