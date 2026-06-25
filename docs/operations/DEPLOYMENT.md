# Deployment

## Local Development

Requirements:
- Docker and Docker Compose
- Node.js 20+
- Python 3.12+
- Make

```bash
cp .env.example .env
# Edit .env with real credentials

make dev        # Start all services
make migrate    # Run Alembic migrations
make seed       # (future) Seed dev data
```

Services started by `make dev`:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- MinIO: http://localhost:9000
- Celery worker
- Celery Beat (scheduler)

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
