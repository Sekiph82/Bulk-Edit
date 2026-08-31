"""
M06.04 — Per-item write audit trail.

Extends the existing, already-general-purpose `audit_logs` table (already
used for apply/revert/media/variation job start/finish events) rather than
creating a new table — one row per (listing, field) a bulk edit apply
actually touched, later linked to its Magic Revert outcome if one occurs.

Every Etsy call in these tests is mocked — no live Etsy call.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.models.audit_log import AuditLog

from tests.test_bulk_edit_revert import (
    APPLY_JOBS_URL,
    SESSIONS_URL,
    _get_org_id_for_user,
    _mock_etsy_settings,
    _register_and_login,
    _setup_and_apply,
    _setup_listing,
)


async def _get_field_audit_rows(db_session, org_id: str, apply_job_id: str | None = None):
    query = select(AuditLog).where(
        AuditLog.organization_id == org_id,
        AuditLog.event_type == "bulk_edit_field_write",
    )
    if apply_job_id:
        query = query.where(AuditLog.apply_job_id == apply_job_id)
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def test_audit_record_written_for_successful_title_apply(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="audit_title@example.com", org_name="Audit Title Org", etsy_prefix="atitle",
    )

    rows = await _get_field_audit_rows(db_session, org_id, apply_job_id)
    assert len(rows) == 1
    row = rows[0]
    assert row.field_name == "title"
    assert row.result_status == "success"
    assert row.apply_job_id == apply_job_id
    assert row.entity_id == listing.id
    assert row.extra_data["before"] == "Original Title For atitle"
    assert row.extra_data["after"] == "Original Title For atitle — Updated"
    assert row.extra_data["etsy_listing_id"] == listing.etsy_listing_id
    assert row.extra_data["bulk_edit_session_id"] == session_id


async def test_audit_record_written_for_price_apply_before_after_accurate(client, db_session):
    token = await _register_and_login(client, {
        "email": "audit_price@example.com", "password": "password123",
        "full_name": "Audit Price Tester", "organization_name": "Audit Price Org",
    })
    org_id = await _get_org_id_for_user(db_session, "audit_price@example.com")
    listing = await _setup_listing(db_session, org_id, "aprice_01", price_amount=6000, quantity=3, currency_code="USD", price_divisor=100)

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "price_amount", "operation": "set", "operation_value": 6288},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with (
        patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock, return_value={"ok": True}),
    ):
        r_apply = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})
    apply_job_id = r_apply.json()["id"]

    rows = await _get_field_audit_rows(db_session, org_id, apply_job_id)
    assert len(rows) == 1
    assert rows[0].field_name == "price_amount"
    assert rows[0].result_status == "success"
    assert rows[0].extra_data["before"] == 6000
    assert rows[0].extra_data["after"] == 6288


async def test_audit_record_written_for_failed_apply_item():
    """Direct unit test of the audit-writer for the failure path (no live
    Etsy call, no HTTP layer needed) -- confirms a failed/skipped item still
    gets an audit row with the sanitized error, not silently dropped."""
    from app.services.bulk_edit_apply import _write_field_audit_trail

    db = AsyncMock()
    listing = MagicMock(id="listing-1", etsy_listing_id="999")
    added = []
    db.add = MagicMock(side_effect=lambda obj: added.append(obj))
    db.flush = AsyncMock()

    await _write_field_audit_trail(
        db, "org-1", "user-1", "shop-1", listing, "job-1", "session-1",
        {"title": {"before": "A", "after": "B"}}, {"title": "append"},
        "failed", "Client error '400 Bad Request' for url: https://openapi.etsy.com/...",
    )

    assert len(added) == 1
    row = added[0]
    assert row.result_status == "failed"
    assert row.field_name == "title"
    assert row.extra_data["error_message"] is not None
    # error message is stored, but the diagnostics are size-limited -- never unbounded raw response
    assert len(row.extra_data["error_message"]) <= 500


async def test_audit_trail_updates_with_revert_outcome(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="audit_revert@example.com", org_name="Audit Revert Org", etsy_prefix="arev",
    )

    with (
        patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock, return_value={"state": "active"}),
        patch("app.services.bulk_edit_revert.fetch_current_listing_for_conflict_check", new_callable=AsyncMock, return_value=None),
        patch(
            "app.services.bulk_edit_revert.detect_revert_conflict",
            return_value={"has_conflict": False, "conflicting_fields": [], "unverified_fields": [], "reason": None},
        ),
    ):
        r = await client.post(f"{APPLY_JOBS_URL}/{apply_job_id}/revert", headers={"Authorization": f"Bearer {token}"})
    revert_job_id = r.json()["id"]

    rows = await _get_field_audit_rows(db_session, org_id, apply_job_id)
    assert len(rows) == 1
    assert rows[0].revert_job_id == revert_job_id
    assert rows[0].revert_status == "completed"


async def test_audit_trail_endpoint_filters_by_apply_job_and_result_status(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="audit_filter@example.com", org_name="Audit Filter Org", etsy_prefix="afilt",
    )

    r = await client.get(
        f"/api/v1/bulk-edit/audit-trail?apply_job_id={apply_job_id}&result_status=success",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["field_name"] == "title"

    r_none = await client.get(
        f"/api/v1/bulk-edit/audit-trail?apply_job_id={apply_job_id}&result_status=failed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_none.json()["total"] == 0


async def test_audit_trail_endpoint_is_org_isolated(client, db_session):
    token_a, org_a, apply_job_a, _, _ = await _setup_and_apply(
        client, db_session, email="audit_org_a@example.com", org_name="Audit Org A", etsy_prefix="aorga",
    )
    token_b, org_b, apply_job_b, _, _ = await _setup_and_apply(
        client, db_session, email="audit_org_b@example.com", org_name="Audit Org B", etsy_prefix="aorgb",
    )

    r = await client.get("/api/v1/bulk-edit/audit-trail", headers={"Authorization": f"Bearer {token_a}"})
    ids = {item["apply_job_id"] for item in r.json()["items"]}
    assert apply_job_a in ids
    assert apply_job_b not in ids


async def test_audit_trail_no_secrets_in_extra_data(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="audit_secrets@example.com", org_name="Audit Secrets Org", etsy_prefix="asec",
    )
    r = await client.get(
        f"/api/v1/bulk-edit/audit-trail?apply_job_id={apply_job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    payload_text = str(r.json())
    assert "fake_revert_token" not in payload_text
    assert "Bearer" not in payload_text
    assert "x-api-key" not in payload_text.lower()


# ── M06.04 CSV export (2026-08-31, sprint after PR #123) ────────────────────

EXPORT_URL = "/api/v1/bulk-edit/audit-trail/export.csv"


async def test_export_requires_auth(client):
    r = await client.get(EXPORT_URL)
    assert r.status_code == 403


async def test_export_is_org_scoped(client, db_session):
    token_a, org_a, apply_job_a, _, _ = await _setup_and_apply(
        client, db_session, email="export_org_a@example.com", org_name="Export Org A", etsy_prefix="exporga",
    )
    token_b, org_b, apply_job_b, _, _ = await _setup_and_apply(
        client, db_session, email="export_org_b@example.com", org_name="Export Org B", etsy_prefix="exporgb",
    )

    r = await client.get(EXPORT_URL, headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    body = r.text
    assert apply_job_a in body
    assert apply_job_b not in body


async def test_export_filters_apply(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="export_filter@example.com", org_name="Export Filter Org", etsy_prefix="exfilt",
    )

    r_match = await client.get(
        f"{EXPORT_URL}?apply_job_id={apply_job_id}&result_status=success",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_match.status_code == 200
    lines_match = [l for l in r_match.text.splitlines() if l]
    assert len(lines_match) == 2  # header + 1 data row

    r_none = await client.get(
        f"{EXPORT_URL}?apply_job_id={apply_job_id}&result_status=failed",
        headers={"Authorization": f"Bearer {token}"},
    )
    lines_none = [l for l in r_none.text.splitlines() if l]
    assert len(lines_none) == 1  # header only, no matching rows


async def test_export_csv_headers_and_content_type(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="export_headers@example.com", org_name="Export Headers Org", etsy_prefix="exhdr",
    )
    r = await client.get(EXPORT_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    assert "bulk-edit-audit-trail-" in r.headers["content-disposition"]

    header_line = r.text.splitlines()[0]
    assert header_line == (
        "created_at,organization_id,user_id,etsy_shop_id,listing_id,etsy_listing_id,"
        "field_name,operation,before,after,result_status,revert_status,"
        "apply_job_id,bulk_edit_session_id,revert_job_id,error_message"
    )


async def test_export_before_after_values_appear_correctly(client, db_session):
    token = await _register_and_login(client, {
        "email": "export_price@example.com", "password": "password123",
        "full_name": "Export Price Tester", "organization_name": "Export Price Org",
    })
    org_id = await _get_org_id_for_user(db_session, "export_price@example.com")
    listing = await _setup_listing(db_session, org_id, "exprice_01", price_amount=6000, quantity=3, currency_code="USD", price_divisor=100)

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "price_amount", "operation": "set", "operation_value": 6288},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})
    with (
        patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()),
        patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock, return_value={"ok": True}),
    ):
        r_apply = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})
    apply_job_id = r_apply.json()["id"]

    r = await client.get(f"{EXPORT_URL}?apply_job_id={apply_job_id}", headers={"Authorization": f"Bearer {token}"})
    body = r.text
    assert "price_amount" in body
    assert "6000" in body  # before
    assert "6288" in body  # after


async def test_export_no_secrets_in_csv(client, db_session):
    token, org_id, apply_job_id, session_id, listing = await _setup_and_apply(
        client, db_session, email="export_secrets@example.com", org_name="Export Secrets Org", etsy_prefix="exsec",
    )
    r = await client.get(f"{EXPORT_URL}?apply_job_id={apply_job_id}", headers={"Authorization": f"Bearer {token}"})
    body = r.text
    assert "fake_revert_token" not in body
    assert "Bearer" not in body
    assert "x-api-key" not in body.lower()


async def test_export_object_values_are_not_object_object(client, db_session):
    """before/after that happen to be a dict/list must render as real JSON
    text, never a Python/JS-style '[object Object]'-equivalent placeholder."""
    from app.services.bulk_edit_apply import export_field_audit_trail_csv
    from app.models.audit_log import AuditLog

    token = await _register_and_login(client, {
        "email": "export_object@example.com", "password": "password123",
        "full_name": "Export Object Tester", "organization_name": "Export Object Org",
    })
    org_id = await _get_org_id_for_user(db_session, "export_object@example.com")

    db_session.add(AuditLog(
        organization_id=org_id, user_id=None, event_type="bulk_edit_field_write",
        entity_type="listing", entity_id="listing-obj-1", apply_job_id="job-obj-1",
        field_name="tags", result_status="success",
        extra_data={"before": ["old", "tags"], "after": ["new", "tags", "here"]},
    ))
    await db_session.commit()

    csv_text = await export_field_audit_trail_csv(db_session, org_id, apply_job_id="job-obj-1")
    assert "object Object" not in csv_text
    assert "old" in csv_text and "tags" in csv_text and "new" in csv_text
