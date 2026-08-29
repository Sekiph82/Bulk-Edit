"""Tests for bulk create endpoint."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
        "terms_accepted": True,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    return result.scalar_one().organization_id


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
async def test_bulk_create_status_ok_with_connected_shop(client: AsyncClient, db_session):
    """Regression test: get_bulk_create_status() was hardcoded to always
    return "not_configured" regardless of org_id, so the page showed
    "Connect your Etsy shop first" even for an account with a real
    connected shop. Must now agree with the same is_connected check
    Connected Shops / etsy.list_connected_shops() use."""
    from app.models.etsy_shop import EtsyShop

    token = await _register_and_login(client, "bc_u3@test.com", "BCOrg3")
    org_id = await _get_org_id(db_session)
    db_session.add(EtsyShop(
        organization_id=org_id,
        etsy_shop_id="bc_shop_1",
        shop_name="BC Test Shop",
        is_connected=True,
    ))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/bulk-create/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] != "not_configured"


@pytest.mark.anyio
async def test_bulk_create_status_not_configured_with_disconnected_shop_only(client: AsyncClient, db_session):
    """A shop row that exists but is disconnected must not count as configured."""
    from app.models.etsy_shop import EtsyShop

    token = await _register_and_login(client, "bc_u4@test.com", "BCOrg4")
    org_id = await _get_org_id(db_session)
    db_session.add(EtsyShop(
        organization_id=org_id,
        etsy_shop_id="bc_shop_2",
        shop_name="BC Disconnected Shop",
        is_connected=False,
    ))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/bulk-create/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "not_configured"


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
