"""
Tests for Sprint 17: Admin Panel.

Security contract verified:
- All endpoints require is_superuser=True (403 for regular users, 401 for unauthenticated).
- No password_hash returned in any response.
- No Etsy access_token/refresh_token returned in shop responses.
- Stripe secret keys never returned (only stripe_customer_id).
- No destructive deletes.
"""
import uuid
import pytest
from httpx import AsyncClient

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.subscription import Subscription
from app.models.user import User
from app.models.etsy_shop import EtsyShop
from app.models.scheduled_job import ScheduledJob
from app.models.audit_log import AuditLog


# ── Helpers ──────────────────────────────────────────────────────────────────

def _id() -> str:
    return str(uuid.uuid4())


async def _make_user(db, email: str | None = None, is_superuser: bool = False, is_active: bool = True) -> User:
    from app.core.security import hash_password
    email = email or f"user-{_id()}@example.com"
    user = User(
        id=_id(),
        email=email,
        password_hash=hash_password("Test1234!"),
        full_name="Test User",
        is_active=is_active,
        is_verified=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    return user


async def _make_org(db, owner: User, plan: str = "pro_monthly") -> Organization:
    org = Organization(id=_id(), name=f"Org-{_id()[:8]}", owner_id=owner.id)
    db.add(org)
    await db.flush()
    member = OrganizationMember(id=_id(), organization_id=org.id, user_id=owner.id, role="owner")
    db.add(member)
    sub = Subscription(id=_id(), organization_id=org.id, plan=plan, status="active")
    db.add(sub)
    await db.flush()
    return org


async def _make_shop(db, org: Organization) -> EtsyShop:
    shop = EtsyShop(
        id=_id(),
        organization_id=org.id,
        etsy_shop_id=f"shop-{_id()[:8]}",
        shop_name="Test Shop",
        is_connected=True,
    )
    db.add(shop)
    await db.flush()
    return shop


async def _make_scheduled_job(db, org: Organization, status: str = "active") -> ScheduledJob:
    job = ScheduledJob(
        id=_id(),
        organization_id=org.id,
        name="Test Job",
        job_type="etsy_sync",
        status=status,
        schedule_type="interval",
        schedule_payload={"interval_minutes": 60},
        timezone="UTC",
    )
    db.add(job)
    await db.flush()
    return job


async def _login(client: AsyncClient, email: str, password: str = "Test1234!") -> str:
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── 1. Authorization checks ───────────────────────────────────────────────────

async def test_admin_overview_unauthenticated(client):
    r = await client.get("/api/v1/admin/overview")
    assert r.status_code == 403  # HTTPBearer returns 403 for missing Authorization header


async def test_admin_overview_regular_user_forbidden(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/overview", headers=_auth(token))
    assert r.status_code == 403


async def test_admin_list_users_forbidden(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/users", headers=_auth(token))
    assert r.status_code == 403


async def test_admin_list_organizations_forbidden(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/organizations", headers=_auth(token))
    assert r.status_code == 403


async def test_admin_list_events_forbidden(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/events", headers=_auth(token))
    assert r.status_code == 403


async def test_admin_disable_user_unauthenticated(client):
    r = await client.post(f"/api/v1/admin/users/{_id()}/disable")
    assert r.status_code == 403  # HTTPBearer returns 403 for missing Authorization header


# ── 2. Overview ───────────────────────────────────────────────────────────────

async def test_admin_overview_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/overview", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "total_users" in data
    assert "total_organizations" in data
    assert "active_subscriptions" in data
    assert "paid_subscriptions" in data
    assert "total_listings" in data
    assert "total_scheduled_jobs" in data
    assert "total_ai_sessions" in data
    assert "total_csv_jobs" in data
    assert data["total_users"] >= 1
    assert data["total_organizations"] >= 1


async def test_admin_overview_counts_increase_with_data(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)

    r1 = await client.get("/api/v1/admin/overview", headers=_auth(token))
    before = r1.json()["total_users"]

    await _make_user(db_session)
    await db_session.commit()

    r2 = await client.get("/api/v1/admin/overview", headers=_auth(token))
    after = r2.json()["total_users"]
    assert after == before + 1


# ── 3. User list ──────────────────────────────────────────────────────────────

async def test_admin_list_users_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 1


async def test_admin_list_users_no_password_hash(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users", headers=_auth(token))
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert "password_hash" not in item
        assert "password" not in item


async def test_admin_list_users_pagination(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    for _ in range(3):
        await _make_user(db_session)
    await db_session.commit()
    token = await _login(client, su.email)

    r = await client.get("/api/v1/admin/users?page=1&page_size=2", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 4


async def test_admin_list_users_page_size_capped_at_100(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users?page_size=200", headers=_auth(token))
    assert r.status_code == 422  # FastAPI rejects >100 via Query(le=100)


# ── 4. User detail ────────────────────────────────────────────────────────────

async def test_admin_user_detail_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    target = await _make_user(db_session)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/users/{target.id}", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == target.id
    assert data["email"] == target.email
    assert "password_hash" not in data


async def test_admin_user_detail_not_found(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/users/{_id()}", headers=_auth(token))
    assert r.status_code == 404


# ── 5. Organization list + detail ─────────────────────────────────────────────

async def test_admin_list_organizations_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/organizations", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    item = data["items"][0]
    assert "id" in item
    assert "name" in item
    assert "owner_id" in item


async def test_admin_organization_detail_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/organizations/{org.id}", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == org.id
    assert "subscription" in data
    assert "shop_count" in data
    assert "listing_count" in data
    assert data["subscription"]["plan"] == "pro_monthly"


async def test_admin_organization_detail_not_found(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/organizations/{_id()}", headers=_auth(token))
    assert r.status_code == 404


# ── 6. Subscription list ──────────────────────────────────────────────────────

async def test_admin_list_subscriptions_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/subscriptions", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    sub = data["items"][0]
    assert "stripe_subscription_id" not in sub
    assert "stripe_price_id" not in sub


async def test_admin_subscriptions_no_stripe_secrets(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/subscriptions", headers=_auth(token))
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert "stripe_subscription_id" not in item
        assert "stripe_price_id" not in item


# ── 7. Usage ──────────────────────────────────────────────────────────────────

async def test_admin_list_usage_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/usage", headers=_auth(token))
    assert r.status_code == 200
    assert "items" in r.json()


# ── 8. Shops ──────────────────────────────────────────────────────────────────

async def test_admin_list_shops_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    await _make_shop(db_session, org)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/shops", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["total"] >= 1


async def test_admin_shops_no_etsy_tokens(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    await _make_shop(db_session, org)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/shops", headers=_auth(token))
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert "access_token" not in item
        assert "refresh_token" not in item


# ── 9. Sync jobs ──────────────────────────────────────────────────────────────

async def test_admin_list_sync_jobs_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/sync-jobs", headers=_auth(token))
    assert r.status_code == 200
    assert "items" in r.json()


# ── 10. Bulk edit sessions ────────────────────────────────────────────────────

async def test_admin_list_bulk_edit_sessions_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/bulk-edit-sessions", headers=_auth(token))
    assert r.status_code == 200
    assert "items" in r.json()


# ── 11. AI sessions ───────────────────────────────────────────────────────────

async def test_admin_list_ai_sessions_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/ai-sessions", headers=_auth(token))
    assert r.status_code == 200
    assert "items" in r.json()


# ── 12. CSV jobs ──────────────────────────────────────────────────────────────

async def test_admin_list_csv_jobs_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/csv-jobs", headers=_auth(token))
    assert r.status_code == 200
    assert "items" in r.json()


# ── 13. Dynamic pricing jobs ──────────────────────────────────────────────────

async def test_admin_list_dynamic_pricing_jobs_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/dynamic-pricing-jobs", headers=_auth(token))
    assert r.status_code == 200
    assert "items" in r.json()


# ── 14. Scheduled jobs ────────────────────────────────────────────────────────

async def test_admin_list_scheduled_jobs_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    await _make_scheduled_job(db_session, org)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/scheduled-jobs", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["total"] >= 1


# ── 15. Scheduled job runs ────────────────────────────────────────────────────

async def test_admin_list_scheduled_job_runs_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/scheduled-job-runs", headers=_auth(token))
    assert r.status_code == 200
    assert "items" in r.json()


# ── 16. Audit events ──────────────────────────────────────────────────────────

async def test_admin_list_events_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    log = AuditLog(
        id=_id(),
        organization_id=org.id,
        user_id=su.id,
        event_type="admin.test",
        entity_type="user",
        entity_id=su.id,
        message="test event",
    )
    db_session.add(log)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/events", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    event = data["items"][0]
    assert "event_type" in event
    assert "organization_id" in event


# ── 17. Disable / Enable user ─────────────────────────────────────────────────

async def test_admin_disable_user_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    target = await _make_user(db_session)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/users/{target.id}/disable", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["ok"] is True

    detail = await client.get(f"/api/v1/admin/users/{target.id}", headers=_auth(token))
    assert detail.json()["is_active"] is False


async def test_admin_enable_user_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    target = await _make_user(db_session, is_active=False)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/users/{target.id}/enable", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["ok"] is True

    detail = await client.get(f"/api/v1/admin/users/{target.id}", headers=_auth(token))
    assert detail.json()["is_active"] is True


async def test_admin_disable_self_forbidden(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/users/{su.id}/disable", headers=_auth(token))
    assert r.status_code == 400


async def test_admin_disable_user_not_found(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/users/{_id()}/disable", headers=_auth(token))
    assert r.status_code == 404


# ── 18. Pause / Resume scheduled job ─────────────────────────────────────────

async def test_admin_pause_scheduled_job_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    job = await _make_scheduled_job(db_session, org, status="active")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/scheduled-jobs/{job.id}/pause", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["ok"] is True


async def test_admin_resume_scheduled_job_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    job = await _make_scheduled_job(db_session, org, status="paused")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/scheduled-jobs/{job.id}/resume", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["ok"] is True


async def test_admin_pause_already_paused_job_fails(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    job = await _make_scheduled_job(db_session, org, status="paused")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/scheduled-jobs/{job.id}/pause", headers=_auth(token))
    assert r.status_code == 400


async def test_admin_resume_active_job_fails(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    job = await _make_scheduled_job(db_session, org, status="active")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/scheduled-jobs/{job.id}/resume", headers=_auth(token))
    assert r.status_code == 400


async def test_admin_pause_job_not_found(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/scheduled-jobs/{_id()}/pause", headers=_auth(token))
    assert r.status_code == 404


# ── 19. Pagination correctness ────────────────────────────────────────────────

async def test_admin_pagination_page2(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    for _ in range(4):
        await _make_user(db_session)
    await db_session.commit()
    token = await _login(client, su.email)

    r1 = await client.get("/api/v1/admin/users?page=1&page_size=2", headers=_auth(token))
    r2 = await client.get("/api/v1/admin/users?page=2&page_size=2", headers=_auth(token))
    assert r1.status_code == 200
    assert r2.status_code == 200
    ids1 = {u["id"] for u in r1.json()["items"]}
    ids2 = {u["id"] for u in r2.json()["items"]}
    assert ids1.isdisjoint(ids2)


# ── 20. Action response has no destructive data ───────────────────────────────

async def test_admin_action_response_shape(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    target = await _make_user(db_session)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.post(f"/api/v1/admin/users/{target.id}/disable", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data
    assert "message" in data
    assert "password_hash" not in data


async def test_admin_organization_detail_with_shop(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    await _make_shop(db_session, org)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/organizations/{org.id}", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["shop_count"] == 1


# ── 21. Users list search/filter ──────────────────────────────────────────────

async def test_admin_list_users_search_by_email(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    target = await _make_user(db_session, email="findme-unique@example.com")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users?q=findme-unique", headers=_auth(token))
    assert r.status_code == 200
    ids = {u["id"] for u in r.json()["items"]}
    assert target.id in ids


async def test_admin_list_users_filter_status_disabled(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    disabled = await _make_user(db_session, is_active=False)
    active = await _make_user(db_session, is_active=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users?status=disabled", headers=_auth(token))
    assert r.status_code == 200
    ids = {u["id"] for u in r.json()["items"]}
    assert disabled.id in ids
    assert active.id not in ids


async def test_admin_list_users_filter_role_superuser(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    other_su = await _make_user(db_session, is_superuser=True)
    regular = await _make_user(db_session, is_superuser=False)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users?role=superuser", headers=_auth(token))
    assert r.status_code == 200
    ids = {u["id"] for u in r.json()["items"]}
    assert other_su.id in ids
    assert regular.id not in ids


async def test_admin_list_users_filter_organization_id(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    member = await _make_user(db_session)
    org = await _make_org(db_session, member)
    outsider = await _make_user(db_session)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/users?organization_id={org.id}", headers=_auth(token))
    assert r.status_code == 200
    ids = {u["id"] for u in r.json()["items"]}
    assert member.id in ids
    assert outsider.id not in ids


async def test_admin_list_users_filter_plan(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    pro_user = await _make_user(db_session)
    await _make_org(db_session, pro_user, plan="pro_monthly")
    free_user = await _make_user(db_session)
    await _make_org(db_session, free_user, plan="free")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users?plan=pro_monthly", headers=_auth(token))
    assert r.status_code == 200
    ids = {u["id"] for u in r.json()["items"]}
    assert pro_user.id in ids
    assert free_user.id not in ids


async def test_admin_list_users_includes_primary_org_and_plan(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    owner = await _make_user(db_session)
    org = await _make_org(db_session, owner, plan="basic_monthly")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/users", headers=_auth(token))
    assert r.status_code == 200
    item = next(u for u in r.json()["items"] if u["id"] == owner.id)
    assert item["organization_id"] == org.id
    assert item["organization_name"] == org.name
    assert item["plan"] == "basic_monthly"


# ── 22. Organizations list search/filter ──────────────────────────────────────

async def test_admin_list_organizations_search_by_name(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    owner = await _make_user(db_session)
    org = Organization(id=_id(), name="Unique Findable Org", owner_id=owner.id)
    db_session.add(org)
    await db_session.flush()
    db_session.add(OrganizationMember(id=_id(), organization_id=org.id, user_id=owner.id, role="owner"))
    db_session.add(Subscription(id=_id(), organization_id=org.id, plan="free", status="free"))
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/organizations?q=Unique Findable", headers=_auth(token))
    assert r.status_code == 200
    ids = {o["id"] for o in r.json()["items"]}
    assert org.id in ids


async def test_admin_list_organizations_filter_plan(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    pro_owner = await _make_user(db_session)
    pro_org = await _make_org(db_session, pro_owner, plan="pro_monthly")
    free_owner = await _make_user(db_session)
    free_org = await _make_org(db_session, free_owner, plan="free")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/organizations?plan=pro_monthly", headers=_auth(token))
    assert r.status_code == 200
    ids = {o["id"] for o in r.json()["items"]}
    assert pro_org.id in ids
    assert free_org.id not in ids


async def test_admin_list_organizations_filter_etsy_connected(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    connected_owner = await _make_user(db_session)
    connected_org = await _make_org(db_session, connected_owner)
    await _make_shop(db_session, connected_org)
    disconnected_owner = await _make_user(db_session)
    disconnected_org = await _make_org(db_session, disconnected_owner)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/organizations?etsy_connected=true", headers=_auth(token))
    assert r.status_code == 200
    ids = {o["id"] for o in r.json()["items"]}
    assert connected_org.id in ids
    assert disconnected_org.id not in ids


async def test_admin_list_organizations_includes_enrichment_fields(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    owner = await _make_user(db_session, email="org-owner@example.com")
    org = await _make_org(db_session, owner, plan="pro_monthly")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/organizations", headers=_auth(token))
    assert r.status_code == 200
    item = next(o for o in r.json()["items"] if o["id"] == org.id)
    assert item["owner_email"] == "org-owner@example.com"
    assert item["plan"] == "pro_monthly"
    assert item["subscription_status"] == "active"
    assert item["etsy_connected"] is False
    assert item["users_count"] == 1


# ── 23. User detail enrichment ────────────────────────────────────────────────

async def test_admin_user_detail_includes_organizations_and_usage(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    owner = await _make_user(db_session)
    org = await _make_org(db_session, owner, plan="basic_monthly")
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/users/{owner.id}", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["organizations"][0]["organization_id"] == org.id
    assert data["organizations"][0]["role"] == "owner"
    assert data["plan"] == "basic_monthly"
    assert "usage" in data
    assert data["usage"]["bulk_edit_sessions_count"] == 0
    assert "recent_events" in data
    assert "password_hash" not in data


# ── 24. Organization detail enrichment ────────────────────────────────────────

async def test_admin_organization_detail_includes_members_usage_risk(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    owner = await _make_user(db_session, email="member-owner@example.com")
    org = await _make_org(db_session, owner)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/organizations/{org.id}", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["members"][0]["email"] == "member-owner@example.com"
    assert data["members"][0]["role"] == "owner"
    assert "usage" in data
    assert data["usage"]["media_jobs_count"] == 0
    assert "risk" in data
    assert data["risk"]["etsy_disconnected"] is False  # no shops at all yet
    assert data["risk"]["billing_issue"] is False
    assert "recent_events" in data


async def test_admin_organization_detail_no_etsy_tokens_in_shops(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    await _make_shop(db_session, org)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/organizations/{org.id}", headers=_auth(token))
    assert r.status_code == 200
    for shop in r.json()["shops"]:
        assert "access_token" not in shop
        assert "refresh_token" not in shop


async def test_admin_organization_detail_etsy_disconnected_risk_flag(client, db_session):
    from app.models.etsy_shop import EtsyShop

    su = await _make_user(db_session, is_superuser=True)
    org = await _make_org(db_session, su)
    shop = EtsyShop(id=_id(), organization_id=org.id, etsy_shop_id=f"shop-{_id()[:8]}", shop_name="Disconnected Shop", is_connected=False)
    db_session.add(shop)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get(f"/api/v1/admin/organizations/{org.id}", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["risk"]["etsy_disconnected"] is True


# ── 25. Trends endpoint ────────────────────────────────────────────────────────

async def test_admin_trends_forbidden_for_regular_user(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/metrics/trends", headers=_auth(token))
    assert r.status_code == 403


async def test_admin_trends_default_30_days(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/metrics/trends", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["days"] == 30
    assert len(data["series"]["users"]) == 30
    assert len(data["series"]["organizations"]) == 30
    assert len(data["series"]["bulk_edit_jobs"]) == 30
    assert len(data["series"]["media_jobs"]) == 30


async def test_admin_trends_zero_filled_no_fake_data(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/metrics/trends?days=7", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["days"] == 7
    for point in data["series"]["bulk_edit_jobs"]:
        assert point["count"] == 0  # no bulk edit sessions created in this test
    for point in data["series"]["users"] + data["series"]["organizations"]:
        assert "date" in point and "count" in point


async def test_admin_trends_counts_todays_new_user(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)

    from datetime import datetime, timezone
    today_key = datetime.now(timezone.utc).date().isoformat()

    r = await client.get("/api/v1/admin/metrics/trends?days=1", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["series"]["users"][0]["date"] == today_key
    assert data["series"]["users"][0]["count"] >= 1  # su was just created today


async def test_admin_trends_days_capped(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/metrics/trends?days=999", headers=_auth(token))
    assert r.status_code == 422  # FastAPI rejects >365 via Query(le=365)
