"""Tests for video generator endpoint."""

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
async def test_video_status_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/video-generator/status")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_video_status_not_configured(client: AsyncClient):
    token = await _register_and_login(client, "vid_u1@test.com", "VidOrg1")
    resp = await client.get(
        "/api/v1/video-generator/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "renderer_enabled" in data
    assert data["renderer_enabled"] is False
    assert "message" in data
