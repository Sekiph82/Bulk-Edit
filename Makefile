# Bulk-Edit Makefile
# Works with GNU Make on Linux/Mac.
# Windows: install Make via `winget install GnuWin32.Make` or use `docker compose` commands directly.

.PHONY: dev stop build migrate rollback test test-backend lint type-check logs clean

## Start all services in development mode
dev:
	docker compose up --build

## Start services detached (background)
dev-d:
	docker compose up --build -d

## Stop all services
stop:
	docker compose down

## Stop and remove volumes (WARNING: deletes all DB data)
clean:
	docker compose down -v

## Run Alembic migrations inside the backend container
migrate:
	docker compose exec backend alembic upgrade head

## Rollback last Alembic migration
rollback:
	docker compose exec backend alembic downgrade -1

## Generate a new Alembic migration (usage: make migration MSG="add users table")
migration:
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

## Run backend tests
test-backend:
	docker compose exec backend pytest --tb=short -q

## Run backend tests locally (requires local Python venv)
test-backend-local:
	cd apps/backend && python -m pytest --tb=short -q

## Run all tests
test: test-backend

## Lint backend
lint-backend:
	docker compose exec backend python -m ruff check app/

## Type-check frontend
type-check:
	docker compose exec frontend npm run type-check

## Show logs for all services
logs:
	docker compose logs -f

## Show backend logs
logs-backend:
	docker compose logs -f backend

## Show frontend logs
logs-frontend:
	docker compose logs -f frontend

## Open a shell in the backend container
shell-backend:
	docker compose exec backend bash

## Open a shell in the frontend container
shell-frontend:
	docker compose exec frontend sh

## Check backend health
health:
	curl -s http://localhost:8000/api/v1/health | python -m json.tool

## Check DB health
health-db:
	curl -s http://localhost:8000/api/v1/health/db | python -m json.tool

## Check Redis health
health-redis:
	curl -s http://localhost:8000/api/v1/health/redis | python -m json.tool
