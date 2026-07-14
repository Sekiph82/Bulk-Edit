"""Tests for action queue endpoint."""

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
        "terms_accepted": True,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


@pytest.mark.anyio
async def test_action_queue_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/action-queue")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_action_queue_empty(client: AsyncClient):
    token = await _register_and_login(client, "aq_u1@test.com", "AQOrg1")
    resp = await client.get(
        "/api/v1/action-queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
