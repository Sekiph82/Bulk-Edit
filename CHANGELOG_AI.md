# CHANGELOG_AI.md — AI Session Log

Append one entry per session. Format: `## [DATE] Sprint N — Summary`

---

## 2026-06-25 Sprint 1 (rev 2) — Custom Ports Applied + CORS Fix

**Skills active:** 05 repo-setup, 04 system-architect, 07 backend-api, 22 devops-deployment, 01 documentation-handoff

**Completed:**
- Updated `docker-compose.yml`: host ports 3100/8100/55432/56379 (container ports unchanged)
- Updated `.env.example`: FRONTEND_URL=:3100, BACKEND_URL=:8100, BACKEND_CORS_ORIGINS plain string format
- Updated `apps/backend/.env.example`: localhost:55432, localhost:56379
- Updated `apps/frontend/.env.local.example`: NEXT_PUBLIC_BACKEND_URL, NEXT_PUBLIC_APP_URL
- Updated `apps/frontend/app/page.tsx`: env var → NEXT_PUBLIC_BACKEND_URL, default :8100
- Updated `apps/frontend/app/dashboard/page.tsx`: same
- Fixed `app/core/config.py`: BACKEND_CORS_ORIGINS as `str` with `get_cors_origins()` method (pydantic-settings v2 can't use field_validator on List[str] before JSON pre-parse)
- Updated `app/main.py`: CORS middleware uses `settings.get_cors_origins()`
- Updated `Makefile`: health curl targets use :8100
- Updated `README.md`, `docs/operations/DEPLOYMENT.md`: all URLs use custom ports
- Ran pytest: 4/4 PASSED, 0 warnings
- Verified CORS validator: plain string and JSON array both parse correctly

**Decisions made:**
- Custom host ports documented in DECISIONS.md
- BACKEND_CORS_ORIGINS storage strategy documented in DECISIONS.md

**Blockers:** None

**Next:** Sprint 2 — Auth + Organization

---

## 2026-06-25 Sprint 1 — Monorepo Skeleton Created

**Skills active:** 05 repo-setup, 04 system-architect, 07 backend-api, 08 frontend-ui, 06 database-modeling, 22 devops-deployment, 20 testing-qa

**Completed:**
- Created `apps/frontend/` — Next.js 14, App Router, TypeScript, Tailwind CSS, landing page, dashboard placeholder, Dockerfile
- Created `apps/backend/` — FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2 settings, health endpoints (`/api/v1/health`, `/api/v1/health/db`, `/api/v1/health/redis`), Dockerfile, pytest suite (4/4 pass)
- Created `docker-compose.yml` — services: frontend (3000), backend (8000), postgres (5432), redis (6379) with healthchecks
- Created `Makefile` — `make dev`, `make migrate`, `make test`, `make health`
- Created `.gitignore` — Python + Node + Docker volumes
- Updated `.env.example` — Docker Compose alignment, frontend env vars
- Updated `README.md` — full local setup instructions
- Ran pytest: 4/4 PASSED, 0 warnings

**Decisions made:**
- See DECISIONS.md for anyio version note and asyncpg pool config

**Blockers:** None

**Next:** Sprint 2 — Auth + Organization

---

## 2026-06-25 Sprint 0 — Project Operating System Initialized

**Skills active:** 01 documentation-handoff, 05 repo-setup

**Completed:**
- Created all Sprint 0 files (CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, ARCHITECTURE.md, LIMIT_PROTOCOL.md, SECURITY.md, CHANGELOG_AI.md, ROADMAP.md, README.md, .env.example)
- Created all Claude command files (.claude/commands/)
- Created all documentation files (docs/product/, docs/technical/, docs/operations/)
- Initialized git repository and connected to GitHub remote
- Committed and pushed Sprint 0 to main

**Decisions made:**
- See DECISIONS.md — full tech stack and product decisions documented

**Blockers:** None

**Next:** Sprint 1 — Monorepo Skeleton
