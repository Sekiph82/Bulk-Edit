"""Tests for bulk create endpoint."""

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


@pytest.mark.anyio
async def test_bulk_create_status_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/bulk-create/status")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_bulk_create_status_not_configured(client: AsyncClient):
    token = await _register_and_login(client, "bc_u1@test.com", "BCOrg1")
    resp = await client.get(
        "/api/v1/bulk-create/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_configured"


@pytest.mark.anyio
async def test_bulk_create_drafts_not_configured(client: AsyncClient):
    token = await _register_and_login(client, "bc_u2@test.com", "BCOrg2")
    resp = await client.post(
        "/api/v1/bulk-create/drafts",
        json={"title": "Test listing", "description": "A test", "price_cents": 1000},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_configured"
