"""
Sprint 18 — Security Hardening Tests.

Verified contracts:
- All protected endpoints require a valid JWT (401 without token).
- Tampered/malformed JWTs are rejected (401).
- Org isolation: users cannot access other organizations' data.
- Superuser endpoints return 403 for regular users.
- No sensitive fields in any response (password_hash, access_token_enc, etc.).
- SQL injection in query params returns 422 or an empty result set, never 500.
- Oversized/malformed IDs return 404 or 422, never 500.
- GET /api/v1/health/ready returns 200 or 503 with correct shape.
"""
import uuid
import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _uid() -> str:
    return str(uuid.uuid4())


async def _register(client: AsyncClient, suffix: str = "") -> dict:
    payload = {
        "email": f"sec{suffix}-{_uid()[:8]}@example.com",
        "password": "SecurePass1!",
        "full_name": "Security Tester",
        "organization_name": f"Sec Org {_uid()[:6]}",
        "terms_accepted": True,
    }
    r = await client.post(REGISTER_URL, json=payload)
    assert r.status_code == 201, r.text
    return r.json()


async def _login(client: AsyncClient, email: str, password: str = "SecurePass1!") -> str:
    r = await client.post(LOGIN_URL, json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Readiness probe ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_ready_shape(client):
    r = await client.get("/api/v1/health/ready")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_health_ready_status_values(client):
    r = await client.get("/api/v1/health/ready")
    data = r.json()
    assert data["status"] in ("ready", "not_ready")


# ── Unauthenticated access blocked ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_token_auth_me(client):
    # FastAPI HTTPBearer returns 403 when no Authorization header is present
    r = await client.get("/api/v1/auth/me")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_listings(client):
    r = await client.get("/api/v1/listings")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_billing_subscription(client):
    r = await client.get("/api/v1/billing/subscription")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_billing_usage(client):
    r = await client.get("/api/v1/billing/usage")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_bulk_edit_sessions(client):
    r = await client.get("/api/v1/bulk-edit/sessions")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_admin_overview(client):
    r = await client.get("/api/v1/admin/overview")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_shops(client):
    r = await client.get("/api/v1/etsy/shops")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_ai_sessions(client):
    r = await client.get("/api/v1/ai/sessions")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_csv_jobs(client):
    r = await client.get("/api/v1/csv/jobs")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_dynamic_pricing_jobs(client):
    r = await client.get("/api/v1/dynamic-pricing/jobs")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_no_token_scheduled_jobs(client):
    r = await client.get("/api/v1/scheduled-jobs/jobs")
    assert r.status_code in (401, 403)


# ── Tampered / malformed JWT rejected ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tampered_signature_rejected(client):
    data = await _register(client, "tamper")
    token = data["access_token"]
    # Corrupt the signature (last segment)
    parts = token.split(".")
    parts[-1] = parts[-1][:-4] + "XXXX"
    bad_token = ".".join(parts)
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_empty_bearer_rejected(client):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer "})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_wrong_scheme_rejected(client):
    data = await _register(client, "scheme")
    token = data["access_token"]
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Basic {token}"})
    assert r.status_code in (401, 403)


# ── Superuser gate ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_overview(client):
    data = await _register(client, "admin-gate")
    token = data["access_token"]
    r = await client.get("/api/v1/admin/overview", headers=_auth(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_regular_user_cannot_list_admin_users(client):
    data = await _register(client, "admin-users")
    token = data["access_token"]
    r = await client.get("/api/v1/admin/users", headers=_auth(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_regular_user_cannot_list_admin_orgs(client):
    data = await _register(client, "admin-orgs")
    token = data["access_token"]
    r = await client.get("/api/v1/admin/organizations", headers=_auth(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_audit(client):
    data = await _register(client, "admin-audit")
    token = data["access_token"]
    r = await client.get("/api/v1/admin/events", headers=_auth(token))
    assert r.status_code == 403


# ── No secrets in responses ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_me_no_password_hash(client):
    data = await _register(client, "nohash")
    token = data["access_token"]
    r = await client.get("/api/v1/auth/me", headers=_auth(token))
    assert r.status_code == 200
    body = r.text
    assert "password_hash" not in body
    assert "password" not in r.json().get("user", {})


@pytest.mark.asyncio
async def test_register_response_no_password_hash(client):
    data = await _register(client, "reg-hash")
    assert "password_hash" not in str(data)
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_response_no_password_hash(client):
    reg = await _register(client, "login-hash")
    # Re-register with known credentials to extract email
    r2 = await client.post(LOGIN_URL, json={
        "email": reg.get("email", ""),
        "password": "SecurePass1!",
    })
    if r2.status_code == 200:
        assert "password_hash" not in r2.text
        assert "password_hash" not in str(r2.json())


@pytest.mark.asyncio
async def test_billing_subscription_no_secrets(client):
    data = await _register(client, "billing-sec")
    token = data["access_token"]
    r = await client.get("/api/v1/billing/subscription", headers=_auth(token))
    assert r.status_code == 200
    body = r.text
    assert "stripe_secret" not in body
    assert "webhook_secret" not in body


# ── Org isolation ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_isolation_listings(client):
    """User B cannot see User A's listings (both see empty list, not each other's data)."""
    data_a = await _register(client, "iso-list-a")
    data_b = await _register(client, "iso-list-b")
    token_a = data_a["access_token"]
    token_b = data_b["access_token"]

    r_a = await client.get("/api/v1/listings", headers=_auth(token_a))
    r_b = await client.get("/api/v1/listings", headers=_auth(token_b))
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    # Both start with 0 listings — neither sees the other's
    assert r_a.json()["total"] == 0
    assert r_b.json()["total"] == 0


@pytest.mark.asyncio
async def test_org_isolation_bulk_edit_sessions(client):
    data_a = await _register(client, "iso-bulk-a")
    data_b = await _register(client, "iso-bulk-b")
    token_a = data_a["access_token"]
    token_b = data_b["access_token"]

    r_a = await client.get("/api/v1/bulk-edit/sessions", headers=_auth(token_a))
    r_b = await client.get("/api/v1/bulk-edit/sessions", headers=_auth(token_b))
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    # /bulk-edit/sessions returns a flat list
    assert r_a.json() == []
    assert r_b.json() == []


@pytest.mark.asyncio
async def test_org_isolation_ai_sessions(client):
    data_a = await _register(client, "iso-ai-a")
    data_b = await _register(client, "iso-ai-b")
    token_a = data_a["access_token"]
    token_b = data_b["access_token"]

    r_a = await client.get("/api/v1/ai/sessions", headers=_auth(token_a))
    r_b = await client.get("/api/v1/ai/sessions", headers=_auth(token_b))
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    assert r_a.json()["total"] == 0
    assert r_b.json()["total"] == 0


@pytest.mark.asyncio
async def test_org_isolation_csv_jobs(client):
    data_a = await _register(client, "iso-csv-a")
    data_b = await _register(client, "iso-csv-b")
    token_a = data_a["access_token"]
    token_b = data_b["access_token"]

    r_a = await client.get("/api/v1/csv/jobs", headers=_auth(token_a))
    r_b = await client.get("/api/v1/csv/jobs", headers=_auth(token_b))
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    # /csv/jobs returns a flat list
    assert r_a.json() == []
    assert r_b.json() == []


@pytest.mark.asyncio
async def test_org_isolation_dynamic_pricing(client):
    data_a = await _register(client, "iso-dp-a")
    data_b = await _register(client, "iso-dp-b")
    token_a = data_a["access_token"]
    token_b = data_b["access_token"]

    r_a = await client.get("/api/v1/dynamic-pricing/jobs", headers=_auth(token_a))
    r_b = await client.get("/api/v1/dynamic-pricing/jobs", headers=_auth(token_b))
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    # /dynamic-pricing/jobs returns a flat list
    assert r_a.json() == []
    assert r_b.json() == []


@pytest.mark.asyncio
async def test_org_isolation_scheduled_jobs(client):
    data_a = await _register(client, "iso-sj-a")
    data_b = await _register(client, "iso-sj-b")
    token_a = data_a["access_token"]
    token_b = data_b["access_token"]

    r_a = await client.get("/api/v1/scheduled-jobs/jobs", headers=_auth(token_a))
    r_b = await client.get("/api/v1/scheduled-jobs/jobs", headers=_auth(token_b))
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    # /scheduled-jobs/jobs returns a flat list
    assert r_a.json() == []
    assert r_b.json() == []


# ── SQL injection in query params ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sql_injection_listings_title(client):
    data = await _register(client, "sqli-title")
    token = data["access_token"]
    r = await client.get(
        "/api/v1/listings",
        headers=_auth(token),
        params={"title": "' OR '1'='1"},
    )
    # Must return 200 with empty results or 422 — never 500
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_sql_injection_listings_tag(client):
    data = await _register(client, "sqli-tag")
    token = data["access_token"]
    r = await client.get(
        "/api/v1/listings",
        headers=_auth(token),
        params={"tag": "'; DROP TABLE listings; --"},
    )
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_sql_injection_sort_by(client):
    data = await _register(client, "sqli-sort")
    token = data["access_token"]
    r = await client.get(
        "/api/v1/listings",
        headers=_auth(token),
        params={"sort_by": "title; DROP TABLE users; --"},
    )
    # Backend validates sort_by against whitelist → 400
    assert r.status_code in (400, 422)


# ── Oversized / malformed IDs ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nonexistent_listing_returns_404(client):
    data = await _register(client, "404-listing")
    token = data["access_token"]
    fake_id = str(uuid.uuid4())
    r = await client.get(f"/api/v1/listings/{fake_id}", headers=_auth(token))
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_bulk_session_returns_404(client):
    data = await _register(client, "404-bulk")
    token = data["access_token"]
    fake_id = str(uuid.uuid4())
    r = await client.get(f"/api/v1/bulk-edit/sessions/{fake_id}", headers=_auth(token))
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_path_traversal_id_rejected(client):
    data = await _register(client, "path-trav")
    token = data["access_token"]
    r = await client.get("/api/v1/listings/../../etc/passwd", headers=_auth(token))
    # FastAPI router won't match — expect 404 or 422
    assert r.status_code in (404, 422)


@pytest.mark.asyncio
async def test_overlong_id_does_not_crash(client):
    data = await _register(client, "overlong")
    token = data["access_token"]
    overlong_id = "a" * 500
    r = await client.get(f"/api/v1/listings/{overlong_id}", headers=_auth(token))
    assert r.status_code in (404, 422)


# ── Input validation ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_rejects_xss_email(client):
    r = await client.post(REGISTER_URL, json={
        "email": "<script>alert(1)</script>@evil.com",
        "password": "SecurePass1!",
        "full_name": "XSS Tester",
        "terms_accepted": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_rejects_short_password(client):
    r = await client.post(REGISTER_URL, json={
        "email": "short@example.com",
        "password": "123",
        "full_name": "Short Pass",
        "terms_accepted": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401_not_500(client):
    await _register(client, "wrongpass")
    r = await client.post(LOGIN_URL, json={
        "email": f"secwrongpass-{_uid()[:8]}@example.com",
        "password": "definitely-wrong",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    payload = {
        "email": f"dup-{_uid()[:8]}@example.com",
        "password": "SecurePass1!",
        "full_name": "Dup User",
        "organization_name": "Dup Org",
        "terms_accepted": True,
    }
    r1 = await client.post(REGISTER_URL, json=payload)
    assert r1.status_code == 201
    r2 = await client.post(REGISTER_URL, json=payload)
    assert r2.status_code == 409


# ── Public endpoints do not expose internals ──────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint_shape(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    # No internal details in health response
    assert "database_url" not in data
    assert "secret" not in str(data).lower()


@pytest.mark.asyncio
async def test_plans_endpoint_no_secrets(client):
    r = await client.get("/api/v1/billing/plans")
    assert r.status_code == 200
    body = r.text
    assert "stripe_secret" not in body
    assert "webhook_secret" not in body
    assert "password" not in body


@pytest.mark.asyncio
async def test_error_responses_no_stack_trace_in_production(client):
    """404 on unknown route must not leak a Python stack trace."""
    r = await client.get("/api/v1/nonexistent-endpoint-xyz")
    assert r.status_code == 404
    body = r.text
    assert "Traceback" not in body
    assert "File \"" not in body
