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

## Local Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

### Run with Docker Compose (recommended)

```bash
# Clone
git clone https://github.com/Sekiph82/Bulk-Edit.git
cd Bulk-Edit

# Copy and configure environment
cp .env.example .env
# Edit .env if needed (defaults work for local dev)

# Start all services (frontend, backend, postgres, redis)
docker compose up --build

# In a separate terminal, run database migrations
docker compose exec backend alembic upgrade head
```

Services:
| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| DB Health | http://localhost:8000/api/v1/health/db |
| Redis Health | http://localhost:8000/api/v1/health/redis |

### Run Backend Locally (without Docker)

```bash
cd apps/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements-dev.txt

# Copy env
cp .env.example .env
# Edit DATABASE_URL and REDIS_URL to use localhost

# Run migrations (requires running PostgreSQL)
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

### Run Frontend Locally (without Docker)

```bash
cd apps/frontend

npm install

# Copy env
cp .env.local.example .env.local

npm run dev
# Open http://localhost:3000
```

### Run Backend Tests

```bash
# Via Docker
docker compose exec backend pytest --tb=short -q

# Locally
cd apps/backend
pip install -r requirements-dev.txt
pytest --tb=short -q
```

### Makefile Commands

```bash
make dev          # Start all services
make stop         # Stop all services
make clean        # Stop and delete volumes
make migrate      # Run migrations
make rollback     # Rollback last migration
make test         # Run all tests
make health       # Check API health
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
