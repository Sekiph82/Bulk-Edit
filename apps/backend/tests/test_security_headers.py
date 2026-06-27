import pytest
import uuid

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.subscription import Subscription
from app.models.user import User


def _id() -> str:
    return str(uuid.uuid4())


async def _make_superuser(db) -> User:
    from app.core.security import hash_password
    user = User(
        id=_id(),
        email=f"su-{_id()}@example.com",
        password_hash=hash_password("Test1234!"),
        full_name="Admin",
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db.add(user)
    await db.flush()
    org = Organization(id=_id(), name=f"Org-{_id()[:8]}", owner_id=user.id)
    db.add(org)
    await db.flush()
    db.add(OrganizationMember(id=_id(), organization_id=org.id, user_id=user.id, role="owner"))
    db.add(Subscription(id=_id(), organization_id=org.id, plan="pro_monthly", status="active"))
    await db.flush()
    return user


async def _superuser_headers(client, db_session) -> dict:
    user = await _make_superuser(db_session)
    await db_session.commit()
    r = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "Test1234!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.anyio
async def test_health_has_security_headers(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "permissions-policy" in r.headers


@pytest.mark.anyio
async def test_api_response_has_security_headers(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"


@pytest.mark.anyio
async def test_cors_still_works(client):
    r = await client.get("/api/v1/health", headers={"Origin": "http://localhost:3100"})
    assert r.status_code == 200
    assert "x-content-type-options" in r.headers


@pytest.mark.anyio
async def test_system_health_has_monitoring_fields(client, db_session):
    """system-health must include redis, rate_limit_backend, sentry_configured, worker_status."""
    headers = await _superuser_headers(client, db_session)
    r = await client.get("/api/v1/admin/system-health", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "redis_status" in data
    assert "rate_limit_backend" in data
    assert "rate_limit_enabled" in data
    assert "sentry_configured" in data
    assert "worker_status" in data
    assert "csp_mode" in data
    # Values sanity
    assert data["redis_status"] in ("ok", "not_configured", "error")
    assert data["rate_limit_backend"] in ("memory", "redis")
    assert isinstance(data["rate_limit_enabled"], bool)
    assert isinstance(data["sentry_configured"], bool)


@pytest.mark.anyio
async def test_system_health_no_redis_url_exposed(client, db_session):
    """system-health must never include raw Redis connection URL."""
    headers = await _superuser_headers(client, db_session)
    r = await client.get("/api/v1/admin/system-health", headers=headers)
    assert r.status_code == 200
    assert "redis://" not in r.text
    assert "REDIS_URL" not in r.text
    assert "56379" not in r.text  # local dev port


@pytest.mark.anyio
async def test_system_health_no_sentry_dsn_exposed(client, db_session):
    """system-health sentry_configured is bool — never the DSN string."""
    headers = await _superuser_headers(client, db_session)
    r = await client.get("/api/v1/admin/system-health", headers=headers)
    assert r.status_code == 200
    assert "sentry.io" not in r.text
    assert "SENTRY_DSN" not in r.text


@pytest.mark.anyio
async def test_system_health_sentry_false_without_dsn(client, db_session):
    """sentry_configured should be False in test env (no DSN set)."""
    headers = await _superuser_headers(client, db_session)
    r = await client.get("/api/v1/admin/system-health", headers=headers)
    assert r.status_code == 200
    assert r.json()["sentry_configured"] is False


@pytest.mark.anyio
async def test_system_health_worker_status_field(client, db_session):
    """worker_status field present — 'not_configured' since no Celery in this deploy."""
    headers = await _superuser_headers(client, db_session)
    r = await client.get("/api/v1/admin/system-health", headers=headers)
    assert r.status_code == 200
    assert r.json()["worker_status"] == "not_configured"
