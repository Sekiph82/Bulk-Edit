# Bulk-Edit

Production-grade SaaS platform for Etsy sellers. Bulk edit listings, sync shop data, apply AI-powered optimizations, and manage media — with a full subscription billing system.

## What This Is

Bulk-Edit lets Etsy sellers:
- Connect their Etsy shops via OAuth
- Sync all listings automatically
- Bulk edit titles, descriptions, tags, photos, videos, prices, quantities, variations, categories, materials, personalization fields, return policies, weight and dimensions
- Preview all bulk changes before publishing
- Backup listings and revert changes with Magic Revert
- Use AI tools for title optimization, description writing, tag generation, alt text, SEO scoring, and category suggestions
- Manage a media library
- Import and export CSV
- Schedule listing updates
- Use dynamic pricing rules
- Pay through Free, Monthly Pro, or Yearly Pro subscription plans

## Current Phase

**Sprint 0 — Project Memory and Operating System** (Complete)

Next: Sprint 1 — Monorepo Skeleton

## How Claude Should Continue

1. Read `CLAUDE.md` first.
2. Read `TASKS.md` to find current sprint.
3. Read `HANDOFF.md` for exact next action.
4. Read `SKILLS.md` to select active skills.
5. Read `PROJECT_STATUS.md` for current blockers.
6. Read `DECISIONS.md` for prior architectural decisions.
7. Read `LIMIT_PROTOCOL.md` to know checkpoint behavior.
8. Execute the next task from HANDOFF.md.

## Local Setup (Placeholder — Sprint 1)

> Full setup instructions will be written in Sprint 1 after the monorepo skeleton is created.

Requirements (planned):
- Docker and Docker Compose
- Node.js 20+
- Python 3.12+
- Make

```bash
# Clone
git clone https://github.com/Sekiph82/Bulk-Edit.git
cd Bulk-Edit

# Copy env
cp .env.example .env
# Fill in your credentials

# Start all services
make dev
```

## Repo Workflow

- Main branch: `main`
- Commit format: `feat:`, `fix:`, `chore:`, `docs:`
- Push after every sprint checkpoint
- See `CLAUDE.md` for full GitHub sync policy

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 + Celery |
| Auth | JWT + Etsy OAuth2 |
| Billing | Stripe |
| Storage | S3-compatible |
| AI | OpenAI + Anthropic |

## Documentation

- `ARCHITECTURE.md` — system design
- `DECISIONS.md` — architectural decisions
- `docs/product/` — product requirements and features
- `docs/technical/` — database schema, API spec, integrations
- `docs/operations/` — deployment and testing
