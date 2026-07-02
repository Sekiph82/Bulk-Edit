#!/bin/sh
# Production start script (Render / any container host).
# Runs DB migrations, then starts the API. Binds to the platform-provided
# $PORT (Render sets it) and falls back to 8000 for plain Docker.
#
# Local dev is unaffected: docker-compose.yml overrides `command:` with its own
# uvicorn --reload invocation, so this script only runs in real deployments.
set -e

PORT="${PORT:-8000}"

# Apply migrations with a short retry — a freshly-provisioned managed DB can be
# briefly unreachable at first boot. Fail the deploy if it never comes up.
n=0
until alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 5 ]; then
    echo "alembic upgrade head failed after $n attempts" >&2
    exit 1
  fi
  echo "migrations failed (attempt $n) — DB not ready yet, retrying in 5s..." >&2
  sleep 5
done

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
