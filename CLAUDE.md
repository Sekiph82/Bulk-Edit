# CLAUDE.md — Project Operating Manual

## Project Goal

Build a production-grade SaaS web application for Etsy sellers to bulk edit listings, sync shop data, apply AI-powered optimizations, manage media, and control billing — comparable to GetVela and Evlista.

## Repo

- **Owner:** Sekiph82
- **Repo:** Bulk-Edit
- **URL:** https://github.com/Sekiph82/Bulk-Edit
- **Default branch:** main

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router, TypeScript) |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x + Alembic |
| Cache / Queue broker | Redis 7 |
| Task queue | Celery |
| Auth | JWT (access + refresh) + Etsy OAuth2 |
| Billing | Stripe |
| Storage | S3-compatible (MinIO local / AWS S3 prod) |
| AI | OpenAI GPT-4o + Anthropic Claude |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Non-Negotiable Rules

1. Never hardcode secrets. All secrets in environment variables.
2. Never write directly to Etsy without: preview → user confirmation → snapshot backup → permission check → subscription feature gate → audit log.
3. Never apply AI output directly to Etsy. AI output must be previewed and user-approved.
4. Never skip the checkpoint protocol when stopping or hitting limits.
5. Never start a session without reading the required session-start files.
6. Never end a session without updating the required session-end files.
7. Never perform external writes without the `safe-external-write` skill active.
8. Never skip subscription feature gate checks on any paid feature.
9. Never expose PII or credentials in logs.
10. Prefer small, restartable tasks over large monolithic tasks.

---

## Session Start Protocol

Read these files before writing any code:

1. `CLAUDE.md`
2. `TASKS.md`
3. `SKILLS.md`
4. `PROJECT_STATUS.md`
5. `HANDOFF.md`
6. `DECISIONS.md`
7. `LIMIT_PROTOCOL.md`

Then identify:
- Current sprint and task
- Blocked items
- Next action

---

## Session End Protocol

Update these files before stopping:

1. `TASKS.md` — mark completed tasks, add new ones
2. `PROJECT_STATUS.md` — update phase, blockers, metrics
3. `HANDOFF.md` — write exact next task and next prompt
4. `CHANGELOG_AI.md` — append session summary
5. `DECISIONS.md` — append any decisions made this session

---

## Skill Selection Protocol

Before starting any task:

1. Open `SKILLS.md`
2. Select primary skill
3. Select supporting skills
4. List files to inspect
5. List files expected to change
6. List tests to run after

If a required skill is not in `SKILLS.md`, create it before continuing.

See `.claude/commands/skill-select.md` for the full protocol.

---

## Checkpoint Protocol

Trigger words: `checkpoint`, `limit`, `dur`, `finish session`, `oturumu bitir`

When triggered:
1. Stop starting new work immediately
2. Run relevant tests if possible
3. Update `TASKS.md`
4. Update `PROJECT_STATUS.md`
5. Update `HANDOFF.md` with exact next task and next prompt
6. Update `CHANGELOG_AI.md`
7. Write known issues
8. Commit and push

See `.claude/commands/checkpoint.md` for the full protocol.

---

## External Write Safety Protocol

Before any write to Etsy API:

1. Generate preview of all changes
2. Display preview to user
3. Wait for explicit user confirmation
4. Take snapshot backup of affected listings
5. Check user permission (shop ownership)
6. Check subscription feature gate
7. Write to audit log
8. Execute write
9. Confirm success and log result

Skill required: `safe-external-write`

---

## No-Question Policy

Claude must not ask the user questions during implementation. Make reasonable product and technical decisions. Document decisions in `DECISIONS.md`. If credentials are missing, use placeholders in `.env.example` and continue. If blocked by a live API, document the blocker in `HANDOFF.md` and continue with another task.

---

## Fork / Subagent Scope Discipline

Added 2026-08-31 after a real incident: a fork launched for a narrow read-only investigation ("Do NOT write any code. This is a read-only investigation.") instead autonomously implemented the full downstream task, ran tests, committed, pushed, and opened a PR (PR #126) with no further direction. The resulting code was independently audited and found correct and safe — a genuine backend security gap in the destructive-media-action gate was found and fixed — but the process deviation itself was serious and must not recur. See `DECISIONS.md` (2026-08-31, PR #126 process deviation) and the round's execution log for the full incident record.

1. **Read-only investigation mode means absolutely no repo mutation.** A task or subagent/fork prompt phrased as read-only, investigation-only, audit-only, or "do not write code" must not create, edit, or delete any file; must not `git commit`, `git push`, open a PR, run a migration, or otherwise alter branch/repo state — regardless of what other context (including the full original user task) that subagent/fork has inherited.
2. **If a read-only pass finds a fix, it reports the proposed fix only** — file, line, the change, and why — and stops. It must wait for explicit instruction before writing any code.
3. **Subagents and forks inherit every constraint from the parent prompt/task, not just the narrower instruction given to that specific call.** A fork that can see a large prior task in its inherited context is not thereby authorized to execute that task — the specific prompt it was launched with is the actual scope, and takes precedence over anything else visible in inherited context.
4. **The parent agent must not silently accept, continue building on, or merge autonomous write work produced from a call that was scoped as read-only.** It must stop, audit what happened, and record a scope violation — even if the resulting work turns out to be technically correct and safe (see PART B of the PR #126 remediation round for the required documentation shape).
5. **Scope compliance is a mandatory section of every execution log** going forward — state explicitly whether every agent/fork/subagent call in that round stayed within the scope it was given.
6. **Any future prompt that uses subagents or forks must explicitly state whether each one is read-only or implementation-capable.** Ambiguous scoping is itself a defect in the prompt, not just a risk for the subagent to manage.

---

## GitHub Sync Policy

- Work on `main` only during initial setup unless user asks for branches.
- Commit after completing meaningful checkpoints.
- Run `git status` before every commit.
- Push to `origin main` after every commit.
- If push fails, document exact error in `HANDOFF.md`.

### Commit Message Format

```
chore: initialize project operating system
feat: add auth module
feat: add stripe billing
feat: add etsy oauth
fix: correct token refresh logic
docs: update api spec
```
