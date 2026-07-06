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

### Docker project isolation and startup readiness

All Windows scripts are plain ASCII-only CMD-safe batch files (no Unicode, no UTF-8, no chcp). They work reliably when double-clicked on any Windows 10/11 system.

Scripts automatically start Docker Desktop if it is closed. Each script polls `docker info` every 5 seconds (up to 180 seconds) and only proceeds once the Docker engine is ready.

After containers start, scripts poll the backend health endpoint (`http://localhost:8100/api/v1/health`) and the frontend (`http://localhost:3100`) before opening the browser. The browser only opens once both services are confirmed ready. If either service fails to respond within 180 seconds, the browser does NOT open and the script prints troubleshooting instructions.

All scripts force Docker Compose project name to `bulk-edit` via `docker compose -p bulk-edit` to prevent accidentally interfering with other Docker projects.

### Windows one-click setup

No developer tools required. Only Docker Desktop is needed — the script installs it automatically if missing.

**Steps:**

1. Download or clone this repo to any folder on your computer.
2. Double-click `setup-and-start.bat`.
3. If Docker Desktop is not installed, the script installs it automatically (may ask for admin/UAC approval — click **Yes**). A Windows restart may be required after Docker installs.
4. After restart, double-click `setup-and-start.bat` again.
5. Wait while Docker builds and starts all services (first run: 5–10 minutes).
6. The browser opens automatically at http://localhost:3100.

**Local demo accounts:**

Local demo users can be seeded for development only. Credentials are generated or
configured locally and are never documented in the public README. See
`apps/backend/.local-superusers.env.example` and the local seed scripts
(`apps/backend/app/services/local_seed.py`, `apps/backend/scripts/seed_local_superusers.py`)
for setup — copy the example file to a gitignored `.local-superusers.env` and set your own
local credentials there.

Demo accounts are seeded only in local Docker development. They are never seeded in
staging or production, and secrets/passwords must always be configured through
gitignored local env files, never committed or documented in this README.

**What the script does automatically:**

- Installs Docker Desktop via winget if missing (or opens download page if winget unavailable)
- Starts Docker Desktop if installed but not running
- Creates `.env` from `.env.example` if missing (existing `.env` is never overwritten)
- Appends safe placeholder values for video/social integrations (does not overwrite real values)
- Creates demo seed accounts so login works immediately
- Builds and starts all services via Docker Compose
- Waits for backend health, database readiness, and frontend
- Opens http://localhost:3100 in the browser

**What's not included:**

- No real Etsy, Pinterest, Instagram, Stripe, or email credentials — placeholders only
- Social integrations (Pinterest, Instagram) and Video Generator require real credentials to be configured in `.env`
- See `docs/operations/PROVIDER_SETUP.md` for setup guides

> **Note:** Docker Desktop may require a Windows restart on first install (WSL2 setup). After restarting, double-click `setup-and-start.bat` again — it picks up where it left off.

Need a full database reset?

```
Double-click  setup-and-start-clean.bat
(Asks for YES confirmation before deleting volumes — destroys all local DB data.)
```

### Windows Quick Start (for developers — already have Docker)

```
1. Clone the repo and open the folder in Explorer.
2. Double-click  start-dev.bat
3. The script checks Docker, creates .env from .env.example if missing,
   stops any old containers, rebuilds services detached, waits for health,
   optionally runs the local superuser seed, opens the browser, then streams logs.
4. Press Ctrl+C to stop log streaming (services keep running).
5. To stop all services: docker compose -p bulk-edit down
```

Need a full reset (wipes local database)?

```
Double-click  start-dev-clean.bat
(Asks for confirmation before deleting volumes.)
```

### Local Demo Superusers (optional, gitignored)

To seed local demo accounts without any Stripe setup:

```
1. Copy:  apps/backend/.local-superusers.env.example
      to: apps/backend/.local-superusers.env

2. Edit apps/backend/.local-superusers.env with your local-only credentials.
   This file is gitignored and never committed.

3. Start services (start-dev.bat or docker compose up).

4. Run the seed (inside the Docker backend container):
   docker compose exec backend python scripts/seed_local_superusers.py

   Or when prompted by start-dev.bat after services are ready: type Y.

5. Login at http://localhost:3100 with the email/password from your local file.
```

Two demo users are created:
- Free plan superuser (plan: free, all free-tier gates apply)
- Paid/Pro plan superuser (plan: pro_monthly, all paid features unlocked including AI Tools and Dynamic Pricing)

The seed is idempotent — safe to run multiple times. Passwords are never printed or logged.

### Run with Docker Compose (manual / Mac / Linux)

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
| PostgreSQL | internal Docker only | Not exposed to host by default |
| Redis | internal Docker only | Not exposed to host by default |

> PostgreSQL and Redis run inside Docker and are not exposed to Windows by default.
> Developers who need direct DB/Redis access can use `docker-compose.dev-ports.yml`.

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
# For direct host DB access, also start: docker compose -f docker-compose.yml -f docker-compose.dev-ports.yml up -d

# Run migrations (postgres must be running via Docker Compose)
# docker compose -p bulk-edit exec backend alembic upgrade head
# Or with dev-ports overlay active:
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
