"""
Deletes expired Etsy-derived snapshot/job data past its retention window.
See ETSY_DATA_RETENTION.md for the policy this enforces (30-day cap).

Not wired to a live worker — no Celery worker is deployed yet (see
PROJECT_STATUS.md / docs/operations/WORKERS.md). Invoke via
scripts/run_retention_cleanup.py on an external scheduler (cron, DO App
Platform scheduled job, etc.) until a real worker exists.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_backup_snapshot import ListingBackupSnapshot
from app.models.listing_media_backup_snapshot import ListingMediaBackupSnapshot
from app.models.listing_variation_backup_snapshot import ListingVariationBackupSnapshot
from app.models.csv_job import CSVJob

# Single source of truth for which tables retention cleanup covers — used by
# both the real delete and the read-only dry-run count so they can never drift.
_RETENTION_MODELS = (
    ListingBackupSnapshot,
    ListingMediaBackupSnapshot,
    ListingVariationBackupSnapshot,
    CSVJob,
)


async def count_expired_snapshots(db: AsyncSession) -> dict[str, int]:
    """Read-only preview of delete_expired_snapshots: same WHERE clause, no writes."""
    now = datetime.now(timezone.utc)
    counts: dict[str, int] = {}
    for model in _RETENTION_MODELS:
        result = await db.execute(
            select(func.count()).select_from(model).where(model.expires_at < now)
        )
        counts[model.__tablename__] = result.scalar_one()
    return counts


async def delete_expired_snapshots(db: AsyncSession) -> dict[str, int]:
    """Deletes all rows whose expires_at has passed. Returns per-table delete counts."""
    now = datetime.now(timezone.utc)
    counts: dict[str, int] = {}
    for model in _RETENTION_MODELS:
        result = await db.execute(delete(model).where(model.expires_at < now))
        counts[model.__tablename__] = result.rowcount or 0
    await db.commit()
    return counts
