"""Tests for Sprint 19 admin business dashboard endpoints."""
import uuid
import pytest
from httpx import AsyncClient

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.subscription import Subscription
from app.models.user import User


# ── Helpers ───────────────────────────────────────────────────────────────────

def _id() -> str:
    return str(uuid.uuid4())


async def _make_user(db, is_superuser: bool = False) -> User:
    from app.core.security import hash_password
    user = User(
        id=_id(),
        email=f"user-{_id()}@example.com",
        password_hash=hash_password("Test1234!"),
        full_name="Test",
        is_active=True,
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
    db.add(OrganizationMember(id=_id(), organization_id=org.id, user_id=owner.id, role="owner"))
    db.add(Subscription(id=_id(), organization_id=org.id, plan=plan, status="active"))
    await db.flush()
    return org


async def _login(client: AsyncClient, email: str) -> str:
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "Test1234!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── billing-summary ───────────────────────────────────────────────────────────

async def test_billing_summary_requires_auth(client):
    r = await client.get("/api/v1/admin/billing-summary")
    assert r.status_code == 403


async def test_billing_summary_requires_superuser(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/billing-summary", headers=_auth(token))
    assert r.status_code == 403


async def test_billing_summary_superuser_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/billing-summary", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    for field in [
        "total_subscriptions", "free_plan_count", "basic_monthly_count",
        "basic_yearly_count", "pro_monthly_count", "pro_yearly_count",
        "active_count", "trialing_count", "canceled_count",
        "cancel_at_period_end_count", "estimated_monthly_revenue",
    ]:
        assert field in data, f"Missing field: {field}"
    assert data["estimated_monthly_revenue"] >= 0
    assert isinstance(data["estimated_monthly_revenue"], (int, float))


async def test_billing_summary_mrr_field_name_is_estimated(client, db_session):
    """Field must be named 'estimated_monthly_revenue', not 'collected_revenue'."""
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/billing-summary", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "estimated_monthly_revenue" in data
    assert "collected_revenue" not in data


async def test_billing_summary_no_stripe_secrets(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/billing-summary", headers=_auth(token))
    assert "sk_live" not in r.text
    assert "sk_test" not in r.text
    assert "whsec_" not in r.text


# ── stripe-summary ────────────────────────────────────────────────────────────

async def test_stripe_summary_requires_superuser(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/stripe-summary", headers=_auth(token))
    assert r.status_code == 403


async def test_stripe_summary_superuser_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/stripe-summary", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    for field in [
        "total_stripe_customers", "subscriptions_with_stripe_sub",
        "active_stripe_subscriptions", "canceling_at_period_end", "total_billing_events",
    ]:
        assert field in data
        assert data[field] >= 0


# ── product-usage ─────────────────────────────────────────────────────────────

async def test_product_usage_requires_superuser(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/product-usage", headers=_auth(token))
    assert r.status_code == 403


async def test_product_usage_superuser_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/product-usage", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    for field in [
        "total_listings", "total_bulk_edit_sessions", "total_ai_sessions",
        "total_csv_jobs", "total_dynamic_pricing_jobs", "total_sync_jobs", "total_shops",
    ]:
        assert field in data
        assert data[field] >= 0


# ── system-health ─────────────────────────────────────────────────────────────

async def test_system_health_requires_superuser(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/system-health", headers=_auth(token))
    assert r.status_code == 403


async def test_system_health_superuser_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/system-health", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["database_status"] == "ok"
    for field in [
        "total_users", "total_organizations", "total_audit_events",
        "recent_failed_scheduled_runs", "recent_failed_ai_sessions",
    ]:
        assert field in data
        assert data[field] >= 0


# ── audit-log ─────────────────────────────────────────────────────────────────

async def test_audit_log_requires_superuser(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/audit-log", headers=_auth(token))
    assert r.status_code == 403


async def test_audit_log_superuser_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/audit-log", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


async def test_audit_log_pagination(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/audit-log?page=1&page_size=5", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5


# ── /auth/me is_superuser exposure ────────────────────────────────────────────

async def test_me_exposes_is_superuser_false_for_normal_user(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/auth/me", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["user"]["is_superuser"] is False


async def test_me_exposes_is_superuser_true_for_superuser(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/auth/me", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["user"]["is_superuser"] is True


async def test_me_no_password_hash_in_response(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/auth/me", headers=_auth(token))
    assert r.status_code == 200
    assert "password_hash" not in r.text
    assert "password" not in r.json()["user"]


# ── contact-submissions ───────────────────────────────────────────────────────

async def test_contact_submissions_requires_superuser(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/contact-submissions", headers=_auth(token))
    assert r.status_code == 403


async def test_contact_submissions_superuser_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/contact-submissions", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data


# ── feature-flags ─────────────────────────────────────────────────────────────

async def test_feature_flags_requires_superuser(client, db_session):
    user = await _make_user(db_session, is_superuser=False)
    await _make_org(db_session, user)
    await db_session.commit()
    token = await _login(client, user.email)
    r = await client.get("/api/v1/admin/feature-flags", headers=_auth(token))
    assert r.status_code == 403


async def test_feature_flags_superuser_ok(client, db_session):
    su = await _make_user(db_session, is_superuser=True)
    await _make_org(db_session, su)
    await db_session.commit()
    token = await _login(client, su.email)
    r = await client.get("/api/v1/admin/feature-flags", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "flags" in data
    keys = {f["key"] for f in data["flags"]}
    assert "VIDEO_RENDERER_ENABLED" in keys
    for f in data["flags"]:
        assert f["source"] == "env"
