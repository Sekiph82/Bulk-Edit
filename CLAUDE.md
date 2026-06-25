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
