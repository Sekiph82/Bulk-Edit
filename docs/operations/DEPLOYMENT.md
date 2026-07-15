# Deployment

## Port Configuration

Custom host ports are used to avoid conflicts with other local projects:

| Service | Host Port | Container Port | Mapping |
|---|---|---|---|
| Frontend | 3100 | 3000 | 3100:3000 |
| Backend | 8100 | 8000 | 8100:8000 |
| PostgreSQL | internal only | 5432 | not exposed by default |
| Redis | internal only | 6379 | not exposed by default |

PostgreSQL and Redis communicate with the backend through Docker's internal network only.
They are not exposed to the Windows host by default, which prevents port-binding conflicts
with Hyper-V/WSL2 reserved port ranges.

To expose DB/Redis on host ports for direct access (pgAdmin, TablePlus, Redis Insight):

```bash
docker compose -p bulk-edit -f docker-compose.yml -f docker-compose.dev-ports.yml up -d
```

See `docker-compose.dev-ports.yml` for configurable `POSTGRES_HOST_PORT` / `REDIS_HOST_PORT`.

---

## Local Development

Requirements:
- Docker Desktop (includes Docker Compose)
- Git

### Windows One-Click Setup (for a friend / reviewer)

For someone who may not have developer tools installed. Requires Windows 10/11 with `winget` (App Installer — available in Microsoft Store).

| File | Purpose |
|---|---|
| `setup-and-start.bat` | Full friend setup: installs Git + Docker Desktop if missing, clones or pulls repo, creates `.env`, builds, starts, opens browser. Keeps volumes (data preserved). |
| `setup-and-start-clean.bat` | Same as above, but destroys local DB volumes. Requires typing `YES` to confirm. |

**What the friend does:**
1. Receive the `setup-and-start.bat` file (or clone the repo and navigate to it).
2. Double-click `setup-and-start.bat`.
3. The script handles everything — tool install, clone, build, start.
4. Browser opens automatically at `http://localhost:3100`.

**Docker Desktop first-install warning:**
Docker Desktop requires WSL2 and may prompt for a Windows restart on first install.
If Docker does not start after install, restart the computer and double-click the script again.

### Windows Startup Scripts (for developers — already cloned)

| File | Purpose |
|---|---|
| `start-dev.bat` | Normal startup: stops old containers, rebuilds, streams logs. Keeps volumes (data preserved). |
| `start-dev-clean.bat` | Full reset: removes containers **and volumes** (destroys DB data), rebuilds from scratch. Asks for confirmation. |

Double-click either file in Explorer — no terminal needed. The script:
1. Checks Docker CLI installed (clear error if not)
2. Starts Docker Desktop automatically: `start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"`
3. Polls `docker info` every 5 seconds until Docker engine is ready (max 180 seconds, then exits with clear error)
4. Checks `docker compose version` (clear error if not)
5. Copies `.env.example` → `.env` if `.env` is missing
6. Appends `COMPOSE_PROJECT_NAME=bulk-edit` to `.env` if not present
7. Runs `docker compose -p bulk-edit down --remove-orphans` (clean: adds `-v` for clean reset)
8. Runs `docker compose -p bulk-edit up --build` (detached, then health-polls before opening browser)
9. Opens browser at http://localhost:3100 once frontend is ready

All scripts use `docker compose -p bulk-edit` for project isolation. User never needs to open Docker Desktop manually.

All .bat files are plain ASCII-only CMD batch files. No Unicode characters, no UTF-8 encoding, no `chcp 65001`. Safe to double-click on any Windows 10/11 system without encoding errors.

### Docker Compose (manual / Mac / Linux)

```bash
# Clone repo
git clone https://github.com/Sekiph82/Bulk-Edit.git
cd Bulk-Edit

# Configure environment
cp .env.example .env
# Defaults work for local Docker Compose dev

# Start all services
docker compose up --build
# OR: make dev

# Run DB migrations (in another terminal)
docker compose exec backend alembic upgrade head
# OR: make migrate
```

Services:

| Service | URL |
|---|---|
| Frontend | http://localhost:3100 |
| Backend | http://localhost:8100 |
| API Docs | http://localhost:8100/docs |
| Health | http://localhost:8100/api/v1/health |
| DB Health | http://localhost:8100/api/v1/health/db |
| Redis Health | http://localhost:8100/api/v1/health/redis |
| PostgreSQL | internal Docker (not exposed to host) |
| Redis | internal Docker (not exposed to host) |

### Makefile Commands

```bash
make dev           # docker compose up --build
make dev-d         # docker compose up --build -d (detached)
make stop          # docker compose down
make clean         # docker compose down -v (destroys DB data)
make migrate       # alembic upgrade head
make rollback      # alembic downgrade -1
make test          # run all tests
make health        # curl http://localhost:8100/api/v1/health
make health-db     # curl http://localhost:8100/api/v1/health/db
make health-redis  # curl http://localhost:8100/api/v1/health/redis
```

### Backend Local (without Docker)

```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements-dev.txt
cp .env.example .env         # postgres/redis accessed via Docker internal network
alembic upgrade head
uvicorn app.main:app --reload --port 8100
```

### Frontend Local (without Docker)

```bash
cd apps/frontend
npm install
cp .env.local.example .env.local
npm run dev -- -p 3100
# http://localhost:3100
```

---

## Production Deployment

Production domain: **bulkeditapp.com**. See `docs/operations/DNS_SSL.md` for DNS/SSL/callback
details and `docs/operations/LAUNCH_CHECKLIST.md` for the go-live checklist.

### Domain model

| Role | URL |
|---|---|
| Marketing site | `https://bulkeditapp.com` (and `https://www.bulkeditapp.com`) |
| Application | `https://app.bulkeditapp.com` (Private Beta gated for new sign-ups) |
| Backend API | `https://api.bulkeditapp.com` |

### Chosen hosting: DigitalOcean App Platform + Cloudflare

Production hosting is **DigitalOcean App Platform** (`bulk-edit-prod-api`, `bulk-edit-prod-web`) +
**Cloudflare** (DNS/TLS). Full walkthrough — app specs, env vars, custom domains, scheduled jobs — in
[`DIGITALOCEAN_DEPLOY.md`](DIGITALOCEAN_DEPLOY.md) and [`CLOUDFLARE_DNS.md`](CLOUDFLARE_DNS.md).
The original Vercel + Render plan ([`VERCEL_RENDER_DEPLOY.md`](VERCEL_RENDER_DEPLOY.md), [`PRODUCTION_SMOKE_TEST.md`](PRODUCTION_SMOKE_TEST.md))
was superseded before it was ever provisioned in production and is kept only as historical reference — see `DECISIONS.md`.
The stack stays provider-agnostic in code; the section below documents the neutral requirements.

### Provider (neutral — not chosen in code)

The stack is provider-agnostic; nothing hardcodes a host or provider.

- **Frontend**: any Next.js host — Vercel or similar.
- **Backend**: Render / Fly.io / Railway / DigitalOcean / AWS (container or app service).
- **PostgreSQL & Redis**: managed production services (RDS/Neon/Supabase; Upstash/ElastiCache).
  Local Docker Postgres/Redis are **not** production infrastructure.
- HTTPS only. Standard ports (80/443) in production — custom `3100`/`8100` are local dev only.

### Production env checklist

- `ENVIRONMENT=production`
- `DEBUG=false`
- `FRONTEND_URL=https://www.bulkeditapp.com`
- `BACKEND_URL=https://api.bulkeditapp.com`
- `NEXT_PUBLIC_APP_URL=https://www.bulkeditapp.com`
- `NEXT_PUBLIC_BACKEND_URL=https://api.bulkeditapp.com`
- `BACKEND_CORS_ORIGINS=https://www.bulkeditapp.com,https://bulkeditapp.com`
- SSL certificates active for `www` and `api`
- Production PostgreSQL (managed — RDS, Neon, Supabase, etc.)
- Production Redis (Upstash or ElastiCache)
- Production S3 (AWS S3 or Cloudflare R2)
- Stripe live keys + webhook `https://api.bulkeditapp.com/api/v1/billing/webhook`
- OAuth callbacks registered on `api.bulkeditapp.com` (Etsy/Pinterest/Instagram — see DNS_SSL.md)
- Sentry DSN configured
- Rate limiting enabled (`RATE_LIMIT_ENABLED=true`, `RATE_LIMIT_BACKEND=redis`)

---

## CI/CD (Planned — Sprint 18)

GitHub Actions workflows:
- On push to `main`: run tests, build Docker images
- On tag `v*.*.*`: deploy to production
