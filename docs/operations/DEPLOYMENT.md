# Deployment

## Port Configuration

Custom host ports are used to avoid conflicts with other local projects:

| Service | Host Port | Container Port | Mapping |
|---|---|---|---|
| Frontend | 3100 | 3000 | 3100:3000 |
| Backend | 8100 | 8000 | 8100:8000 |
| PostgreSQL | 55432 | 5432 | 55432:5432 |
| Redis | 56379 | 6379 | 56379:6379 |

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
7. Safely stops old ERP project: `docker compose -p fmcg-erp-system-main down --remove-orphans` (silenced — does not stop script, no `-v` so ERP volumes preserved)
8. Runs `docker compose -p bulk-edit down --remove-orphans` (clean: adds `-v`)
9. Runs `docker compose -p bulk-edit up --build` (foreground, streams logs)
10. Keeps CMD window open with `pause` after Docker exits

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
| PostgreSQL | localhost:55432 |
| Redis | localhost:56379 |

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
cp .env.example .env         # uses localhost:55432 and localhost:56379
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

## Production Deployment (Planned — Sprint 18)

Target: Railway, Render, or AWS ECS

Production checklist:
- `ENVIRONMENT=production`
- `DEBUG=false`
- SSL configured
- Production PostgreSQL (managed — RDS, Neon, Supabase, etc.)
- Production Redis (Upstash or ElastiCache)
- Production S3 (AWS S3 or Cloudflare R2)
- Stripe live keys configured
- Sentry DSN configured
- Rate limiting enabled

Standard ports (80/443) used in production — custom ports are local dev only.

---

## CI/CD (Planned — Sprint 18)

GitHub Actions workflows:
- On push to `main`: run tests, build Docker images
- On tag `v*.*.*`: deploy to production
