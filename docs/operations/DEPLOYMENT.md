# Deployment

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
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### Makefile Commands

```bash
make dev          # docker compose up --build
make dev-d        # docker compose up --build -d (detached)
make stop         # docker compose down
make clean        # docker compose down -v (destroys DB data)
make migrate      # alembic upgrade head
make rollback     # alembic downgrade -1
make test         # run all tests
make health       # curl /api/v1/health
make health-db    # curl /api/v1/health/db
make health-redis # curl /api/v1/health/redis
```

### Backend Local (without Docker)

```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements-dev.txt
cp .env.example .env         # edit DATABASE_URL/REDIS_URL to localhost
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend Local (without Docker)

```bash
cd apps/frontend
npm install
cp .env.local.example .env.local
npm run dev
# http://localhost:3000
```

## Docker Compose Services

```yaml
services:
  frontend:    # Next.js on port 3000
  backend:     # FastAPI on port 8000
  db:          # PostgreSQL on port 5432
  redis:       # Redis on port 6379
  minio:       # MinIO on port 9000
  worker:      # Celery worker
  beat:        # Celery Beat
```

## Production Deployment (Planned — Sprint 18)

Target: Railway, Render, or AWS ECS

Required environment variables: see `.env.example`

Production checklist:
- `ENVIRONMENT=production`
- `DEBUG=false`
- SSL configured
- Proper domain and CORS origins
- Production PostgreSQL (managed — RDS, Neon, Supabase, etc.)
- Production Redis (Upstash or ElastiCache)
- Production S3 (AWS S3 or Cloudflare R2)
- Stripe live keys configured
- Sentry DSN configured
- Rate limiting enabled

## CI/CD (Planned — Sprint 18)

GitHub Actions workflows:
- On push to `main`: run tests, build Docker images
- On tag `v*.*.*`: deploy to production

## Makefile Commands

```
make dev         Start all services (docker compose up)
make stop        Stop all services
make migrate     Run Alembic migrations
make rollback    Rollback last migration
make test        Run all tests
make lint        Run linters
make build       Build production images
```
