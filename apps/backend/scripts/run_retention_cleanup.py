#!/usr/bin/env python3
"""
Delete backup snapshots / CSV jobs past their 30-day retention window.
See ETSY_DATA_RETENTION.md for the policy.

Run inside the Docker backend container:
  docker compose exec backend python scripts/run_retention_cleanup.py

Intended to be invoked on a schedule (cron, DO App Platform scheduled job)
until a real Celery worker exists — no background loop here.
"""
import asyncio
import sys
from pathlib import Path

_script_dir = Path(__file__).parent
_backend_root = _script_dir.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

import app.models

assert app.models  # import is for its side effect: registers all ORM models on Base.metadata before first use

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.services.retention_cleanup import delete_expired_snapshots  # noqa: E402


async def main() -> None:
    async with AsyncSessionLocal() as db:
        counts = await delete_expired_snapshots(db)
    total = sum(counts.values())
    print(f"\nRetention cleanup complete — {total} row(s) deleted:\n")
    for table, count in counts.items():
        print(f"  {table}: {count}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
