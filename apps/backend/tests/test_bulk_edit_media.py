"""
Sprint 11 tests: bulk media edit jobs, results, backup snapshots, org isolation.

All Etsy write functions are mocked — no real API calls.
settings.is_etsy_configured() is patched to True where needed.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.models.listing_image import ListingImage

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
JOBS_URL = "/api/v1/bulk-edit/media/jobs"


# ── helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(client, user: dict) -> str:
    await client.post(REGISTER_URL, json=user)
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    return result.scalar_one().organization_id


async def _setup_listing_with_token(db_session, org_id: str, etsy_id: str = "11001"):
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"media_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(
            organization_id=org_id,
            etsy_shop_id=shop_etsy_id,
            shop_name="Media Shop",
            is_connected=True,
        )
        db_session.add(shop)
        await db_session.flush()
        token = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake_media_token"),
            refresh_token_enc=encrypt_token("fake_r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scopes="listings_r listings_w",
        )
        db_session.add(token)
        await db_session.flush()

    listing = Listing(
        organization_id=org_id,
        etsy_shop_id=shop.id,
        etsy_listing_id=etsy_id,
        title=f"Media Test Listing {etsy_id}",
        state="active",
        price_amount=1500,
        quantity=2,
    )
    db_session.add(listing)
    await db_session.commit()
    return listing, shop


async def _add_listing_image(db_session, listing, etsy_image_id: str = "IMG001", rank: int = 1):
    img = ListingImage(
        listing_id=listing.id,
        etsy_image_id=etsy_image_id,
        rank=rank,
        url_fullxfull=f"https://example.com/img/{etsy_image_id}.jpg",
    )
    db_session.add(img)
    await db_session.commit()
    return img


def _etsy_settings_mock():
    m = MagicMock()
    m.is_etsy_configured.return_value = True
    return m


# ── auth gate ─────────────────────────────────────────────────────────────────

async def test_create_media_job_requires_auth(client, db_session):
    r = await client.post(JOBS_URL, json={
        "listing_ids": ["fake-id"],
        "operation_type": "add_image",
        "payload": {},
    })
    assert r.status_code in (401, 403)


async def test_list_media_jobs_requires_auth(client, db_session):
    r = await client.get(JOBS_URL)
    assert r.status_code in (401, 403)


# ── validation ────────────────────────────────────────────────────────────────

async def test_create_media_job_rejects_empty_listing_ids(client, db_session):
    token = await _register_and_login(client, {
        "email": "mv1@example.com", "password": "password123",
        "full_name": "V1", "organization_name": "MV1 Org",
    })
    r = await client.post(JOBS_URL, json={
        "listing_ids": [],
        "operation_type": "add_image",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


async def test_create_media_job_rejects_unknown_operation(client, db_session):
    token = await _register_and_login(client, {
        "email": "mv2@example.com", "password": "password123",
        "full_name": "V2", "organization_name": "MV2 Org",
    })
    r = await client.post(JOBS_URL, json={
        "listing_ids": ["fake-id"],
        "operation_type": "delete_everything",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


async def test_create_media_job_rejects_cross_org_listing(client, db_session):
    # User A creates a listing
    token_a = await _register_and_login(client, {
        "email": "mcross_a@example.com", "password": "password123",
        "full_name": "A", "organization_name": "Cross A Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_listing_with_token(db_session, org_a, "20001")

    # User B tries to use that listing id
    token_b = await _register_and_login(client, {
        "email": "mcross_b@example.com", "password": "password123",
        "full_name": "B", "organization_name": "Cross B Org",
    })
    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404


# ── create job success ─────────────────────────────────────────────────────────

async def test_create_add_image_job_succeeds(client, db_session):
    token = await _register_and_login(client, {
        "email": "madd@example.com", "password": "password123",
        "full_name": "Add", "organization_name": "Add Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "30001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg", "rank": 1},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    data = r.json()
    assert data["operation_type"] == "add_image"
    assert data["status"] == "pending"
    assert data["total_items"] == 1


async def test_create_replace_image_job_succeeds(client, db_session):
    token = await _register_and_login(client, {
        "email": "mreplace@example.com", "password": "password123",
        "full_name": "Replace", "organization_name": "Replace Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "30002")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_image",
        "payload": {"image_url": "https://example.com/new.jpg", "target_rank": 1},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    assert r.json()["operation_type"] == "replace_image"


async def test_create_delete_image_job_succeeds(client, db_session):
    token = await _register_and_login(client, {
        "email": "mdelete@example.com", "password": "password123",
        "full_name": "Delete", "organization_name": "Delete Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "30003")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "delete_image",
        "payload": {"image_id": "IMG001"},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    assert r.json()["operation_type"] == "delete_image"


# ── apply blocked without Etsy configured ─────────────────────────────────────

async def test_apply_blocked_without_etsy_configured(client, db_session):
    token = await _register_and_login(client, {
        "email": "mnoapply@example.com", "password": "password123",
        "full_name": "NoApply", "organization_name": "NoApply Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "40001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 503
    assert "Etsy" in r2.json()["detail"]


# ── apply: backup snapshot created before write ────────────────────────────────

async def test_apply_add_image_creates_backup_snapshot(client, db_session):
    token = await _register_and_login(client, {
        "email": "mbackup@example.com", "password": "password123",
        "full_name": "Backup", "organization_name": "Backup Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "50001")
    await _add_listing_image(db_session, listing, "BKUP001", rank=1)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/new.jpg", "rank": 2},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_image = {"listing_image_id": "999001", "rank": 2, "url_fullxfull": "https://etsy.com/999001.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload, \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        mock_upload.return_value = fake_etsy_image
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200

    r3 = await client.get(f"{JOBS_URL}/{job_id}/backups", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    backups = r3.json()
    assert len(backups) == 1
    snap = backups[0]
    assert snap["listing_id"] == listing.id
    assert snap["snapshot_type"] == "pre_media_write"
    assert snap["images_snapshot"] is not None


# ── apply: add_image calls upload_etsy_listing_image ──────────────────────────

async def test_apply_add_image_calls_upload(client, db_session):
    token = await _register_and_login(client, {
        "email": "mupload@example.com", "password": "password123",
        "full_name": "Upload", "organization_name": "Upload Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "60001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg", "rank": 1},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_image = {"listing_image_id": "888001", "rank": 1, "url_fullxfull": "https://etsy.com/888001.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload, \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        mock_upload.return_value = fake_etsy_image
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    assert mock_upload.called
    assert r2.json()["success_count"] == 1
    assert r2.json()["failure_count"] == 0
    assert r2.json()["status"] == "completed"


# ── apply: replace_image deletes then uploads ─────────────────────────────────

async def test_apply_replace_image_deletes_then_uploads(client, db_session):
    token = await _register_and_login(client, {
        "email": "mrepl2@example.com", "password": "password123",
        "full_name": "Repl", "organization_name": "Repl Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "70001")
    await _add_listing_image(db_session, listing, "OLD001", rank=1)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_image",
        "payload": {"image_url": "https://example.com/new.jpg", "target_rank": 1},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_image = {"listing_image_id": "777001", "rank": 1, "url_fullxfull": "https://etsy.com/777001.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.delete_etsy_listing_image", new_callable=AsyncMock) as mock_delete, \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload, \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        mock_upload.return_value = fake_etsy_image
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    assert mock_delete.called
    assert mock_upload.called
    assert r2.json()["success_count"] == 1


# ── apply: delete_image calls delete_etsy_listing_image ───────────────────────

async def test_apply_delete_image_calls_delete(client, db_session):
    token = await _register_and_login(client, {
        "email": "mdel2@example.com", "password": "password123",
        "full_name": "Del2", "organization_name": "Del2 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "80001")
    await _add_listing_image(db_session, listing, "DEL001", rank=1)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "delete_image",
        "payload": {"image_id": "DEL001"},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.delete_etsy_listing_image", new_callable=AsyncMock) as mock_delete:
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    assert mock_delete.called
    assert r2.json()["success_count"] == 1


# ── apply: delete_image with no matching image → result failed ─────────────────

async def test_apply_delete_image_no_match_is_failure(client, db_session):
    token = await _register_and_login(client, {
        "email": "mdelnomatch@example.com", "password": "password123",
        "full_name": "DelNoMatch", "organization_name": "DelNoMatch Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "80002")
    # No images added — delete by image_id should fail per-listing

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "delete_image",
        "payload": {"image_id": "NONEXISTENT"},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    data = r2.json()
    assert data["failure_count"] == 1
    assert data["success_count"] == 0


# ── apply: success updates local listing_images ───────────────────────────────

async def test_apply_add_image_success_updates_local_images(client, db_session):
    token = await _register_and_login(client, {
        "email": "mlocalupdate@example.com", "password": "password123",
        "full_name": "LocalUpdate", "organization_name": "LocalUpdate Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "90001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg", "rank": 1},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_image = {"listing_image_id": "LOCAL001", "rank": 1, "url_fullxfull": "https://etsy.com/LOCAL001.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload, \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        mock_upload.return_value = fake_etsy_image
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    # upsert_listing_images was called (local update triggered)
    assert r2.status_code == 200
    assert r2.json()["success_count"] == 1
    assert r2.json()["failure_count"] == 0
    # Confirm after_media captured in result row
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    result_item = r3.json()["items"][0]
    assert result_item["status"] == "success"
    assert result_item["after_media"] is not None


# ── apply: failure does NOT update local images ───────────────────────────────

async def test_apply_failure_does_not_update_local_images(client, db_session):
    token = await _register_and_login(client, {
        "email": "mfailnolocal@example.com", "password": "password123",
        "full_name": "FailNoLocal", "organization_name": "FailNoLocal Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "90002")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg", "rank": 1},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    from app.services.etsy_media_write import EtsyMediaWriteError

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload:
        mock_upload.side_effect = EtsyMediaWriteError("Upload failed", status_code=500)
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    assert r2.json()["failure_count"] == 1

    images_q = await db_session.execute(
        select(ListingImage).where(ListingImage.listing_id == listing.id)
    )
    assert len(images_q.scalars().all()) == 0


# ── per-listing result rows ───────────────────────────────────────────────────

async def test_apply_creates_result_rows_per_listing(client, db_session):
    token = await _register_and_login(client, {
        "email": "mresults@example.com", "password": "password123",
        "full_name": "Results", "organization_name": "Results Org",
    })
    org_id = await _get_org_id(db_session)
    listing1, _ = await _setup_listing_with_token(db_session, org_id, "100001")
    listing2, _ = await _setup_listing_with_token(db_session, org_id, "100002")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing1.id, listing2.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_image = {"listing_image_id": "R001", "rank": 1, "url_fullxfull": "https://etsy.com/r001.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload, \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        mock_upload.return_value = fake_etsy_image
        await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    r2 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# ── partial failure → completed_with_errors ───────────────────────────────────

async def test_apply_partial_failure_status_completed_with_errors(client, db_session):
    token = await _register_and_login(client, {
        "email": "mpartial@example.com", "password": "password123",
        "full_name": "Partial", "organization_name": "Partial Org",
    })
    org_id = await _get_org_id(db_session)
    listing1, _ = await _setup_listing_with_token(db_session, org_id, "110001")
    listing2, _ = await _setup_listing_with_token(db_session, org_id, "110002")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing1.id, listing2.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    from app.services.etsy_media_write import EtsyMediaWriteError

    call_count = 0

    async def sometimes_fail(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise EtsyMediaWriteError("Etsy rate limit", status_code=429)
        return {"listing_image_id": "PART001", "rank": 1, "url_fullxfull": "https://etsy.com/p.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", side_effect=sometimes_fail), \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    data = r2.json()
    assert data["status"] == "completed_with_errors"
    assert data["success_count"] == 1
    assert data["failure_count"] == 1


# ── org isolation: job detail / results / backups ─────────────────────────────

async def test_get_job_cross_org_returns_404(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "misolate_a@example.com", "password": "password123",
        "full_name": "IsoA", "organization_name": "IsoA Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_listing_with_token(db_session, org_a, "120001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token_a}"})
    job_id = r.json()["id"]

    token_b = await _register_and_login(client, {
        "email": "misolate_b@example.com", "password": "password123",
        "full_name": "IsoB", "organization_name": "IsoB Org",
    })
    r2 = await client.get(f"{JOBS_URL}/{job_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


async def test_get_results_cross_org_returns_404(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "mresiso_a@example.com", "password": "password123",
        "full_name": "ResIsoA", "organization_name": "ResIsoA Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_listing_with_token(db_session, org_a, "130001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token_a}"})
    job_id = r.json()["id"]

    token_b = await _register_and_login(client, {
        "email": "mresiso_b@example.com", "password": "password123",
        "full_name": "ResIsoB", "organization_name": "ResIsoB Org",
    })
    r2 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


async def test_list_jobs_only_returns_own_org_jobs(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "mlistiso_a@example.com", "password": "password123",
        "full_name": "ListIsoA", "organization_name": "ListIsoA Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_listing_with_token(db_session, org_a, "140001")

    await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token_a}"})

    token_b = await _register_and_login(client, {
        "email": "mlistiso_b@example.com", "password": "password123",
        "full_name": "ListIsoB", "organization_name": "ListIsoB Org",
    })
    r = await client.get(JOBS_URL, headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    assert len(r.json()) == 0


# ── audit log on start + finish ───────────────────────────────────────────────

async def test_apply_writes_audit_logs(client, db_session):
    token = await _register_and_login(client, {
        "email": "maudit@example.com", "password": "password123",
        "full_name": "Audit", "organization_name": "Audit Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "150001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_image = {"listing_image_id": "AUD001", "rank": 1, "url_fullxfull": "https://etsy.com/aud001.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload, \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        mock_upload.return_value = fake_etsy_image
        await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    from app.models.audit_log import AuditLog
    logs_q = await db_session.execute(
        select(AuditLog).where(
            AuditLog.entity_id == job_id,
        ).order_by(AuditLog.created_at.asc())
    )
    logs = logs_q.scalars().all()
    event_types = [l.event_type for l in logs]
    assert "bulk_edit_media_job_started" in event_types
    assert "bulk_edit_media_job_finished" in event_types


# ── reorder_images removed entirely — not a valid operation type ──────────────

async def test_create_reorder_images_job_rejected_as_invalid_operation(client, db_session):
    """reorder_images was never implemented (Etsy has no atomic reorder
    endpoint, and delete-then-reupload has a real data-loss window on live
    listings) and has been removed as an option entirely — creating a job
    with it must fail validation, not silently accept and skip it."""
    token = await _register_and_login(client, {
        "email": "mreorder@example.com", "password": "password123",
        "full_name": "Reorder", "organization_name": "Reorder Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160099")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "reorder_images",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


async def _make_video_render(db_session, org_id: str, status: str = "completed", is_etsy_ready: bool | None = True, file_path: str = "/tmp/fake-render.mp4", source: str = "generated"):
    from app.models.video_render import VideoRender
    render = VideoRender(
        organization_id=org_id,
        template_id="slideshow",
        source=source,
        status=status,
        image_count=3,
        aspect_ratio="9:16",
        duration_seconds=10.0,
        file_size_bytes=1024,
        width=1080,
        height=1920,
        is_etsy_ready=is_etsy_ready,
        file_path=file_path,
    )
    db_session.add(render)
    await db_session.commit()
    await db_session.refresh(render)
    return render


async def test_create_replace_video_job_succeeds(client, db_session):
    token = await _register_and_login(client, {
        "email": "mvideocreate@example.com", "password": "password123",
        "full_name": "VideoCreate", "organization_name": "VideoCreate Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160010")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    assert r.json()["operation_type"] == "replace_video"


async def test_apply_replace_video_requires_video_render_id(client, db_session):
    token = await _register_and_login(client, {
        "email": "mvideonoid@example.com", "password": "password123",
        "full_name": "VideoNoId", "organization_name": "VideoNoId Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160011")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_video",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert "video_render_id" in r3.json()["items"][0]["error_message"]


async def test_apply_replace_video_rejects_non_etsy_ready_render(client, db_session):
    token = await _register_and_login(client, {
        "email": "mvideobad@example.com", "password": "password123",
        "full_name": "VideoBad", "organization_name": "VideoBad Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160012")
    render = await _make_video_render(db_session, org_id, is_etsy_ready=False)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1


async def test_apply_replace_video_rejects_cross_org_render(client, db_session):
    token = await _register_and_login(client, {
        "email": "mvideocross@example.com", "password": "password123",
        "full_name": "VideoCross", "organization_name": "VideoCross Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160013")
    other_render = await _make_video_render(db_session, "some-other-org-id")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_video",
        "payload": {"video_render_id": other_render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1


async def test_apply_replace_video_success_uploads_and_stores_local_row(client, db_session):
    from app.models.listing_video import ListingVideo

    token = await _register_and_login(client, {
        "email": "mvideosuccess@example.com", "password": "password123",
        "full_name": "VideoSuccess", "organization_name": "VideoSuccess Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160014")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_video = {"video_id": "VID001", "video_url": "https://etsy.example/v.mp4", "thumbnail_url": "https://etsy.example/t.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_video", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = fake_etsy_video
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["success_count"] == 1
    assert mock_upload.called
    _, kwargs = mock_upload.call_args
    assert kwargs["video_file_path"] == render.file_path

    videos_q = await db_session.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
    stored = videos_q.scalar_one()
    assert stored.etsy_video_id == "VID001"


async def test_apply_replace_video_deletes_existing_video_first(client, db_session):
    from app.models.listing_video import ListingVideo

    token = await _register_and_login(client, {
        "email": "mvideoreplace@example.com", "password": "password123",
        "full_name": "VideoReplace", "organization_name": "VideoReplace Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160015")
    render = await _make_video_render(db_session, org_id)

    db_session.add(ListingVideo(listing_id=listing.id, etsy_video_id="OLDVID", rank=1))
    await db_session.commit()

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.delete_etsy_listing_video", new_callable=AsyncMock) as mock_delete, \
         patch("app.services.bulk_edit_media.upload_etsy_listing_video", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = {"video_id": "NEWVID"}
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["success_count"] == 1
    assert mock_delete.called
    assert mock_delete.call_args.kwargs["video_id"] == "OLDVID"


async def test_apply_replace_video_endpoint_not_implemented_surfaces_clearly(client, db_session):
    from app.services.etsy_media_write import EtsyMediaWriteError

    token = await _register_and_login(client, {
        "email": "mvideo404@example.com", "password": "password123",
        "full_name": "Video404", "organization_name": "Video404 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160016")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "replace_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch(
             "app.services.bulk_edit_media.upload_etsy_listing_video",
             new_callable=AsyncMock,
             side_effect=EtsyMediaWriteError("Etsy video upload failed: HTTP 404", status_code=404, not_implemented=True),
         ):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert "HTTP 404" in r3.json()["items"][0]["error_message"]


async def test_create_delete_video_job_succeeds(client, db_session):
    token = await _register_and_login(client, {
        "email": "mdvideocreate@example.com", "password": "password123",
        "full_name": "DelVideoCreate", "organization_name": "DelVideoCreate Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160020")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "delete_video",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    assert r.json()["operation_type"] == "delete_video"


async def test_apply_delete_video_no_video_is_failure(client, db_session):
    token = await _register_and_login(client, {
        "email": "mdvideo@example.com", "password": "password123",
        "full_name": "DelVideo", "organization_name": "DelVideo Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160002")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "delete_video",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1


async def test_apply_delete_video_success(client, db_session):
    from app.models.listing_video import ListingVideo

    token = await _register_and_login(client, {
        "email": "mdvideosuccess@example.com", "password": "password123",
        "full_name": "DelVideoSuccess", "organization_name": "DelVideoSuccess Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "160021")

    db_session.add(ListingVideo(listing_id=listing.id, etsy_video_id="VIDTOKILL", rank=1))
    await db_session.commit()

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "delete_video",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.delete_etsy_listing_video", new_callable=AsyncMock) as mock_delete:
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["success_count"] == 1
    assert mock_delete.called

    videos_q = await db_session.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
    assert videos_q.scalar_one_or_none() is None


# ── apply: cannot apply non-pending job ───────────────────────────────────────

async def test_apply_already_running_job_returns_400(client, db_session):
    token = await _register_and_login(client, {
        "email": "mdouble@example.com", "password": "password123",
        "full_name": "Double", "organization_name": "Double Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "170001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_image",
        "payload": {"image_url": "https://example.com/img.jpg"},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    fake_etsy_image = {"listing_image_id": "DBL001", "rank": 1, "url_fullxfull": "https://etsy.com/dbl001.jpg"}

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_image", new_callable=AsyncMock) as mock_upload, \
         patch("app.services.bulk_edit_media.upsert_listing_images", new_callable=AsyncMock):
        mock_upload.return_value = fake_etsy_image
        await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    # Try applying again — job is now "completed"
    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400
    assert "pending" in r2.json()["detail"]


# ── add_video ──────────────────────────────────────────────────────────────────

async def test_create_add_video_job_succeeds_with_video_render_id(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo1@example.com", "password": "password123",
        "full_name": "AddVideo1", "organization_name": "AddVideo1 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180001")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    assert r.json()["operation_type"] == "add_video"


async def test_create_add_video_job_succeeds_with_uploaded_video_id(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo2@example.com", "password": "password123",
        "full_name": "AddVideo2", "organization_name": "AddVideo2 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180002")
    render = await _make_video_render(db_session, org_id, source="uploaded")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"uploaded_video_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201

    fake_etsy_video = {"video_id": "UPLD001", "video_url": "https://etsy.example/u.mp4"}
    job_id = r.json()["id"]
    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_video", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = fake_etsy_video
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["success_count"] == 1
    assert mock_upload.call_args.kwargs["video_file_path"] == render.file_path


async def test_apply_add_video_rejects_missing_video_source(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo3@example.com", "password": "password123",
        "full_name": "AddVideo3", "organization_name": "AddVideo3 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180003")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert "video_render_id" in r3.json()["items"][0]["error_message"]


async def test_apply_add_video_rejects_cross_org_render(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo4@example.com", "password": "password123",
        "full_name": "AddVideo4", "organization_name": "AddVideo4 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180004")
    other_render = await _make_video_render(db_session, "some-other-org-id-2")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": other_render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1


async def test_apply_add_video_rejects_non_completed_render(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo5@example.com", "password": "password123",
        "full_name": "AddVideo5", "organization_name": "AddVideo5 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180005")
    render = await _make_video_render(db_session, org_id, status="rendering")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1


async def test_apply_add_video_rejects_non_etsy_ready_render(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo6@example.com", "password": "password123",
        "full_name": "AddVideo6", "organization_name": "AddVideo6 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180006")
    render = await _make_video_render(db_session, org_id, is_etsy_ready=False)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1


async def test_apply_add_video_rejects_missing_local_file(client, db_session):
    """render.file_path points to a file that doesn't exist on disk — the
    real upload_etsy_listing_video (not mocked) must reject it clearly."""
    token = await _register_and_login(client, {
        "email": "maddvideo7@example.com", "password": "password123",
        "full_name": "AddVideo7", "organization_name": "AddVideo7 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180007")
    render = await _make_video_render(db_session, org_id, file_path="/tmp/does-not-exist-xyz-123.mp4")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert "not found on disk" in r3.json()["items"][0]["error_message"].lower()


async def test_apply_add_video_creates_backup_snapshot(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo8@example.com", "password": "password123",
        "full_name": "AddVideo8", "organization_name": "AddVideo8 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180008")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_video", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = {"video_id": "BKUPVID"}
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    r3 = await client.get(f"{JOBS_URL}/{job_id}/backups", headers={"Authorization": f"Bearer {token}"})
    backups = r3.json()
    assert len(backups) == 1
    assert backups[0]["snapshot_type"] == "pre_media_write"


async def test_apply_add_video_calls_upload_with_file_path(client, db_session):
    token = await _register_and_login(client, {
        "email": "maddvideo9@example.com", "password": "password123",
        "full_name": "AddVideo9", "organization_name": "AddVideo9 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180009")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_video", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = {"video_id": "CALL001"}
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert mock_upload.called
    assert mock_upload.call_args.kwargs["video_file_path"] == render.file_path
    assert r2.json()["success_count"] == 1


async def test_apply_add_video_stores_listing_video_row_on_success(client, db_session):
    from app.models.listing_video import ListingVideo

    token = await _register_and_login(client, {
        "email": "maddvideo10@example.com", "password": "password123",
        "full_name": "AddVideo10", "organization_name": "AddVideo10 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180010")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch("app.services.bulk_edit_media.upload_etsy_listing_video", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = {"video_id": "STORE001", "video_url": "https://etsy.example/store.mp4"}
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["success_count"] == 1
    videos_q = await db_session.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
    stored = videos_q.scalar_one()
    assert stored.etsy_video_id == "STORE001"


async def test_apply_add_video_fails_if_listing_already_has_video(client, db_session):
    from app.models.listing_video import ListingVideo

    token = await _register_and_login(client, {
        "email": "maddvideo11@example.com", "password": "password123",
        "full_name": "AddVideo11", "organization_name": "AddVideo11 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180011")
    render = await _make_video_render(db_session, org_id)

    db_session.add(ListingVideo(listing_id=listing.id, etsy_video_id="EXISTINGVID", rank=1))
    await db_session.commit()

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert "Replace Video" in r3.json()["items"][0]["error_message"]

    # Existing video must be untouched — add_video never deletes.
    videos_q = await db_session.execute(select(ListingVideo).where(ListingVideo.listing_id == listing.id))
    stored = videos_q.scalar_one()
    assert stored.etsy_video_id == "EXISTINGVID"


async def test_apply_add_video_endpoint_not_implemented_surfaces_clearly(client, db_session):
    from app.services.etsy_media_write import EtsyMediaWriteError

    token = await _register_and_login(client, {
        "email": "maddvideo12@example.com", "password": "password123",
        "full_name": "AddVideo12", "organization_name": "AddVideo12 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_listing_with_token(db_session, org_id, "180012")
    render = await _make_video_render(db_session, org_id)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "add_video",
        "payload": {"video_render_id": render.id},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    with patch("app.services.bulk_edit_media.settings", _etsy_settings_mock()), \
         patch(
             "app.services.bulk_edit_media.upload_etsy_listing_video",
             new_callable=AsyncMock,
             side_effect=EtsyMediaWriteError("Etsy video upload failed: HTTP 501", status_code=501, not_implemented=True),
         ):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert "HTTP 501" in r3.json()["items"][0]["error_message"]
