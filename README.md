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

**Sprint 1 — Monorepo Skeleton** (Complete)

Next: Sprint 2 — Auth + Organization

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

> **Port note:** This project uses custom host ports to avoid conflicts with other local services.

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
# Defaults work for local Docker Compose dev

# Start all services (frontend, backend, postgres, redis)
docker compose up --build

# In a separate terminal, run database migrations
docker compose exec backend alembic upgrade head
```

Services:

| Service | Host URL | Notes |
|---|---|---|
| Frontend | http://localhost:3100 | Host port 3100 → container 3000 |
| Backend API | http://localhost:8100 | Host port 8100 → container 8000 |
| API Docs | http://localhost:8100/docs | Swagger UI |
| Health | http://localhost:8100/api/v1/health | Liveness |
| DB Health | http://localhost:8100/api/v1/health/db | PostgreSQL |
| Redis Health | http://localhost:8100/api/v1/health/redis | Redis |
| PostgreSQL | localhost:55432 | Host port 55432 → container 5432 |
| Redis | localhost:56379 | Host port 56379 → container 6379 |

### Run Backend Locally (without Docker)

```bash
cd apps/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements-dev.txt

# Copy env (local dev uses host-mapped ports 55432 / 56379)
cp .env.example .env

# Run migrations (requires running PostgreSQL on port 55432)
alembic upgrade head

# Start backend on port 8100
uvicorn app.main:app --reload --port 8100
```

### Run Frontend Locally (without Docker)

```bash
cd apps/frontend

npm install

# Copy env
cp .env.local.example .env.local

# Starts on port 3100 by default via Next.js -p flag, or set PORT=3100
npm run dev -- -p 3100
# Open http://localhost:3100
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
make dev           # Start all services (docker compose up --build)
make dev-d         # Start detached
make stop          # Stop all services
make clean         # Stop and delete volumes (destroys DB data)
make migrate       # Run Alembic migrations
make rollback      # Rollback last migration
make test          # Run all tests
make health        # GET http://localhost:8100/api/v1/health
make health-db     # GET http://localhost:8100/api/v1/health/db
make health-redis  # GET http://localhost:8100/api/v1/health/redis
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
