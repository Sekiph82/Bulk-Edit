"""
M06.03 — Magic Revert refuses or warns when a listing changed since the
original apply. Covers only the fields this app can currently verify
(title/description/sku as normalized text, price_amount/quantity as exact
numbers) — any other field present in the snapshot is treated as unverified,
which is itself a conflict (never assumed safe). See DECISIONS.md.

Every Etsy call here is mocked — no live Etsy read or write.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.services.bulk_edit_revert import detect_revert_conflict

from tests.test_bulk_edit_revert import (
    APPLY_JOBS_URL,
    REVERT_JOBS_URL,
    _mock_etsy_settings,
    _setup_and_apply,
)


def _fake_current_listing(title: str, price_amount: int = 2000, quantity: int = 3) -> dict:
    return {
        "title": title,
        "price": {"amount": price_amount, "divisor": 100, "currency_code": "USD"},
        "quantity": quantity,
    }


# ── unit tests: detect_revert_conflict() ────────────────────────────────────

def test_detect_conflict_no_conflict_when_current_matches_expected():
    listing = MagicMock(title="Same Title", price_amount=2000, quantity=3)
    snapshot_data = {"title": "Original Title"}  # revert target — irrelevant to the comparison
    current = _fake_current_listing("Same Title")
    result = detect_revert_conflict(listing, snapshot_data, current)
    assert result["has_conflict"] is False
    assert result["conflicting_fields"] == []


def test_detect_conflict_flags_changed_title():
    listing = MagicMock(title="Expected Title", price_amount=2000, quantity=3)
    snapshot_data = {"title": "Original Title"}
    current = _fake_current_listing("Someone Changed This On Etsy")
    result = detect_revert_conflict(listing, snapshot_data, current)
    assert result["has_conflict"] is True
    assert "title" in result["conflicting_fields"]


def test_detect_conflict_flags_changed_price():
    listing = MagicMock(title="T", price_amount=2000, quantity=3)
    snapshot_data = {"price_amount": 1500}
    current = _fake_current_listing("T", price_amount=9999)
    result = detect_revert_conflict(listing, snapshot_data, current)
    assert result["has_conflict"] is True
    assert "price_amount" in result["conflicting_fields"]


def test_detect_conflict_unverified_field_is_still_a_conflict():
    """A field the checker can't yet verify (e.g. is_customizable) must not
    be assumed safe — it's still a conflict, per this task's explicit rule."""
    listing = MagicMock(title="T", price_amount=2000, quantity=3, is_customizable=True)
    snapshot_data = {"is_customizable": False}
    current = _fake_current_listing("T")
    result = detect_revert_conflict(listing, snapshot_data, current)
    assert result["has_conflict"] is True
    assert "is_customizable" in result["unverified_fields"]
    assert result["conflicting_fields"] == []


def test_detect_conflict_unreadable_current_state_is_a_conflict():
    listing = MagicMock(title="T", price_amount=2000, quantity=3)
    result = detect_revert_conflict(listing, {"title": "X"}, None)
    assert result["has_conflict"] is True
    assert result["unverified_fields"] == ["*"]


def test_detect_conflict_reason_text_matches_required_owner_copy():
    listing = MagicMock(title="Expected", price_amount=2000, quantity=3)
    snapshot_data = {"title": "Original"}
    current = _fake_current_listing("Different")
    result = detect_revert_conflict(listing, snapshot_data, current)
    assert "changed after the original apply" in result["reason"]
    assert "overwrite newer work" in result["reason"]


# ── integration tests: full revert flow through the conflict gate ──────────

async def test_revert_proceeds_when_no_conflict(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="conflict_ok@example.com", org_name="Conflict OK Org", etsy_prefix="cok",
    )
    listing_id = listing.id  # capture as plain str before expire_all() below
    db_session.expire_all()
    from app.models.listing import Listing
    listing = (await db_session.execute(select(Listing).where(Listing.id == listing_id))).scalar_one()
    current_title = listing.title  # exactly what apply set it to — no drift

    with (
        patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_revert.fetch_current_listing_for_conflict_check", new_callable=AsyncMock) as mock_fetch,
        patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock, return_value={"state": "active"}),
    ):
        mock_fetch.return_value = _fake_current_listing(current_title)
        r = await client.post(f"{APPLY_JOBS_URL}/{apply_job_id}/revert", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    revert_job_id = r.json()["id"]
    results_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}/results", headers={"Authorization": f"Bearer {token}"})
    items = results_r.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "success"


async def test_revert_refused_when_listing_changed_since_apply(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="conflict_bad@example.com", org_name="Conflict Bad Org", etsy_prefix="cbad",
    )

    with (
        patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_revert.fetch_current_listing_for_conflict_check", new_callable=AsyncMock) as mock_fetch,
        patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock) as mock_patch,
    ):
        mock_fetch.return_value = _fake_current_listing("Someone edited this directly on Etsy")
        r = await client.post(f"{APPLY_JOBS_URL}/{apply_job_id}/revert", headers={"Authorization": f"Bearer {token}"})

        # No Etsy write attempted for the conflicted item
        mock_patch.assert_not_called()

    assert r.status_code == 202
    revert_job_id = r.json()["id"]
    revert_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}", headers={"Authorization": f"Bearer {token}"})
    revert_job = revert_r.json()["job"]
    assert revert_job["skipped_count"] == 1
    assert revert_job["success_count"] == 0

    results_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}/results", headers={"Authorization": f"Bearer {token}"})
    items = results_r.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "conflict"
    assert "changed after the original apply" in items[0]["error_message"]
    assert "overwrite newer work" in items[0]["error_message"]


async def test_conflict_diagnostics_contain_no_secrets(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="conflict_secrets@example.com", org_name="Conflict Secrets Org", etsy_prefix="csec",
    )

    with (
        patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_revert.fetch_current_listing_for_conflict_check", new_callable=AsyncMock) as mock_fetch,
        patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock),
    ):
        mock_fetch.return_value = _fake_current_listing("Different title entirely")
        r = await client.post(f"{APPLY_JOBS_URL}/{apply_job_id}/revert", headers={"Authorization": f"Bearer {token}"})

    revert_job_id = r.json()["id"]
    results_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}/results", headers={"Authorization": f"Bearer {token}"})
    item = results_r.json()["items"][0]
    payload_text = str(item)
    assert "fake_revert_token" not in payload_text
    assert "Bearer" not in payload_text
    assert "x-api-key" not in payload_text.lower()
