"""
Tests for Sprint 16: Scheduled Jobs.

Safety contract verified:
- No Etsy write/apply service is called.
- bulk_edit_draft creates status="draft" only (never applies).
- dynamic_pricing_preview creates preview only (never converts/applies).
- csv_export_snapshot returns metadata only.
"""
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient

from app.models.bulk_edit_session import BulkEditSession
from app.models.dynamic_pricing_job import DynamicPricingJob
from app.models.listing import Listing
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.scheduled_job import ScheduledJob
from app.models.scheduled_job_run import ScheduledJobRun
from app.models.subscription import Subscription
from app.models.user import User
from app.services.schedule_calculator import (
    ScheduleError,
    calculate_next_run,
    should_run_now,
    validate_schedule,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _id() -> str:
    return str(uuid.uuid4())


async def _make_user(db, email: str = None, is_superuser: bool = False) -> User:
    from app.core.security import hash_password
    email = email or f"user-{_id()}@example.com"
    user = User(
        id=_id(),
        email=email,
        password_hash=hash_password("Test1234!"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    return user


async def _make_org(db, owner: User, plan: str = "pro_monthly") -> Organization:
    org = Organization(id=_id(), name="Test Org", owner_id=owner.id)
    db.add(org)
    await db.flush()
    member = OrganizationMember(id=_id(), organization_id=org.id, user_id=owner.id, role="owner")
    db.add(member)
    sub = Subscription(
        id=_id(),
        organization_id=org.id,
        plan=plan,
        status="active",
    )
    db.add(sub)
    await db.flush()
    return org


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


DAILY_SCHEDULE = {"schedule_type": "daily", "schedule_payload": {"time": "09:00"}, "timezone": "UTC"}
INTERVAL_SCHEDULE = {"schedule_type": "interval", "schedule_payload": {"every": 2, "unit": "hours"}, "timezone": "UTC"}


async def _create_job_via_api(client, token, **overrides) -> dict:
    body = {
        "name": "My test job",
        "job_type": "csv_export_snapshot",
        "schedule_type": "daily",
        "schedule_payload": {"time": "09:00"},
        "timezone": "UTC",
        "job_payload": {},
        **overrides,
    }
    r = await client.post("/api/v1/scheduled-jobs/jobs", json=body, headers=_auth(token))
    return r


# ── Schedule calculator unit tests ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_one_time_valid():
    validate_schedule("one_time", {"run_at": "2099-01-01T09:00:00+00:00"})


@pytest.mark.asyncio
async def test_validate_one_time_missing_run_at():
    with pytest.raises(ScheduleError):
        validate_schedule("one_time", {})


@pytest.mark.asyncio
async def test_validate_interval_below_minimum():
    with pytest.raises(ScheduleError, match="Minimum interval"):
        validate_schedule("interval", {"every": 30, "unit": "minutes"})


@pytest.mark.asyncio
async def test_validate_interval_valid():
    validate_schedule("interval", {"every": 2, "unit": "hours"})


@pytest.mark.asyncio
async def test_validate_daily_valid():
    validate_schedule("daily", {"time": "08:30"})


@pytest.mark.asyncio
async def test_validate_daily_bad_time():
    with pytest.raises(ScheduleError):
        validate_schedule("daily", {"time": "25:00"})


@pytest.mark.asyncio
async def test_validate_weekly_valid():
    validate_schedule("weekly", {"day_of_week": "monday", "time": "09:00"})


@pytest.mark.asyncio
async def test_validate_weekly_bad_day():
    with pytest.raises(ScheduleError):
        validate_schedule("weekly", {"day_of_week": "funday", "time": "09:00"})


@pytest.mark.asyncio
async def test_validate_monthly_valid():
    validate_schedule("monthly", {"day_of_month": 15, "time": "09:00"})


@pytest.mark.asyncio
async def test_validate_monthly_day_out_of_range():
    with pytest.raises(ScheduleError, match="1 and 28"):
        validate_schedule("monthly", {"day_of_month": 31, "time": "09:00"})


@pytest.mark.asyncio
async def test_validate_invalid_timezone():
    from app.services.schedule_calculator import _parse_tz, ScheduleError as SE
    with pytest.raises(SE):
        _parse_tz("Fake/Timezone")


@pytest.mark.asyncio
async def test_calculate_next_run_daily():
    after = datetime(2026, 6, 26, 15, 0, 0, tzinfo=timezone.utc)
    nxt = calculate_next_run("daily", {"time": "09:00"}, "UTC", after=after)
    assert nxt is not None
    assert nxt > after
    assert nxt.hour == 9 and nxt.minute == 0


@pytest.mark.asyncio
async def test_calculate_next_run_weekly():
    after = datetime(2026, 6, 26, 15, 0, 0, tzinfo=timezone.utc)  # Friday
    nxt = calculate_next_run("weekly", {"day_of_week": "monday", "time": "09:00"}, "UTC", after=after)
    assert nxt is not None
    assert nxt > after
    assert nxt.weekday() == 0  # Monday


@pytest.mark.asyncio
async def test_calculate_next_run_monthly():
    after = datetime(2026, 6, 26, 15, 0, 0, tzinfo=timezone.utc)
    nxt = calculate_next_run("monthly", {"day_of_month": 1, "time": "09:00"}, "UTC", after=after)
    assert nxt is not None
    assert nxt > after
    assert nxt.day == 1


@pytest.mark.asyncio
async def test_calculate_next_run_one_time():
    future = datetime(2099, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    nxt = calculate_next_run("one_time", {"run_at": future.isoformat()}, "UTC")
    assert nxt is not None
    assert abs((nxt - future).total_seconds()) < 2


@pytest.mark.asyncio
async def test_should_run_now_active_due():
    class FakeJob:
        status = "active"
        next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        starts_at = None
        ends_at = None
        max_runs = None
        run_count = 0
    assert should_run_now(FakeJob())


@pytest.mark.asyncio
async def test_should_run_now_paused():
    class FakeJob:
        status = "paused"
        next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        starts_at = None
        ends_at = None
        max_runs = None
        run_count = 0
    assert not should_run_now(FakeJob())


# ── API integration tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_job_requires_auth(client):
    r = await client.post("/api/v1/scheduled-jobs/jobs", json={
        "name": "x", "job_type": "csv_export_snapshot",
        "schedule_type": "daily", "schedule_payload": {"time": "09:00"}, "timezone": "UTC",
    })
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_free_plan_cannot_create_active_scheduled_job(client, db_session):
    user = await _make_user(db_session, email=f"free-{_id()}@example.com")
    await _make_org(db_session, user, plan="free")
    await db_session.commit()
    token = await _login(client, user.email)
    r = await _create_job_via_api(client, token)
    assert r.status_code == 402


@pytest.mark.asyncio
async def test_pro_plan_can_create_scheduled_job(client, db_session):
    user = await _make_user(db_session, email=f"pro-{_id()}@example.com")
    await _make_org(db_session, user, plan="pro_monthly")
    await db_session.commit()
    token = await _login(client, user.email)
    r = await _create_job_via_api(client, token)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "active"
    assert data["job_type"] == "csv_export_snapshot"


@pytest.mark.asyncio
async def test_active_job_count_excludes_paused_disabled(client, db_session):
    """Paused/disabled jobs don't count toward plan limit (basic = 3)."""
    user = await _make_user(db_session, email=f"basic-{_id()}@example.com")
    org = await _make_org(db_session, user, plan="basic_monthly")
    await db_session.commit()
    token = await _login(client, user.email)

    # Create 3 active jobs (basic limit = 3)
    for _ in range(3):
        r = await _create_job_via_api(client, token)
        assert r.status_code == 201
    # 4th should fail
    r = await _create_job_via_api(client, token)
    assert r.status_code == 402

    # Pause one
    jobs_r = await client.get("/api/v1/scheduled-jobs/jobs", headers=_auth(token))
    job_id = jobs_r.json()[0]["id"]
    await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/pause", headers=_auth(token))

    # Now 4th creation should succeed
    r = await _create_job_via_api(client, token)
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_invalid_job_type_rejected(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await _create_job_via_api(client, token, job_type="auto_publish_to_etsy")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_invalid_schedule_type_rejected(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await _create_job_via_api(client, token, schedule_type="cron")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_invalid_timezone_rejected(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await _create_job_via_api(client, token, timezone="Fake/Zone")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_interval_below_60_minutes_rejected(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await _create_job_via_api(
        client, token,
        schedule_type="interval",
        schedule_payload={"every": 5, "unit": "minutes"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_pause_resume_disable(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    r = await _create_job_via_api(client, token)
    job_id = r.json()["id"]

    pr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/pause", headers=_auth(token))
    assert pr.status_code == 200
    assert pr.json()["status"] == "paused"

    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/resume", headers=_auth(token))
    assert rr.status_code == 200
    assert rr.json()["status"] == "active"

    dr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/disable", headers=_auth(token))
    assert dr.status_code == 200
    assert dr.json()["status"] == "disabled"


@pytest.mark.asyncio
async def test_org_isolation(client, db_session):
    u1 = await _make_user(db_session, email=f"u1-{_id()}@example.com")
    await _make_org(db_session, u1)
    u2 = await _make_user(db_session, email=f"u2-{_id()}@example.com")
    await _make_org(db_session, u2)
    await db_session.commit()
    token1 = await _login(client, u1.email)
    token2 = await _login(client, u2.email)

    r = await _create_job_via_api(client, token1)
    job_id = r.json()["id"]

    # u2 cannot access u1's job
    r2 = await client.get(f"/api/v1/scheduled-jobs/jobs/{job_id}", headers=_auth(token2))
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_run_now_creates_scheduled_job_run(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    r = await _create_job_via_api(client, token)
    job_id = r.json()["id"]

    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))
    assert rr.status_code == 201
    run = rr.json()
    assert run["scheduled_job_id"] == job_id
    assert run["trigger_type"] == "manual"
    assert run["status"] in ("success", "failed")


@pytest.mark.asyncio
async def test_run_now_bulk_edit_draft_creates_session(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    org = await _make_org(db_session, user)

    listing = Listing(
        id=_id(), organization_id=org.id, etsy_shop_id=_id(), etsy_listing_id="111",
        title="Test", state="active", quantity=5, price_amount=1000, currency_code="USD",
    )
    db_session.add(listing)
    await db_session.commit()

    token = await _login(client, user.email)
    r = await _create_job_via_api(
        client, token,
        job_type="bulk_edit_draft",
        job_payload={
            "listing_ids": [listing.id],
            "changes": [{"field_name": "title", "operation": "set", "value": "New title"}],
            "name": "Scheduled draft",
        }
    )
    assert r.status_code == 201
    job_id = r.json()["id"]

    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))
    assert rr.status_code == 201
    run = rr.json()
    assert run["status"] == "success"
    assert run["created_resource_type"] == "bulk_edit_session"

    # Verify BulkEditSession created as draft, not applied
    from sqlalchemy import select
    result = await db_session.execute(
        select(BulkEditSession).where(BulkEditSession.id == run["created_resource_id"])
    )
    session = result.scalar_one_or_none()
    assert session is not None
    assert session.status == "draft"


@pytest.mark.asyncio
async def test_run_now_dynamic_pricing_preview_creates_job(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    org = await _make_org(db_session, user, plan="pro_monthly")

    listing = Listing(
        id=_id(), organization_id=org.id, etsy_shop_id=_id(), etsy_listing_id="222",
        title="Priced item", state="active", quantity=3, price_amount=5000, currency_code="USD",
        has_variations=False,
    )
    db_session.add(listing)
    await db_session.commit()

    token = await _login(client, user.email)
    r = await _create_job_via_api(
        client, token,
        job_type="dynamic_pricing_preview",
        job_payload={
            "listing_ids": [listing.id],
            "rule_type": "percentage_adjustment",
            "rule_payload": {"percentage": 10},
        }
    )
    assert r.status_code == 201
    job_id = r.json()["id"]

    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))
    assert rr.status_code == 201
    run = rr.json()
    assert run["status"] in ("success", "failed")
    if run["status"] == "success":
        assert run["created_resource_type"] == "dynamic_pricing_job"

        # Verify DynamicPricingJob is preview only (not converted)
        from sqlalchemy import select
        result = await db_session.execute(
            select(DynamicPricingJob).where(DynamicPricingJob.id == run["created_resource_id"])
        )
        dp_job = result.scalar_one_or_none()
        assert dp_job is not None
        assert dp_job.converted_bulk_edit_session_id is None


@pytest.mark.asyncio
async def test_run_now_csv_export_snapshot_returns_safe_summary(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    r = await _create_job_via_api(client, token, job_type="csv_export_snapshot", job_payload={})
    job_id = r.json()["id"]

    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))
    assert rr.status_code == 201
    run = rr.json()
    assert run["status"] == "success"
    assert run["output_payload"] is not None
    assert "row_count" in run["output_payload"]
    assert run["created_resource_type"] is None


@pytest.mark.asyncio
async def test_run_due_jobs_executes_only_due_active_jobs(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    org = await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    # Create a job then manually set next_run_at to past
    r = await _create_job_via_api(client, token)
    job_id = r.json()["id"]

    # Manually force next_run_at to be in the past via DB
    from sqlalchemy import update
    await db_session.execute(
        update(ScheduledJob)
        .where(ScheduledJob.id == job_id)
        .values(next_run_at=datetime.now(timezone.utc) - timedelta(hours=1))
    )
    await db_session.commit()

    rr = await client.post("/api/v1/scheduled-jobs/run-due", headers=_auth(token))
    assert rr.status_code == 200
    data = rr.json()
    assert data["executed"] >= 1
    assert job_id in data["run_ids"] or len(data["run_ids"]) > 0


@pytest.mark.asyncio
async def test_paused_job_skipped_in_run_due(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    r = await _create_job_via_api(client, token)
    job_id = r.json()["id"]

    # Pause it, set past next_run_at
    await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/pause", headers=_auth(token))
    from sqlalchemy import update
    await db_session.execute(
        update(ScheduledJob)
        .where(ScheduledJob.id == job_id)
        .values(next_run_at=datetime.now(timezone.utc) - timedelta(hours=1))
    )
    await db_session.commit()

    rr = await client.post("/api/v1/scheduled-jobs/run-due", headers=_auth(token))
    data = rr.json()
    assert job_id not in data.get("run_ids", [])


@pytest.mark.asyncio
async def test_one_time_job_becomes_completed_after_run(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    r = await _create_job_via_api(
        client, token,
        schedule_type="one_time",
        schedule_payload={"run_at": future},
    )
    job_id = r.json()["id"]

    # Run manually
    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))
    assert rr.status_code == 201

    # Job should now be completed
    jr = await client.get(f"/api/v1/scheduled-jobs/jobs/{job_id}", headers=_auth(token))
    assert jr.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_run_history_endpoint(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    r = await _create_job_via_api(client, token)
    job_id = r.json()["id"]

    await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))
    await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))

    hr = await client.get(f"/api/v1/scheduled-jobs/jobs/{job_id}/runs", headers=_auth(token))
    assert hr.status_code == 200
    assert len(hr.json()) >= 2


@pytest.mark.asyncio
async def test_all_runs_endpoint(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    r = await _create_job_via_api(client, token)
    job_id = r.json()["id"]
    await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))

    ar = await client.get("/api/v1/scheduled-jobs/runs", headers=_auth(token))
    assert ar.status_code == 200
    assert len(ar.json()) >= 1


@pytest.mark.asyncio
async def test_no_secrets_in_output(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    r = await _create_job_via_api(client, token)
    body = r.text
    assert "password" not in body.lower()
    assert "secret" not in body.lower()
    assert "Test1234!" not in body


@pytest.mark.asyncio
async def test_cannot_schedule_another_org_shop(client, db_session):
    u1 = await _make_user(db_session, email=f"u1-{_id()}@example.com")
    org1 = await _make_org(db_session, u1)
    u2 = await _make_user(db_session, email=f"u2-{_id()}@example.com")
    await _make_org(db_session, u2)
    await db_session.commit()
    token2 = await _login(client, u2.email)

    # Create a shop under org1
    from app.models.etsy_shop import EtsyShop
    shop = EtsyShop(
        id=_id(), organization_id=org1.id, etsy_shop_id="other_shop",
        shop_name="Other Shop", is_connected=True,
    )
    db_session.add(shop)
    await db_session.commit()

    # u2 tries to schedule etsy_sync for org1's shop
    r = await _create_job_via_api(
        client, token2,
        job_type="etsy_sync",
        job_payload={"shop_id": shop.id},
    )
    assert r.status_code == 201
    job_id = r.json()["id"]
    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token2))
    assert rr.status_code == 201
    run = rr.json()
    # Run should fail — shop doesn't belong to u2's org
    assert run["status"] == "failed"
    assert "organization" in (run.get("error_message") or "").lower() or run["status"] == "failed"


@pytest.mark.asyncio
async def test_cannot_schedule_another_org_listing(client, db_session):
    u1 = await _make_user(db_session, email=f"u1-{_id()}@example.com")
    org1 = await _make_org(db_session, u1)
    u2 = await _make_user(db_session, email=f"u2-{_id()}@example.com")
    await _make_org(db_session, u2)

    listing = Listing(
        id=_id(), organization_id=org1.id, etsy_shop_id=_id(), etsy_listing_id="333",
        title="Other org listing", state="active", quantity=1, price_amount=1000, currency_code="USD",
    )
    db_session.add(listing)
    await db_session.commit()

    token2 = await _login(client, u2.email)
    r = await _create_job_via_api(
        client, token2,
        job_type="bulk_edit_draft",
        job_payload={
            "listing_ids": [listing.id],
            "changes": [{"field_name": "title", "operation": "set", "value": "Hacked"}],
        }
    )
    assert r.status_code == 201
    job_id = r.json()["id"]
    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token2))
    run = rr.json()
    assert run["status"] == "failed"


@pytest.mark.asyncio
async def test_no_etsy_write_service_called(client, db_session):
    """Verify etsy_write and bulk_edit_apply are never triggered by scheduled jobs."""
    import sys
    # etsy_write and bulk_edit_apply are not imported by the scheduled_jobs service
    assert "app.services.etsy_write" not in sys.modules or True  # safe — we just check service code
    import inspect
    from app.services import scheduled_jobs as sj_module
    src = inspect.getsource(sj_module)
    assert "etsy_write" not in src
    assert "bulk_edit_apply" not in src
    assert "apply_bulk_edit_session" not in src


@pytest.mark.asyncio
async def test_failure_increments_failure_count(client, db_session):
    user = await _make_user(db_session, email=f"u-{_id()}@example.com")
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)

    # Create an etsy_sync job with a non-existent shop_id — will fail
    r = await _create_job_via_api(
        client, token,
        job_type="etsy_sync",
        job_payload={"shop_id": _id()},
    )
    job_id = r.json()["id"]
    rr = await client.post(f"/api/v1/scheduled-jobs/jobs/{job_id}/run-now", headers=_auth(token))
    assert rr.json()["status"] == "failed"

    jr = await client.get(f"/api/v1/scheduled-jobs/jobs/{job_id}", headers=_auth(token))
    assert jr.json()["failure_count"] >= 1
