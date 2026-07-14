#!/usr/bin/env python3
"""
Delete backup snapshots / CSV jobs past their 30-day retention window.
See ETSY_DATA_RETENTION.md for the policy.

Run inside the Docker backend container:
  docker compose exec backend python scripts/run_retention_cleanup.py

Preview what would be deleted, with no writes, using --dry-run:
  docker compose exec backend python scripts/run_retention_cleanup.py --dry-run

Intended to be invoked on a schedule (cron, DO App Platform scheduled job)
until a real Celery worker exists — no background loop here.
"""
import argparse
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
from app.services.retention_cleanup import count_expired_snapshots, delete_expired_snapshots  # noqa: E402


async def main(dry_run: bool) -> None:
    async with AsyncSessionLocal() as db:
        if dry_run:
            counts = await count_expired_snapshots(db)
        else:
            counts = await delete_expired_snapshots(db)
    total = sum(counts.values())

    if dry_run:
        print("\nRetention cleanup dry run\n")
        for table, count in counts.items():
            print(f"{table}: {count}")
        print(f"\ntotal_expired_candidates: {total}\n")
        print("No data was deleted.\n")
    else:
        print(f"\nRetention cleanup complete — {total} row(s) deleted:\n")
        for table, count in counts.items():
            print(f"  {table}: {count}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report expired-row counts per table without deleting anything.",
    )
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))
