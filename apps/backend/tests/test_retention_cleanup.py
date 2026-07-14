"""
Tests for the Etsy-derived data retention cleanup service and CLI script.

Covers: app/services/retention_cleanup.py (count_expired_snapshots,
delete_expired_snapshots) and scripts/run_retention_cleanup.py (--dry-run).

Scope under test is exactly the 4 tables the 30-day retention window
applies to: listing_backup_snapshots, listing_media_backup_snapshots,
listing_variation_backup_snapshots, csv_jobs. See ETSY_DATA_RETENTION.md.
"""
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.models.organization import Organization
from app.models.user import User
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.listing_backup_snapshot import ListingBackupSnapshot
from app.models.listing_media_backup_snapshot import ListingMediaBackupSnapshot
from app.models.listing_variation_backup_snapshot import ListingVariationBackupSnapshot
from app.models.csv_job import CSVJob
from app.services.retention_cleanup import count_expired_snapshots, delete_expired_snapshots

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _id() -> str:
    return str(uuid.uuid4())


async def _make_org(db) -> Organization:
    from app.core.security import hash_password

    owner = User(id=_id(), email=f"retention-{_id()}@example.com", password_hash=hash_password("Test1234!"))
    db.add(owner)
    await db.flush()
    org = Organization(id=_id(), name=f"Org-{_id()[:8]}", owner_id=owner.id)
    db.add(org)
    await db.flush()
    return org


async def _make_shop(db, org: Organization) -> EtsyShop:
    shop = EtsyShop(id=_id(), organization_id=org.id, etsy_shop_id=f"shop-{_id()[:8]}", shop_name="Test Shop", is_connected=True)
    db.add(shop)
    await db.flush()
    return shop


async def _make_listing(db, org: Organization, shop: EtsyShop) -> Listing:
    listing = Listing(id=_id(), organization_id=org.id, etsy_shop_id=shop.id, etsy_listing_id=f"L-{_id()[:8]}")
    db.add(listing)
    await db.flush()
    return listing


async def _seed_one_expired_one_unexpired(db) -> dict:
    """Creates exactly 1 expired + 1 unexpired row in each of the 4 retention tables.

    Returns the ids of every row created, keyed table -> {"expired": id, "unexpired": id}.
    """
    org = await _make_org(db)
    shop = await _make_shop(db, org)
    listing = await _make_listing(db, org, shop)

    expired_at = datetime.now(timezone.utc) - timedelta(days=1)
    future_at = datetime.now(timezone.utc) + timedelta(days=10)

    ids: dict[str, dict[str, str]] = {}

    snap_expired = ListingBackupSnapshot(
        id=_id(), expires_at=expired_at, organization_id=org.id, listing_id=listing.id,
        etsy_shop_id=shop.id, etsy_listing_id=listing.etsy_listing_id, snapshot_data={},
    )
    snap_unexpired = ListingBackupSnapshot(
        id=_id(), expires_at=future_at, organization_id=org.id, listing_id=listing.id,
        etsy_shop_id=shop.id, etsy_listing_id=listing.etsy_listing_id, snapshot_data={},
    )
    db.add_all([snap_expired, snap_unexpired])
    ids["listing_backup_snapshots"] = {"expired": snap_expired.id, "unexpired": snap_unexpired.id}

    media_expired = ListingMediaBackupSnapshot(
        id=_id(), expires_at=expired_at, organization_id=org.id, listing_id=listing.id,
        etsy_shop_id=shop.id, etsy_listing_id=listing.etsy_listing_id,
    )
    media_unexpired = ListingMediaBackupSnapshot(
        id=_id(), expires_at=future_at, organization_id=org.id, listing_id=listing.id,
        etsy_shop_id=shop.id, etsy_listing_id=listing.etsy_listing_id,
    )
    db.add_all([media_expired, media_unexpired])
    ids["listing_media_backup_snapshots"] = {"expired": media_expired.id, "unexpired": media_unexpired.id}

    var_expired = ListingVariationBackupSnapshot(
        id=_id(), expires_at=expired_at, organization_id=org.id, listing_id=listing.id,
        etsy_shop_id=shop.id, etsy_listing_id=listing.etsy_listing_id,
    )
    var_unexpired = ListingVariationBackupSnapshot(
        id=_id(), expires_at=future_at, organization_id=org.id, listing_id=listing.id,
        etsy_shop_id=shop.id, etsy_listing_id=listing.etsy_listing_id,
    )
    db.add_all([var_expired, var_unexpired])
    ids["listing_variation_backup_snapshots"] = {"expired": var_expired.id, "unexpired": var_unexpired.id}

    csv_expired = CSVJob(id=_id(), expires_at=expired_at, organization_id=org.id, job_type="listings_import")
    csv_unexpired = CSVJob(id=_id(), expires_at=future_at, organization_id=org.id, job_type="listings_import")
    db.add_all([csv_expired, csv_unexpired])
    ids["csv_jobs"] = {"expired": csv_expired.id, "unexpired": csv_unexpired.id}

    await db.commit()
    return ids


_TABLES = (
    "listing_backup_snapshots",
    "listing_media_backup_snapshots",
    "listing_variation_backup_snapshots",
    "csv_jobs",
)


async def test_dry_run_finds_expired_records(db_session):
    await _seed_one_expired_one_unexpired(db_session)
    counts = await count_expired_snapshots(db_session)
    assert counts == {t: 1 for t in _TABLES}
    assert sum(counts.values()) == 4


async def test_dry_run_does_not_delete_expired_records(db_session):
    ids = await _seed_one_expired_one_unexpired(db_session)
    await count_expired_snapshots(db_session)

    result = await db_session.execute(select(ListingBackupSnapshot.id).where(ListingBackupSnapshot.id == ids["listing_backup_snapshots"]["expired"]))
    assert result.scalar_one_or_none() is not None
    result = await db_session.execute(select(CSVJob.id).where(CSVJob.id == ids["csv_jobs"]["expired"]))
    assert result.scalar_one_or_none() is not None


async def test_dry_run_does_not_modify_unexpired_records(db_session):
    ids = await _seed_one_expired_one_unexpired(db_session)
    await count_expired_snapshots(db_session)

    row = await db_session.get(ListingMediaBackupSnapshot, ids["listing_media_backup_snapshots"]["unexpired"])
    assert row is not None
    # SQLite (test DB) returns naive datetimes even for tz-aware columns; strip tzinfo before comparing.
    stored = row.expires_at.replace(tzinfo=None) if row.expires_at.tzinfo else row.expires_at
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    assert stored > now_naive


async def test_normal_cleanup_deletes_expired_records(db_session):
    ids = await _seed_one_expired_one_unexpired(db_session)
    counts = await delete_expired_snapshots(db_session)
    assert counts == {t: 1 for t in _TABLES}

    result = await db_session.execute(select(ListingVariationBackupSnapshot.id).where(ListingVariationBackupSnapshot.id == ids["listing_variation_backup_snapshots"]["expired"]))
    assert result.scalar_one_or_none() is None


async def test_normal_cleanup_preserves_unexpired_records(db_session):
    ids = await _seed_one_expired_one_unexpired(db_session)
    await delete_expired_snapshots(db_session)

    for table_model, key in (
        (ListingBackupSnapshot, "listing_backup_snapshots"),
        (ListingMediaBackupSnapshot, "listing_media_backup_snapshots"),
        (ListingVariationBackupSnapshot, "listing_variation_backup_snapshots"),
        (CSVJob, "csv_jobs"),
    ):
        row = await db_session.get(table_model, ids[key]["unexpired"])
        assert row is not None, f"{key} unexpired row was incorrectly deleted"


async def test_cleanup_is_idempotent(db_session):
    await _seed_one_expired_one_unexpired(db_session)
    first = await delete_expired_snapshots(db_session)
    assert sum(first.values()) == 4

    second = await delete_expired_snapshots(db_session)
    assert second == {t: 0 for t in _TABLES}


def test_database_failure_exits_nonzero():
    """The CLI script must exit non-zero (not swallow the error) when the DB is unreachable."""
    env = {
        **__import__("os").environ,
        "DATABASE_URL": "postgresql+asyncpg://baduser:badpass@127.0.0.1:1/baddb",
        "ENCRYPTION_KEY": "uOv7K6PYL6v4G77O0WqJrA5BrM42x3NCAQZUSO2rTio=",
    }
    result = subprocess.run(
        [sys.executable, "scripts/run_retention_cleanup.py", "--dry-run"],
        cwd=str(_BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
