"""
M06.03 — Magic Revert refuses or warns when a listing changed since the
original apply. Compares live Etsy state against the ORIGINAL apply job's
own captured after-values (build_expected_after_values()), never against
the current local Listing row -- see the module docstring in
bulk_edit_revert.py for the same-app later-write bug this remediates
(PR #121 audit finding).

Covers only the fields this app can currently verify (title/description/sku
as normalized text, price_amount/quantity as exact numbers) -- any other
changed field, or a field with no reliable captured after-value, is treated
as unverified, which is itself a conflict (never assumed safe). See
DECISIONS.md.

Every Etsy call here is mocked -- no live Etsy read or write.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.services.bulk_edit_revert import detect_revert_conflict, build_expected_after_values

from tests.test_bulk_edit_revert import (
    APPLY_JOBS_URL,
    REVERT_JOBS_URL,
    SESSIONS_URL,
    _mock_etsy_settings,
    _setup_and_apply,
    _register_and_login,
)


def _fake_current_listing(title: str, price_amount: int = 2000, quantity: int = 3) -> dict:
    return {
        "title": title,
        "price": {"amount": price_amount, "divisor": 100, "currency_code": "USD"},
        "quantity": quantity,
    }


# ── unit tests: detect_revert_conflict() ────────────────────────────────────

def test_detect_conflict_no_conflict_when_current_matches_expected():
    expected_after = {"title": "Expected Title"}
    current = _fake_current_listing("Expected Title")
    result = detect_revert_conflict(expected_after, {"title"}, current)
    assert result["has_conflict"] is False
    assert result["conflicting_fields"] == []


def test_detect_conflict_flags_changed_title():
    expected_after = {"title": "Expected Title"}
    current = _fake_current_listing("Someone Changed This On Etsy")
    result = detect_revert_conflict(expected_after, {"title"}, current)
    assert result["has_conflict"] is True
    assert "title" in result["conflicting_fields"]


def test_detect_conflict_flags_changed_price():
    expected_after = {"price_amount": 1500}
    current = _fake_current_listing("T", price_amount=9999)
    result = detect_revert_conflict(expected_after, {"price_amount"}, current)
    assert result["has_conflict"] is True
    assert "price_amount" in result["conflicting_fields"]


def test_detect_conflict_allows_price_when_matches_expected_after():
    expected_after = {"price_amount": 6288}
    current = _fake_current_listing("T", price_amount=6288)
    result = detect_revert_conflict(expected_after, {"price_amount"}, current)
    assert result["has_conflict"] is False


def test_detect_conflict_quantity_match_and_mismatch():
    current = _fake_current_listing("T", quantity=5)
    ok = detect_revert_conflict({"quantity": 5}, {"quantity"}, current)
    assert ok["has_conflict"] is False
    bad = detect_revert_conflict({"quantity": 9}, {"quantity"}, current)
    assert bad["has_conflict"] is True
    assert "quantity" in bad["conflicting_fields"]


def test_detect_conflict_unverified_field_is_still_a_conflict():
    """A changed field this checker has no comparator for (e.g. is_customizable)
    must not be assumed safe -- it's still a conflict, even if we somehow had
    an expected-after value for it."""
    expected_after = {"title": "T", "is_customizable": False}
    current = _fake_current_listing("T")
    result = detect_revert_conflict(expected_after, {"title", "is_customizable"}, current)
    assert result["has_conflict"] is True
    assert "is_customizable" in result["unverified_fields"]
    assert result["conflicting_fields"] == []


def test_detect_conflict_field_missing_expected_after_is_unverified_not_safe():
    """The core fix under test: a changed field with NO captured after-value
    (neither AuditLog nor preview diff had it) must be unverified, never
    silently treated as safe by falling back to some other value."""
    current = _fake_current_listing("Whatever Is Live Now")
    result = detect_revert_conflict({}, {"title"}, current)
    assert result["has_conflict"] is True
    assert "title" in result["unverified_fields"]
    assert result["conflicting_fields"] == []


def test_detect_conflict_no_changed_fields_at_all_blocks_as_unverified():
    """Old job with zero reliable source (no audit rows, no preview diff) --
    block entirely rather than silently allowing the revert."""
    current = _fake_current_listing("T")
    result = detect_revert_conflict({}, set(), current)
    assert result["has_conflict"] is True
    assert result["unverified_fields"] == ["*"]
    assert "Cannot verify the expected post-apply value" in result["reason"]


def test_detect_conflict_unreadable_current_state_is_a_conflict():
    result = detect_revert_conflict({"title": "X"}, {"title"}, None)
    assert result["has_conflict"] is True
    assert result["unverified_fields"] == ["*"]


def test_detect_conflict_reason_text_matches_required_owner_copy():
    expected_after = {"title": "Expected"}
    current = _fake_current_listing("Different")
    result = detect_revert_conflict(expected_after, {"title"}, current)
    assert "changed after the original apply" in result["reason"]
    assert "overwrite newer work" in result["reason"]


def test_detect_conflict_unverified_reason_text_matches_required_owner_copy():
    current = _fake_current_listing("T")
    result = detect_revert_conflict({}, {"title"}, current)
    assert "Cannot verify the expected post-apply value" in result["reason"]
    assert "overwriting newer work" in result["reason"]


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


# ── the core regression: same-app later-write must not be missed ───────────

async def test_same_app_later_write_regression_blocks_revert_of_stale_job(client, db_session):
    """This is the exact PR #121 audit finding scenario:

    Job A: title "Original Title For X" -> "Original Title For X — Updated" (Job A's after)
    Job B: applied later on the SAME listing, changes title again to "Second Update"
    Now local Listing.title == live Etsy title == "Second Update" (both equal!)

    The OLD (buggy) implementation compared live Etsy to the local Listing row,
    which would say "no conflict" here since both are "Second Update" -- and
    would then overwrite Job B's work by reverting Job A. The fix must compare
    live Etsy against Job A's OWN captured after-value ("...— Updated"), which
    does not match "Second Update" -- so Job A's revert must be refused.
    """
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="same_app_later_write@example.com",
        org_name="Same App Later Write Org", etsy_prefix="salw",
    )
    await db_session.refresh(listing)
    job_a_after_title = listing.title  # "...— Updated" — Job A's real captured after-value
    assert job_a_after_title.endswith("— Updated")

    # Job B: a second bulk-edit session on the SAME listing, applied after Job A,
    # that changes the title again -- simulates a later same-app write.
    r = await client.post(
        SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"},
    )
    session_b_id = r.json()["id"]
    await client.post(
        f"{SESSIONS_URL}/{session_b_id}/changes",
        json={"field_name": "title", "operation": "set", "operation_value": "Second Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_b_id}/preview", headers={"Authorization": f"Bearer {token}"})
    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_apply_b:
        mock_apply_b.return_value = {"state": "active"}
        r_apply_b = await client.post(f"{SESSIONS_URL}/{session_b_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r_apply_b.status_code == 202

    await db_session.refresh(listing)
    assert listing.title == "Second Update"  # local row now reflects Job B, not Job A

    # Now revert Job A. Live Etsy is mocked to also say "Second Update" (Job B's
    # write actually landed on Etsy) -- i.e. live == local, the exact condition
    # the old buggy comparison would have called "safe".
    with (
        patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_revert.fetch_current_listing_for_conflict_check", new_callable=AsyncMock) as mock_fetch,
        patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock) as mock_patch,
    ):
        mock_fetch.return_value = _fake_current_listing("Second Update")
        r = await client.post(f"{APPLY_JOBS_URL}/{apply_job_id}/revert", headers={"Authorization": f"Bearer {token}"})
        mock_patch.assert_not_called()  # no Etsy write for the conflicted item

    assert r.status_code == 202
    revert_job_id = r.json()["id"]
    revert_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}", headers={"Authorization": f"Bearer {token}"})
    revert_job = revert_r.json()["job"]
    assert revert_job["success_count"] == 0
    assert revert_job["skipped_count"] == 1

    results_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}/results", headers={"Authorization": f"Bearer {token}"})
    item = results_r.json()["items"][0]
    assert item["status"] == "conflict"
    assert "changed after the original apply" in item["error_message"]

    # Local listing must still say "Second Update" -- Job B's work was NOT overwritten.
    await db_session.refresh(listing)
    assert listing.title == "Second Update"


# ── build_expected_after_values(): source priority + old-job fallback ──────

async def test_build_expected_after_values_uses_audit_log_after(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="expected_after_audit@example.com",
        org_name="Expected After Audit Org", etsy_prefix="eaa",
    )
    listing_id = listing.id  # capture as plain str before expire_all() below
    db_session.expire_all()
    expected_map = await build_expected_after_values(db_session, org_id, apply_job_id, session_id, [listing_id])
    expected_after, changed_fields = expected_map[listing_id]
    assert "title" in changed_fields
    from app.models.listing import Listing
    fresh_listing = (await db_session.execute(select(Listing).where(Listing.id == listing_id))).scalar_one()
    assert expected_after["title"] == fresh_listing.title  # audit row's after == what apply actually set


async def test_build_expected_after_values_falls_back_to_preview_diff_when_no_audit_rows(client, db_session):
    """Simulates an OLD apply job that predates the AuditLog write-trail
    columns: delete its per-field AuditLog rows, keep the preview item's diff
    intact. The preview diff must still supply a reliable after-value."""
    from app.models.audit_log import AuditLog
    from app.models.listing import Listing
    from sqlalchemy import delete

    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="expected_after_fallback@example.com",
        org_name="Expected After Fallback Org", etsy_prefix="eaf",
    )
    listing_id = listing.id  # capture as plain str before expire_all() below
    await db_session.execute(delete(AuditLog).where(AuditLog.apply_job_id == apply_job_id))
    await db_session.commit()
    db_session.expire_all()

    expected_map = await build_expected_after_values(db_session, org_id, apply_job_id, session_id, [listing_id])
    expected_after, changed_fields = expected_map[listing_id]
    assert "title" in changed_fields
    fresh_listing = (await db_session.execute(select(Listing).where(Listing.id == listing_id))).scalar_one()
    assert expected_after["title"] == fresh_listing.title


async def test_build_expected_after_values_no_source_leaves_field_unverified(client, db_session):
    """Both sources gone (audit rows deleted AND preview item's diff cleared)
    -- must NOT fall back to the local Listing row. changed_fields becomes
    empty, so detect_revert_conflict() blocks the whole item as unverified."""
    from app.models.audit_log import AuditLog
    from app.models.bulk_edit_preview_item import BulkEditPreviewItem
    from sqlalchemy import delete, update

    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="expected_after_none@example.com",
        org_name="Expected After None Org", etsy_prefix="eanone",
    )
    listing_id = listing.id  # capture as plain str before expire_all() below
    await db_session.execute(delete(AuditLog).where(AuditLog.apply_job_id == apply_job_id))
    await db_session.execute(
        update(BulkEditPreviewItem)
        .where(BulkEditPreviewItem.bulk_edit_session_id == session_id, BulkEditPreviewItem.listing_id == listing_id)
        .values(diff={})
    )
    await db_session.commit()
    db_session.expire_all()

    expected_map = await build_expected_after_values(db_session, org_id, apply_job_id, session_id, [listing_id])
    expected_after, changed_fields = expected_map[listing_id]
    assert expected_after == {}
    assert changed_fields == set()

    current = _fake_current_listing("Whatever Etsy Says Now")
    result = detect_revert_conflict(expected_after, changed_fields, current)
    assert result["has_conflict"] is True
    assert result["unverified_fields"] == ["*"]


async def test_revert_blocked_when_old_job_has_no_captured_after_value(client, db_session):
    """End-to-end: an apply job with no audit rows and no preview diff must
    have its revert refused for that item -- no Etsy write attempted."""
    from app.models.audit_log import AuditLog
    from app.models.bulk_edit_preview_item import BulkEditPreviewItem
    from sqlalchemy import delete, update

    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="old_job_no_source@example.com",
        org_name="Old Job No Source Org", etsy_prefix="ojns",
    )
    await db_session.execute(delete(AuditLog).where(AuditLog.apply_job_id == apply_job_id))
    await db_session.execute(
        update(BulkEditPreviewItem)
        .where(BulkEditPreviewItem.bulk_edit_session_id == session_id, BulkEditPreviewItem.listing_id == listing.id)
        .values(diff={})
    )
    await db_session.commit()

    with (
        patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_revert.fetch_current_listing_for_conflict_check", new_callable=AsyncMock) as mock_fetch,
        patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock) as mock_patch,
    ):
        mock_fetch.return_value = _fake_current_listing("Anything")
        r = await client.post(f"{APPLY_JOBS_URL}/{apply_job_id}/revert", headers={"Authorization": f"Bearer {token}"})
        mock_patch.assert_not_called()

    assert r.status_code == 202
    revert_job_id = r.json()["id"]
    results_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}/results", headers={"Authorization": f"Bearer {token}"})
    item = results_r.json()["items"][0]
    assert item["status"] == "conflict"
    assert "Cannot verify the expected post-apply value" in item["error_message"]


# ── unsupported field touched ────────────────────────────────────────────

async def test_unsupported_field_touched_blocks_revert_even_with_after_value(client, db_session):
    """A changed field with a real captured after-value but no comparator
    (e.g. tags) must still be unverified/conflict -- never assumed safe just
    because we happen to know the after-value."""
    current = _fake_current_listing("T")
    expected_after = {"title": "T", "tags": ["a", "b"]}
    result = detect_revert_conflict(expected_after, {"title", "tags"}, current)
    assert result["has_conflict"] is True
    assert "tags" in result["unverified_fields"]
    assert "title" not in result["conflicting_fields"]
    assert "title" not in result["unverified_fields"]


# ── mixed job: one safe item, one conflicted item ───────────────────────────

async def test_mixed_job_one_safe_one_conflict_partial_revert(client, db_session):
    """Two listings in one apply job: one has no drift (revert succeeds), the
    other was changed since apply (conflict, skipped). Counts must reflect
    both outcomes and no Etsy write must happen for the conflicted item."""
    token = await _register_and_login(
        client,
        {"email": "mixed_job@example.com", "password": "password123", "full_name": "Mixed", "organization_name": "Mixed Job Org"},
    )
    from tests.test_bulk_edit_revert import _get_org_id_for_user, _grant_plan, _setup_listing

    org_id = await _get_org_id_for_user(db_session, "mixed_job@example.com")
    await _grant_plan(db_session, org_id, "pro_monthly")
    listing_ok = await _setup_listing(db_session, org_id, "mixed_ok_01", title="Mixed OK Title")
    listing_bad = await _setup_listing(db_session, org_id, "mixed_bad_01", title="Mixed Bad Title")

    r = await client.post(
        SESSIONS_URL, json={"listing_ids": [listing_ok.id, listing_bad.id]}, headers={"Authorization": f"Bearer {token}"},
    )
    session_id = r.json()["id"]
    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "append", "operation_value": " — Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as m:
        m.return_value = {"state": "active"}
        r_apply = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r_apply.status_code == 202
    apply_job_id = r_apply.json()["id"]

    await db_session.refresh(listing_ok)
    await db_session.refresh(listing_bad)
    ok_after_title = listing_ok.title
    bad_after_title = listing_bad.title

    def fake_current(etsy_listing_id):
        if etsy_listing_id == listing_ok.etsy_listing_id:
            return _fake_current_listing(ok_after_title)  # unchanged since apply
        return _fake_current_listing("Someone changed this on Etsy")  # drifted

    with (
        patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_revert.fetch_current_listing_for_conflict_check", new_callable=AsyncMock) as mock_fetch,
        patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock) as mock_patch,
    ):
        mock_fetch.side_effect = lambda access_token, etsy_listing_id: fake_current(etsy_listing_id)
        mock_patch.return_value = {"state": "active"}
        r = await client.post(f"{APPLY_JOBS_URL}/{apply_job_id}/revert", headers={"Authorization": f"Bearer {token}"})
        assert mock_patch.call_count == 1  # only the safe item got an Etsy write

    assert r.status_code == 202
    revert_job_id = r.json()["id"]
    revert_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}", headers={"Authorization": f"Bearer {token}"})
    job = revert_r.json()["job"]
    assert job["success_count"] == 1
    assert job["skipped_count"] == 1
    assert job["failure_count"] == 0

    results_r = await client.get(f"{REVERT_JOBS_URL}/{revert_job_id}/results", headers={"Authorization": f"Bearer {token}"})
    items = {i["etsy_listing_id"]: i for i in results_r.json()["items"]}
    assert items[listing_ok.etsy_listing_id]["status"] == "success"
    assert items[listing_bad.etsy_listing_id]["status"] == "conflict"
