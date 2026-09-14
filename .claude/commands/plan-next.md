# /plan-next

Plan only from the canonical root `TASKS.md` ledger.

1. Read `TASKS.md` Project Status, Blockers/Waits, and canonical task rows.
2. Treat `[~]` as active/partial, `[!]` as blocked, `[ ]` as planned/backlog, and `[x]` as validated complete.
3. Respect dependencies, owner-only gates, production-write safety, and the Required Actor/Workflow State fields.
4. Use `ROADMAP.md`, audits, `DECISIONS.md`, and `CHANGELOG_AI.md` only as supporting context.
5. Do not resurrect completed or historical work unless a new verified defect explicitly reopens it.
6. When proposing the next executable task, keep its stable task ID and identify the evidence required for closure.

Do not plan from `PROJECT_STATUS.md`, `HANDOFF.md`, or archived `.hiveai` ledgers.
