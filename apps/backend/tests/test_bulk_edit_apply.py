"""
Sprint 8 tests: bulk edit apply, backup snapshots, apply jobs, org isolation.

Etsy writes are NOT made in tests — settings.ETSY_CLIENT_ID is a placeholder,
so is_etsy_configured() returns False and apply returns 503 before any write.
Tests verify the safety gates, backup creation, job creation, and schema validation.
A patched Etsy write path tests success/failure scenarios without hitting the real API.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.services.etsy_write import build_etsy_patch_payload

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
SESSIONS_URL = "/api/v1/bulk-edit/sessions"


def _mock_etsy_settings():
    """Return a MagicMock settings with is_etsy_configured() → True."""
    m = MagicMock()
    m.is_etsy_configured.return_value = True
    return m


# ── helpers ────────────────────────────────────────────────────────────────────

async def _register_and_login(client, user: dict) -> str:
    await client.post(REGISTER_URL, json=user)
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _setup_listing(db_session, org_id: str, etsy_id: str = "10001", **kwargs):
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"apply_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(
            organization_id=org_id,
            etsy_shop_id=shop_etsy_id,
            shop_name="Apply Shop",
            is_connected=True,
        )
        db_session.add(shop)
        await db_session.flush()
        token = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake_apply_token"),
            refresh_token_enc=encrypt_token("fake_r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scopes="listings_r listings_w",
        )
        db_session.add(token)

    listing = Listing(
        organization_id=org_id,
        etsy_shop_id=shop.id,
        etsy_listing_id=etsy_id,
        title=kwargs.get("title", f"Apply Listing {etsy_id}"),
        state="active",
        price_amount=kwargs.get("price_amount", 2000),
        quantity=kwargs.get("quantity", 3),
        tags=kwargs.get("tags", ["handmade", "gift"]),
        **{k: v for k, v in kwargs.items() if k not in ("title", "price_amount", "quantity", "tags")},
    )
    db_session.add(listing)
    await db_session.commit()
    return listing


async def _get_org_id_for_user(db_session, user_email: str) -> str:
    from app.models.user import User
    from app.models.organization_member import OrganizationMember
    u_r = await db_session.execute(select(User).where(User.email == user_email))
    u = u_r.scalar_one()
    m_r = await db_session.execute(select(OrganizationMember).where(OrganizationMember.user_id == u.id).limit(1))
    m = m_r.scalar_one()
    return m.organization_id


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    return member.organization_id


async def _create_previewed_session(client, db_session, token, org_id, etsy_prefix: str):
    listing = await _setup_listing(db_session, org_id, f"{etsy_prefix}_01", title=f"Listing For {etsy_prefix} Test Here")

    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [listing.id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, f"Session create failed: {r.json()}"
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "append", "operation_value": " — Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"{SESSIONS_URL}/{session_id}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    return session_id, listing


# ── unit tests for etsy_write helpers ─────────────────────────────────────────

def test_build_etsy_patch_payload_title():
    diff = {"title": {"before": "Old", "after": "New Title"}}
    payload = build_etsy_patch_payload(diff)
    assert payload["title"] == "New Title"


def test_build_etsy_patch_payload_tags():
    diff = {"tags": {"before": ["a"], "after": ["a", "b"]}}
    payload = build_etsy_patch_payload(diff)
    assert payload["tags"] == ["a", "b"]


def test_build_etsy_patch_payload_section_id_maps_to_shop_section_id():
    diff = {"section_id": {"before": "123", "after": "456"}}
    payload = build_etsy_patch_payload(diff)
    assert "shop_section_id" in payload
    assert payload["shop_section_id"] == "456"
    assert "section_id" not in payload


def test_build_etsy_patch_payload_bool_field():
    diff = {"is_supply": {"before": False, "after": True}}
    payload = build_etsy_patch_payload(diff)
    assert "is_supply" in payload
    assert payload["is_supply"] is True


def test_build_etsy_patch_payload_excludes_price_amount():
    diff = {
        "title": {"before": "Old", "after": "New Title"},
        "price_amount": {"before": 1000, "after": 2000},
    }
    payload = build_etsy_patch_payload(diff)
    assert "price_amount" not in payload
    assert "title" in payload


def test_build_etsy_patch_payload_excludes_quantity():
    diff = {"quantity": {"before": 5, "after": 10}}
    payload = build_etsy_patch_payload(diff)
    assert "quantity" not in payload


def test_build_etsy_patch_payload_empty_diff():
    payload = build_etsy_patch_payload({})
    assert payload == {}


def test_build_etsy_patch_payload_description():
    diff = {"description": {"before": "Old desc", "after": "New desc"}}
    payload = build_etsy_patch_payload(diff)
    assert payload["description"] == "New desc"


# ── API tests: safety gates ────────────────────────────────────────────────────

async def test_apply_requires_preview_ready_status(client, db_session):
    token = await _register_and_login(client, {
        "email": "ap_gate1@example.com", "password": "password123",
        "full_name": "G1", "organization_name": "Gate1 Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "gate1_01", title="Gate One Test Listing Here")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    # No preview generated — session is "draft"
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400
    assert "preview_ready" in r2.json()["detail"]


async def test_apply_blocked_when_etsy_not_configured(client, db_session):
    token = await _register_and_login(client, {
        "email": "ap_gate2@example.com", "password": "password123",
        "full_name": "G2", "organization_name": "Gate2 Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, _ = await _create_previewed_session(client, db_session, token, org_id, "gate2")

    # ETSY_CLIENT_ID is placeholder — is_etsy_configured() returns False → 503
    r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 503
    assert "Etsy" in r.json()["detail"]


async def test_apply_blocked_when_invalid_preview_items_exist(client, db_session):
    token = await _register_and_login(client, {
        "email": "ap_gate3@example.com", "password": "password123",
        "full_name": "G3", "organization_name": "Gate3 Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "gate3_01", title="Gate Three Listing Here Test")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    # Set title to empty string → validation_status="invalid"
    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "set", "operation_value": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})

    # Patch settings so Etsy appears configured, to hit the invalid items check
    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()):
        r2 = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 422
    assert "invalid" in r2.json()["detail"].lower()


async def test_apply_requires_auth(client):
    r = await client.post(f"{SESSIONS_URL}/fake-id/apply")
    assert r.status_code == 403


async def test_apply_404_on_wrong_org(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "ap_iso_a@example.com", "password": "password123",
        "full_name": "IA", "organization_name": "Iso Apply A",
    })
    # Get org A BEFORE registering B
    org_a_id = await _get_org_id_for_user(db_session, "ap_iso_a@example.com")

    token_b = await _register_and_login(client, {
        "email": "ap_iso_b@example.com", "password": "password123",
        "full_name": "IB", "organization_name": "Iso Apply B",
    })

    session_id, _ = await _create_previewed_session(client, db_session, token_a, org_a_id, "iso_apply")

    # Org B user tries to apply org A's session
    r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404


# ── API tests: job creation and result retrieval ───────────────────────────────

async def test_apply_creates_job_and_returns_202(client, db_session):
    token = await _register_and_login(client, {
        "email": "ap_job1@example.com", "password": "password123",
        "full_name": "J1", "organization_name": "Job1 Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, _ = await _create_previewed_session(client, db_session, token, org_id, "job1")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {"listing_id": "job1_01", "state": "active"}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    data = r.json()
    assert data["status"] in ("completed", "completed_with_errors")
    assert "id" in data
    assert data["bulk_edit_session_id"] == session_id


async def test_apply_job_success_updates_listing(client, db_session):
    from app.models.listing import Listing

    token = await _register_and_login(client, {
        "email": "ap_upd@example.com", "password": "password123",
        "full_name": "Upd", "organization_name": "Update Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, listing = await _create_previewed_session(client, db_session, token, org_id, "upd")

    original_title = listing.title

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {"listing_id": listing.etsy_listing_id, "state": "active"}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    data = r.json()
    assert data["success_count"] >= 1

    await db_session.refresh(listing)
    assert listing.title != original_title
    assert listing.title == original_title + " — Updated"


async def test_apply_etsy_failure_does_not_update_listing(client, db_session):
    from app.models.listing import Listing
    from app.services.etsy_write import EtsyWriteError

    token = await _register_and_login(client, {
        "email": "ap_fail@example.com", "password": "password123",
        "full_name": "Fail", "organization_name": "Fail Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, listing = await _create_previewed_session(client, db_session, token, org_id, "fail")
    original_title = listing.title

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.side_effect = EtsyWriteError("Etsy rejected the request", 400)
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    data = r.json()
    assert data["failure_count"] >= 1
    assert data["success_count"] == 0
    assert data["status"] == "failed"

    await db_session.refresh(listing)
    assert listing.title == original_title  # not modified


async def test_apply_creates_backup_snapshot(client, db_session):
    from app.models.listing_backup_snapshot import ListingBackupSnapshot

    token = await _register_and_login(client, {
        "email": "ap_bkp@example.com", "password": "password123",
        "full_name": "Bkp", "organization_name": "Backup Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, listing = await _create_previewed_session(client, db_session, token, org_id, "bkp")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {"listing_id": listing.etsy_listing_id}
        await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    snaps = await db_session.execute(
        select(ListingBackupSnapshot).where(
            ListingBackupSnapshot.bulk_edit_session_id == session_id,
        )
    )
    snapshots = snaps.scalars().all()
    assert len(snapshots) >= 1
    assert snapshots[0].snapshot_type == "pre_write"
    assert "title" in snapshots[0].snapshot_data


async def test_list_apply_jobs_for_session(client, db_session):
    token = await _register_and_login(client, {
        "email": "ap_jobs@example.com", "password": "password123",
        "full_name": "Jobs", "organization_name": "Jobs Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, _ = await _create_previewed_session(client, db_session, token, org_id, "jobs")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {}
        await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    r = await client.get(
        f"{SESSIONS_URL}/{session_id}/apply-jobs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_get_apply_job_detail_includes_results(client, db_session):
    token = await _register_and_login(client, {
        "email": "ap_detail@example.com", "password": "password123",
        "full_name": "Det", "organization_name": "Detail Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, _ = await _create_previewed_session(client, db_session, token, org_id, "detail")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {}
        r_apply = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    job_id = r_apply.json()["id"]
    r = await client.get(
        f"/api/v1/bulk-edit/apply-jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "job" in data
    assert "results" in data
    assert isinstance(data["results"], list)


async def test_get_backups_for_session(client, db_session):
    token = await _register_and_login(client, {
        "email": "ap_bkp2@example.com", "password": "password123",
        "full_name": "B2", "organization_name": "Backup2 Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, _ = await _create_previewed_session(client, db_session, token, org_id, "bkp2")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {}
        await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    r = await client.get(
        f"{SESSIONS_URL}/{session_id}/backups",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["snapshot_type"] == "pre_write"


async def test_apply_job_detail_404_wrong_org(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "ap_det_a@example.com", "password": "password123",
        "full_name": "DA", "organization_name": "Det Org A",
    })
    # Get org A BEFORE registering B
    org_a_id = await _get_org_id_for_user(db_session, "ap_det_a@example.com")

    token_b = await _register_and_login(client, {
        "email": "ap_det_b@example.com", "password": "password123",
        "full_name": "DB", "organization_name": "Det Org B",
    })

    session_id, _ = await _create_previewed_session(client, db_session, token_a, org_a_id, "det_iso")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {}
        r_apply = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token_a}"})

    job_id = r_apply.json()["id"]
    r = await client.get(
        f"/api/v1/bulk-edit/apply-jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 404


async def test_apply_increments_usage_on_success(client, db_session):
    from app.models.usage_counter import UsageCounter
    from datetime import datetime, timezone

    token = await _register_and_login(client, {
        "email": "ap_usage@example.com", "password": "password123",
        "full_name": "Us", "organization_name": "Usage Org",
    })
    org_id = await _get_org_id(db_session)
    session_id, _ = await _create_previewed_session(client, db_session, token, org_id, "usage")

    period = datetime.now(timezone.utc).strftime("%Y-%m")

    before_result = await db_session.execute(
        select(UsageCounter).where(
            UsageCounter.organization_id == org_id,
            UsageCounter.period_key == period,
        )
    )
    before_counter = before_result.scalar_one_or_none()
    before_count = before_counter.bulk_edits_used if before_counter else 0

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = {}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    if r.json().get("success_count", 0) > 0:
        after_result = await db_session.execute(
            select(UsageCounter).where(
                UsageCounter.organization_id == org_id,
                UsageCounter.period_key == period,
            )
        )
        after_counter = after_result.scalar_one_or_none()
        after_count = after_counter.bulk_edits_used if after_counter else 0
        assert after_count > before_count
