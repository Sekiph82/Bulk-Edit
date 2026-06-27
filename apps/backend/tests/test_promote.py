"""Tests for promote endpoint."""

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
async def test_promote_config_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/promote/config-status")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_promote_config_ok(client: AsyncClient):
    token = await _register_and_login(client, "prm_u1@test.com", "PrmOrg1")
    resp = await client.get(
        "/api/v1/promote/config-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "pinterest_configured" in data
    assert "instagram_configured" in data
    assert data["pinterest_configured"] is False
    assert data["instagram_configured"] is False
