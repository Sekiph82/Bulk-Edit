"""Tests for insights endpoint."""

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
async def test_insights_summary_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/insights/summary")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_insights_summary_ok(client: AsyncClient):
    token = await _register_and_login(client, "ins_u1@test.com", "InsOrg1")
    resp = await client.get(
        "/api/v1/insights/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "date_from" in data
    assert "date_to" in data
    assert "total_views" in data
    assert "total_revenue_cents" in data


@pytest.mark.anyio
async def test_insights_summary_date_range(client: AsyncClient):
    token = await _register_and_login(client, "ins_u2@test.com", "InsOrg2")
    resp = await client.get(
        "/api/v1/insights/summary?date_from=2026-01-01&date_to=2026-01-31",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["date_from"] == "2026-01-01"
    assert data["date_to"] == "2026-01-31"
