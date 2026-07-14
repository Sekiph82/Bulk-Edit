"""Tests for promote endpoint."""

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.social_connection import SocialConnection
from app.models.social_oauth_state import SocialOAuthState
from app.core.encryption import encrypt_token

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(client: AsyncClient, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
        "terms_accepted": True,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


async def _get_org_id(client: AsyncClient, token: str) -> str:
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    data = r.json()
    return data["memberships"][0]["organization_id"]


# ---------------------------------------------------------------------------
# config-status
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_promote_config_public_no_auth_needed(client: AsyncClient):
    """config-status is public — no auth required."""
    resp = await client.get("/api/v1/promote/config-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "pinterest_configured" in data
    assert "instagram_configured" in data


@pytest.mark.anyio
async def test_promote_config_returns_false_when_unconfigured(client: AsyncClient):
    resp = await client.get("/api/v1/promote/config-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pinterest_configured"] is False
    assert data["instagram_configured"] is False
    assert "pinterest_missing_vars" not in data
    assert "instagram_missing_vars" not in data


@pytest.mark.anyio
async def test_promote_config_does_not_expose_var_names(client: AsyncClient):
    """config-status must not leak env var names to callers."""
    data = (await client.get("/api/v1/promote/config-status")).json()
    response_str = str(data)
    assert "PINTEREST_CLIENT_ID" not in response_str
    assert "PINTEREST_CLIENT_SECRET" not in response_str
    assert "META_APP_ID" not in response_str
    assert "META_APP_SECRET" not in response_str
    assert "INSTAGRAM_REDIRECT_URI" not in response_str


# ---------------------------------------------------------------------------
# connect-url
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pinterest_connect_url_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/promote/pinterest/connect-url")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_pinterest_connect_url_503_when_not_configured(client: AsyncClient):
    token = await _register_and_login(client, "pu1@test.com", "PuOrg1")
    resp = await client.get(
        "/api/v1/promote/pinterest/connect-url",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 503


@pytest.mark.anyio
async def test_instagram_connect_url_503_when_not_configured(client: AsyncClient):
    token = await _register_and_login(client, "iu1@test.com", "IuOrg1")
    resp = await client.get(
        "/api/v1/promote/instagram/connect-url",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 503


@pytest.mark.anyio
async def test_pinterest_connect_url_returns_authorization_url_when_configured(client: AsyncClient):
    token = await _register_and_login(client, "pu2@test.com", "PuOrg2")
    with patch("app.api.v1.promote._is_pinterest_configured", return_value=True), \
         patch("app.api.v1.promote.settings") as mock_settings:
        mock_settings.PINTEREST_CLIENT_ID = "test_client_id"
        mock_settings.PINTEREST_CLIENT_SECRET = "test_secret"
        mock_settings.PINTEREST_REDIRECT_URI = "http://localhost:8100/api/v1/promote/pinterest/callback"
        resp = await client.get(
            "/api/v1/promote/pinterest/connect-url",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "pinterest" in data["url"]
    assert data["platform"] == "pinterest"


# ---------------------------------------------------------------------------
# status endpoints
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pinterest_status_not_connected_when_no_row(client: AsyncClient):
    token = await _register_and_login(client, "ps1@test.com", "PsOrg1")
    with patch("app.api.v1.promote._is_pinterest_configured", return_value=True):
        resp = await client.get(
            "/api/v1/promote/pinterest/status",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "not_connected"
    assert data["connected"] is False


@pytest.mark.anyio
async def test_pinterest_status_connected_returns_account_info(client: AsyncClient, db_session):
    token = await _register_and_login(client, "ps2@test.com", "PsOrg2")
    org_id = await _get_org_id(client, token)

    db_session.add(SocialConnection(
        organization_id=org_id,
        platform="pinterest",
        status="connected",
        access_token_encrypted=encrypt_token("fake_token"),
        token_type="Bearer",
        account_name="Test User",
        username="testuser",
        external_account_id="pinterest_123",
    ))
    await db_session.commit()

    with patch("app.api.v1.promote._is_pinterest_configured", return_value=True):
        resp = await client.get(
            "/api/v1/promote/pinterest/status",
            headers={"Authorization": f"Bearer {token}"},
        )
    data = resp.json()
    assert data["state"] == "connected"
    assert data["connected"] is True
    assert data["account_name"] == "Test User"
    assert data["username"] == "testuser"
    assert data["external_account_id"] == "pinterest_123"


@pytest.mark.anyio
async def test_pinterest_status_no_token_in_response(client: AsyncClient, db_session):
    token = await _register_and_login(client, "ps3@test.com", "PsOrg3")
    org_id = await _get_org_id(client, token)

    db_session.add(SocialConnection(
        organization_id=org_id,
        platform="pinterest",
        status="connected",
        access_token_encrypted=encrypt_token("super_secret_token"),
        token_type="Bearer",
    ))
    await db_session.commit()

    with patch("app.api.v1.promote._is_pinterest_configured", return_value=True):
        resp = await client.get(
            "/api/v1/promote/pinterest/status",
            headers={"Authorization": f"Bearer {token}"},
        )
    content = resp.text
    assert "super_secret_token" not in content
    assert "access_token_encrypted" not in content
    assert "encrypted" not in content.lower() or "access_token_encrypted" not in content


@pytest.mark.anyio
async def test_instagram_status_no_token_in_response(client: AsyncClient, db_session):
    token = await _register_and_login(client, "is1@test.com", "IsOrg1")
    org_id = await _get_org_id(client, token)

    db_session.add(SocialConnection(
        organization_id=org_id,
        platform="instagram",
        status="connected",
        access_token_encrypted=encrypt_token("ig_secret_token"),
        token_type="Bearer",
    ))
    await db_session.commit()

    with patch("app.api.v1.promote._is_instagram_configured", return_value=True):
        resp = await client.get(
            "/api/v1/promote/instagram/status",
            headers={"Authorization": f"Bearer {token}"},
        )
    content = resp.text
    assert "ig_secret_token" not in content
    assert "access_token_encrypted" not in content


# ---------------------------------------------------------------------------
# OAuth callback — popup HTML
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pinterest_callback_bad_state_returns_html_error(client: AsyncClient):
    resp = await client.get(
        "/api/v1/promote/pinterest/callback?code=abc&state=bad_state_value",
    )
    assert resp.status_code == 200
    assert "window.close" in resp.text
    assert '"error"' in resp.text
    assert "bulk-edit-social-oauth" in resp.text


@pytest.mark.anyio
async def test_instagram_callback_bad_state_returns_html_error(client: AsyncClient):
    resp = await client.get(
        "/api/v1/promote/instagram/callback?code=abc&state=bad_state_value",
    )
    assert resp.status_code == 200
    assert "window.close" in resp.text
    assert '"error"' in resp.text


@pytest.mark.anyio
async def test_pinterest_callback_missing_code_returns_html_error(client: AsyncClient):
    resp = await client.get("/api/v1/promote/pinterest/callback?state=somestate")
    assert resp.status_code == 200
    assert "window.close" in resp.text
    assert '"error"' in resp.text


@pytest.mark.anyio
async def test_pinterest_callback_error_param_returns_html_error(client: AsyncClient):
    resp = await client.get(
        "/api/v1/promote/pinterest/callback?error=access_denied&state=s"
    )
    assert resp.status_code == 200
    assert '"error"' in resp.text
    assert "window.close" in resp.text


@pytest.mark.anyio
async def test_pinterest_callback_html_never_contains_token(client: AsyncClient, db_session):
    token = await _register_and_login(client, "cb1@test.com", "CbOrg1")
    org_id = await _get_org_id(client, token)

    state_value = "test_state_value_123"
    state_hash = hashlib.sha256(state_value.encode()).hexdigest()
    db_session.add(SocialOAuthState(
        organization_id=org_id,
        user_id="user-123",
        platform="pinterest",
        state_hash=state_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    ))
    await db_session.commit()

    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.json.return_value = {
        "access_token": "real_pinterest_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "boards:read",
    }

    with patch("app.api.v1.promote._is_pinterest_configured", return_value=True), \
         patch("app.api.v1.promote._fetch_pinterest_account", new=AsyncMock(return_value={})), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        resp = await client.get(
            f"/api/v1/promote/pinterest/callback?code=auth_code&state={state_value}",
        )

    assert resp.status_code == 200
    html = resp.text
    assert "real_pinterest_access_token_12345" not in html
    assert "auth_code" not in html
    assert "Bearer " not in html
    assert "window.close" in html


@pytest.mark.anyio
async def test_pinterest_callback_expired_state_returns_html_error(client: AsyncClient, db_session):
    token = await _register_and_login(client, "cb2@test.com", "CbOrg2")
    org_id = await _get_org_id(client, token)

    state_value = "expired_state_value"
    state_hash = hashlib.sha256(state_value.encode()).hexdigest()
    db_session.add(SocialOAuthState(
        organization_id=org_id,
        user_id="user-123",
        platform="pinterest",
        state_hash=state_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    ))
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/promote/pinterest/callback?code=abc&state={state_value}",
    )
    assert resp.status_code == 200
    assert '"error"' in resp.text
    assert "window.close" in resp.text


@pytest.mark.anyio
async def test_pinterest_callback_consumed_state_returns_html_error(client: AsyncClient, db_session):
    token = await _register_and_login(client, "cb3@test.com", "CbOrg3")
    org_id = await _get_org_id(client, token)

    state_value = "consumed_state_value"
    state_hash = hashlib.sha256(state_value.encode()).hexdigest()
    db_session.add(SocialOAuthState(
        organization_id=org_id,
        user_id="user-123",
        platform="pinterest",
        state_hash=state_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        consumed_at=datetime.now(timezone.utc),  # already consumed
    ))
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/promote/pinterest/callback?code=abc&state={state_value}",
    )
    assert resp.status_code == 200
    assert '"error"' in resp.text
    assert "window.close" in resp.text


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pinterest_disconnect_clears_token_sets_revoked(client: AsyncClient, db_session):
    token = await _register_and_login(client, "dc1@test.com", "DcOrg1")
    org_id = await _get_org_id(client, token)

    db_session.add(SocialConnection(
        organization_id=org_id,
        platform="pinterest",
        status="connected",
        access_token_encrypted=encrypt_token("some_token"),
        token_type="Bearer",
    ))
    await db_session.commit()

    resp = await client.delete(
        "/api/v1/promote/pinterest/disconnect",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    from sqlalchemy import select as sa_select
    from app.models.social_connection import SocialConnection as SC
    result = await db_session.execute(
        sa_select(SC).where(SC.organization_id == org_id, SC.platform == "pinterest")
    )
    conn = result.scalar_one_or_none()
    assert conn is not None
    assert conn.status == "revoked"
    assert conn.access_token_encrypted is None


# ---------------------------------------------------------------------------
# share endpoints
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pinterest_share_requires_connected(client: AsyncClient):
    token = await _register_and_login(client, "sh1@test.com", "ShOrg1")
    with patch("app.api.v1.promote._is_pinterest_configured", return_value=True):
        resp = await client.post(
            "/api/v1/promote/pinterest/share",
            json={"caption": "Test caption"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_instagram_share_requires_connected(client: AsyncClient):
    token = await _register_and_login(client, "sh2@test.com", "ShOrg2")
    with patch("app.api.v1.promote._is_instagram_configured", return_value=True):
        resp = await client.post(
            "/api/v1/promote/instagram/share",
            json={"caption": "Test caption"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_pinterest_share_returns_deferred_not_fake_success(client: AsyncClient, db_session):
    token = await _register_and_login(client, "sh3@test.com", "ShOrg3")
    org_id = await _get_org_id(client, token)

    db_session.add(SocialConnection(
        organization_id=org_id,
        platform="pinterest",
        status="connected",
        access_token_encrypted=encrypt_token("token"),
        token_type="Bearer",
    ))
    await db_session.commit()

    resp = await client.post(
        "/api/v1/promote/pinterest/share",
        json={"caption": "Check out my listing!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["deferred"] is True
    assert "not fully enabled" in data["message"]


@pytest.mark.anyio
async def test_instagram_share_returns_deferred_not_fake_success(client: AsyncClient, db_session):
    token = await _register_and_login(client, "sh4@test.com", "ShOrg4")
    org_id = await _get_org_id(client, token)

    db_session.add(SocialConnection(
        organization_id=org_id,
        platform="instagram",
        status="connected",
        access_token_encrypted=encrypt_token("ig_token"),
        token_type="Bearer",
    ))
    await db_session.commit()

    resp = await client.post(
        "/api/v1/promote/instagram/share",
        json={"caption": "Check out my listing!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["deferred"] is True


# ---------------------------------------------------------------------------
# listings
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_promote_listings_empty_when_no_listings(client: AsyncClient):
    token = await _register_and_login(client, "ls1@test.com", "LsOrg1")
    resp = await client.get(
        "/api/v1/promote/listings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["empty"] is True
    assert data["listings"] == []
    assert "Sync" in data["message"]


@pytest.mark.anyio
async def test_promote_listings_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/promote/listings")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# org isolation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_social_connection_org_isolated(client: AsyncClient, db_session):
    token_a = await _register_and_login(client, "iso1@test.com", "IsoOrgA")
    token_b = await _register_and_login(client, "iso2@test.com", "IsoOrgB")
    org_a = await _get_org_id(client, token_a)

    db_session.add(SocialConnection(
        organization_id=org_a,
        platform="pinterest",
        status="connected",
        access_token_encrypted=encrypt_token("org_a_token"),
        token_type="Bearer",
        account_name="Org A User",
    ))
    await db_session.commit()

    # Org B should not see Org A's connection
    with patch("app.api.v1.promote._is_pinterest_configured", return_value=True):
        resp_b = await client.get(
            "/api/v1/promote/pinterest/status",
            headers={"Authorization": f"Bearer {token_b}"},
        )
    data = resp_b.json()
    assert data["state"] == "not_connected"
    assert data.get("account_name") is None


@pytest.mark.anyio
async def test_share_org_isolated_listing(client: AsyncClient, db_session):
    """Share should fail if listing_id belongs to different org."""
    token_a = await _register_and_login(client, "iso3@test.com", "IsoOrgC")
    token_b = await _register_and_login(client, "iso4@test.com", "IsoOrgD")
    org_b = await _get_org_id(client, token_b)

    # Org B has connected Pinterest
    db_session.add(SocialConnection(
        organization_id=org_b,
        platform="pinterest",
        status="connected",
        access_token_encrypted=encrypt_token("org_b_token"),
        token_type="Bearer",
    ))
    await db_session.commit()

    # Org A creates a listing (we reference a fake ID)
    resp = await client.post(
        "/api/v1/promote/pinterest/share",
        json={"caption": "Test", "listing_id": "nonexistent-listing-id-from-other-org"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # listing_id doesn't exist in org_b's scope → 404
    assert resp.status_code == 404
