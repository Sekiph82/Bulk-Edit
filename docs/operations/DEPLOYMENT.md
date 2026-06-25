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
