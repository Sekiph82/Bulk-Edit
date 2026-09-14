# CLAUDE.md — Bulk-Edit Project Operating Manual

## Project Goal

Build and operate a production-grade SaaS application for Etsy sellers to sync shops/listings, perform safe bulk edits, use preview-first AI and pricing tools, manage media/video workflows, and control billing without bypassing Etsy safety, audit, or plan gates.

## Repository

- Owner: Sekiph82
- Repository: Bulk-Edit
- URL: https://github.com/Sekiph82/Bulk-Edit
- Default branch: main

## H!veAI Canonical Tracking

The repository root `TASKS.md` is the only authoritative current project-status tracker consumed by H!veAI.

Do not use or recreate a hidden `.hiveai` control plane. Historical `.hiveai` artifacts were retired into `docs/migration/legacy-task-trackers/` and are archival evidence only.

At session start, read in this order:

1. `CLAUDE.md`
2. root `TASKS.md`
3. `SKILLS.md`
4. `DECISIONS.md`
5. `LIMIT_PROTOCOL.md` when checkpoint/resume behavior is relevant
6. implementation docs required by the active task

Derive the current milestone, sprint, task, status, next action, required actor, workflow state, and blockers from root `TASKS.md`, not from `PROJECT_STATUS.md` or `HANDOFF.md`.

When work changes project state:

1. Update `TASKS.md` Project Status using plain parser labels, never bold labels.
2. Update the matching canonical task row using `[x]`, `[~]`, `[!]`, or `[ ]`.
3. Keep evidence and history as ordinary bullets rather than accidental task checkboxes.
4. Update `## Blockers/Waits` when needed.
5. Append durable decisions to `DECISIONS.md` and engineering history to `CHANGELOG_AI.md` when appropriate.
6. Commit the tracker change with the evidence it describes.

Canonical task row format:

`- [status] TASK-ID — Title`

Do not create a competing task ledger in `PROJECT_STATUS.md`, `HANDOFF.md`, provider-specific memory files, or hidden folders.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, App Router, TypeScript |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 |
| ORM / migrations | SQLAlchemy 2.x + Alembic |
| Cache / broker | Redis 7 |
| Task queue | Celery |
| Auth | JWT access/refresh + Etsy OAuth2 |
| Billing | Stripe |
| Storage | S3-compatible |
| Containerization | Docker / Docker Compose |
| CI/CD | GitHub Actions |

## Non-Negotiable Safety Rules

1. Never hardcode or expose secrets. Use environment variables and redact sensitive values from logs/docs.
2. Never write to Etsy without the established safe-write path: preview, explicit confirmation, backup where supported, ownership/permission checks, subscription gate, audit logging, rate-limit/pacing controls, item-level results, and failure handling.
3. Never auto-apply AI output to Etsy. AI output must be previewed and user-approved.
4. Etsy live tests/writes are owner-run unless the owner explicitly authorizes the exact action.
5. Never disable Private Beta, change DNS/Cloudflare, change production environment, or perform real Stripe charge/refund/subscription actions without explicit owner instruction.
6. Never leak OAuth code/state, access/refresh tokens, Etsy shared/client secrets, DigitalOcean tokens, authorization headers, cookies, raw environment values, or database URLs.
7. Paid features must use the effective-plan gate, not an unsafe raw-plan shortcut.
8. Prefer small, restartable, independently testable changes.
9. Builder/agent self-report is not acceptance evidence by itself.
10. Merging to `main` redeploys production, including docs-only merges. Use reviewed PRs and do not merge casually.

## External Write Safety Protocol

Before an Etsy write:

1. Generate and show the intended change/preview.
2. Require explicit user/owner confirmation for the authorized live action.
3. Capture a recoverable snapshot/backup when the workflow supports it.
4. Verify organization/shop ownership and permission.
5. Verify effective-plan/feature gates.
6. Record safe audit metadata without secrets.
7. Apply rate-limit pacing/retry protection.
8. Execute the write.
9. Return item-level success/skipped/failed results.
10. Preserve or expose revert/recovery behavior where supported.

Use the `safe-external-write` skill for write-surface work.

## Skill Selection Protocol

Before implementation:

1. Read `SKILLS.md`.
2. Select the primary skill and any supporting skills.
3. Identify files to inspect and files expected to change.
4. Identify tests and acceptance evidence required by the active `TASKS.md` row.

If a missing skill is genuinely required, add it deliberately rather than silently inventing a parallel workflow.

## Checkpoint and Session-End Protocol

When the user says `checkpoint`, `limit`, `dur`, `finish session`, or `oturumu bitir`, or when context is running out:

1. Stop starting new work and finish only the current safe atomic unit.
2. Run relevant tests when feasible.
3. Update root `TASKS.md` if current task/status/next action/blockers changed.
4. Append to `CHANGELOG_AI.md` when a meaningful engineering session occurred.
5. Append to `DECISIONS.md` when a durable decision was made.
6. Commit and push the working branch only when appropriate to the task and repository safety policy.

`PROJECT_STATUS.md` and `HANDOFF.md` are non-authoritative compatibility pointers. Do not duplicate current task state into them.

## Fork / Subagent Scope Discipline

A historical read-only fork exceeded its scope and autonomously wrote/committed code. The resulting fix was technically accepted, but the process violation remains a durable lesson.

1. Read-only, audit-only, investigation-only, or “do not write code” means no file edits, commits, pushes, PRs, migrations, or production mutations.
2. A read-only investigation that finds a fix reports the proposed fix and stops.
3. Subagents inherit every parent-task restriction.
4. The parent must not silently accept unauthorized mutations from a read-only subagent; stop, audit, and record the scope violation.
5. Execution logs should state whether subagents/forks stayed within assigned scope.
6. Every subagent prompt must explicitly identify it as read-only or implementation-capable.

## Git / Branch Discipline

- Inspect `git status`, branch, and HEAD before meaningful work.
- Do not reset/rebase/force-push over unrelated user work.
- Prefer a dedicated branch + PR for changes that would trigger production deploy on merge.
- Commit meaningful checkpoints with clear messages.
- Update root `TASKS.md` in the same PR when task truth changes.
- Never claim a push/merge/deploy that was not actually verified.

## No-Question Policy

Make reasonable technical decisions when repository evidence resolves the ambiguity. Document durable decisions in `DECISIONS.md`. Do not invent credentials, production facts, acceptance evidence, or authorization for live actions. When an owner-only action is required, mark the task/blocker truthfully in `TASKS.md` and stop at the safe boundary.
