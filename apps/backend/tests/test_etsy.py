import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
AUTHORIZE_URL = "/api/v1/etsy/authorize"
CALLBACK_URL = "/api/v1/etsy/callback"
SHOPS_URL = "/api/v1/etsy/shops"

VALID_USER = {
    "email": "etsy_test@example.com",
    "password": "password123",
    "full_name": "Etsy Tester",
    "organization_name": "Etsy Test Org",
    "terms_accepted": True,
}


async def _register_and_login(client) -> str:
    await client.post(REGISTER_URL, json=VALID_USER)
    r = await client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    return r.json()["access_token"]


# ---------------------------------------------------------------------------
# Encryption unit tests
# ---------------------------------------------------------------------------

def test_encrypt_decrypt_roundtrip():
    from app.core.encryption import encrypt_token, decrypt_token
    plaintext = "some_secret_access_token_value"
    ciphertext = encrypt_token(plaintext)
    assert ciphertext != plaintext
    assert decrypt_token(ciphertext) == plaintext


def test_encrypt_produces_different_ciphertexts_each_call():
    from app.core.encryption import encrypt_token
    t = "same_token"
    assert encrypt_token(t) != encrypt_token(t)


# ---------------------------------------------------------------------------
# PKCE helper tests
# ---------------------------------------------------------------------------

def test_generate_code_verifier_length():
    from app.services.etsy import generate_code_verifier
    v = generate_code_verifier()
    assert 40 <= len(v) <= 50
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in v)


def test_generate_code_challenge_is_deterministic():
    from app.services.etsy import generate_code_verifier, generate_code_challenge
    v = generate_code_verifier()
    assert generate_code_challenge(v) == generate_code_challenge(v)


def test_code_challenge_differs_from_verifier():
    from app.services.etsy import generate_code_verifier, generate_code_challenge
    v = generate_code_verifier()
    assert generate_code_challenge(v) != v


# ---------------------------------------------------------------------------
# GET /etsy/authorize
# ---------------------------------------------------------------------------

async def test_authorize_503_when_etsy_not_configured(client):
    token = await _register_and_login(client)
    mock_settings = MagicMock()
    mock_settings.is_etsy_configured.return_value = False
    with patch("app.api.v1.etsy.settings", mock_settings):
        r = await client.get(AUTHORIZE_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"].lower()


async def test_authorize_401_without_token(client):
    r = await client.get(AUTHORIZE_URL)
    assert r.status_code == 403


async def test_authorize_returns_url_when_configured(client):
    token = await _register_and_login(client)
    mock_settings = MagicMock()
    mock_settings.is_etsy_configured.return_value = True
    mock_settings.ETSY_CLIENT_ID = "test_client_id"
    mock_settings.ETSY_REDIRECT_URI = "http://localhost:8100/api/v1/etsy/callback"
    mock_settings.ETSY_SCOPES = "listings_r listings_w"
    mock_settings.FRONTEND_URL = "http://localhost:3100"
    with (
        patch("app.api.v1.etsy.settings", mock_settings),
        patch("app.services.etsy.settings", mock_settings),
    ):
        r = await client.get(AUTHORIZE_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "authorization_url" in data
    assert "etsy.com/oauth/connect" in data["authorization_url"]
    assert "code_challenge" in data["authorization_url"]
    assert "state" in data["authorization_url"]


# ---------------------------------------------------------------------------
# GET /etsy/callback
# ---------------------------------------------------------------------------

async def test_callback_redirects_on_error_param(client):
    r = await client.get(f"{CALLBACK_URL}?error=access_denied", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]


async def test_callback_redirects_on_missing_code(client):
    r = await client.get(f"{CALLBACK_URL}?state=somestate", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]


async def test_callback_redirects_on_invalid_state(client):
    r = await client.get(f"{CALLBACK_URL}?code=abc&state=nonexistent_state", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]


async def test_callback_success_flow(client, db_session):
    """Full happy-path: valid state in DB, mock Etsy token exchange and shop fetch."""
    from app.models.etsy_oauth_state import EtsyOAuthState
    from app.services.etsy import generate_code_verifier
    import uuid

    state_val = "valid_state_abc123"
    verifier = generate_code_verifier()
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    record = EtsyOAuthState(
        state=state_val,
        code_verifier=verifier,
        organization_id=org_id,
        user_id=user_id,
        expires_at=expires,
    )
    db_session.add(record)
    await db_session.commit()

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {
        "access_token": "etsy_access_token_value",
        "refresh_token": "etsy_refresh_token_value",
        "expires_in": 3600,
        "user_id": "12345",
    }
    mock_shop_resp = MagicMock()
    mock_shop_resp.raise_for_status = MagicMock()
    mock_shop_resp.json.return_value = {
        "count": 1,
        "results": [{"shop_id": 99999, "shop_name": "My Test Shop"}],
    }

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(return_value=mock_shop_resp)

    with patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "connected=true" in r.headers["location"]


async def test_callback_stores_real_granted_scope_not_token_type(client, db_session):
    """
    Regression test for a real bug: the granted-scope column previously stored
    token_data["token_type"] (always "Bearer") instead of the actual scope
    string Etsy returns. See ETSY_OAUTH_SCOPES.md.
    """
    from app.models.etsy_oauth_state import EtsyOAuthState
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.services.etsy import generate_code_verifier
    from sqlalchemy import select
    import uuid

    state_val = "scope_test_state"
    verifier = generate_code_verifier()
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    db_session.add(EtsyOAuthState(
        state=state_val, code_verifier=verifier, organization_id=org_id,
        user_id=user_id, expires_at=expires,
    ))
    await db_session.commit()

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {
        "access_token": "etsy_access_token_value",
        "refresh_token": "etsy_refresh_token_value",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "listings_r listings_w shops_r profile_r",
    }
    mock_shop_resp = MagicMock()
    mock_shop_resp.raise_for_status = MagicMock()
    mock_shop_resp.json.return_value = {
        "count": 1,
        "results": [{"shop_id": 88888, "shop_name": "Scope Test Shop"}],
    }
    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(return_value=mock_shop_resp)

    with patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)
    assert r.status_code == 302

    result = await db_session.execute(
        select(EtsyToken).join(EtsyShop, EtsyToken.etsy_shop_id == EtsyShop.id)
        .where(EtsyShop.etsy_shop_id == "88888")
    )
    token_row = result.scalar_one()
    assert token_row.scopes == "listings_r listings_w shops_r profile_r"
    assert token_row.scopes != "Bearer"


# ---------------------------------------------------------------------------
# GET /etsy/shops
# ---------------------------------------------------------------------------

async def test_list_shops_empty(client):
    token = await _register_and_login(client)
    r = await client.get(SHOPS_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["shops"] == []


async def test_list_shops_401_without_token(client):
    r = await client.get(SHOPS_URL)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /etsy/shops/{shop_id}
# ---------------------------------------------------------------------------

async def _setup_shop_with_token(db_session, org_id: str, expires_at) -> tuple:
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    import uuid

    shop = EtsyShop(
        organization_id=org_id,
        etsy_shop_id=f"refresh_test_{uuid.uuid4().hex[:8]}",
        shop_name="Refresh Test Shop",
        is_connected=True,
    )
    db_session.add(shop)
    await db_session.flush()

    token = EtsyToken(
        etsy_shop_id=shop.id,
        access_token_enc=encrypt_token("old_access_token"),
        refresh_token_enc=encrypt_token("old_refresh_token"),
        expires_at=expires_at,
        scopes="listings_r listings_w shops_r profile_r",
    )
    db_session.add(token)
    await db_session.commit()
    return shop, token


def _mock_combined_http_client(refresh_access_token: str = "brand_new_access_token", refresh_raises: bool = False):
    """
    IMPORTANT: `app.services.etsy` and `app.services.etsy_sync` both do
    `import httpx` — that's the *same* module object, so `httpx.AsyncClient`
    is one shared attribute. Patching it via both dotted module paths at once
    (`patch("app.services.etsy.httpx.AsyncClient", ...)` AND
    `patch("app.services.etsy_sync.httpx.AsyncClient", ...)` in the same
    `with` block) makes the second patch silently clobber the first, since
    they resolve to the identical target. The fix is a single patch (either
    dotted path works — they're the same object) with one mock client whose
    `.post` (used by refresh_etsy_token) and `.get` (used by
    fetch_shop_listings) are both configured.
    """
    import httpx as httpx_module

    refresh_resp = MagicMock()
    if refresh_raises:
        refresh_resp.status_code = 401
        refresh_resp.raise_for_status = MagicMock(
            side_effect=httpx_module.HTTPStatusError("revoked", request=MagicMock(), response=refresh_resp)
        )
    else:
        refresh_resp.raise_for_status = MagicMock()
        refresh_resp.json.return_value = {
            "access_token": refresh_access_token,
            "refresh_token": "brand_new_refresh_token",
            "expires_in": 3600,
        }

    listings_resp = MagicMock()
    listings_resp.raise_for_status = MagicMock()
    listings_resp.is_success = True
    listings_resp.status_code = 200
    listings_resp.json.return_value = {"count": 0, "results": []}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=refresh_resp)
    mock_client.get = AsyncMock(return_value=listings_resp)
    return mock_client


async def test_sync_auto_refreshes_near_expiry_token(client, db_session):
    """
    Regression test: get_valid_etsy_access_token previously only logged a
    warning and used the stale token when near/past expiry. It must now
    proactively call refresh_etsy_token before the sync proceeds, and store
    the new access token.
    """
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import decrypt_token
    from sqlalchemy import select

    reg_token = await _register_and_login(client)

    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    org_id = result.scalar_one().organization_id

    near_expiry = datetime.now(timezone.utc) + timedelta(seconds=60)  # inside refresh buffer
    shop, _ = await _setup_shop_with_token(db_session, org_id, near_expiry)
    shop_id = shop.id  # capture as plain str before expire_all() below

    with patch("app.services.etsy.httpx.AsyncClient", return_value=_mock_combined_http_client()):
        r = await client.post(f"/api/v1/shops/{shop_id}/sync", headers={"Authorization": f"Bearer {reg_token}"})

    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    db_session.expire_all()
    result = await db_session.execute(select(EtsyToken).where(EtsyToken.etsy_shop_id == shop_id))
    assert decrypt_token(result.scalar_one().access_token_enc) == "brand_new_access_token"


async def test_sync_marks_shop_disconnected_on_revoked_refresh(client, db_session):
    """
    Regression test: if Etsy rejects the refresh (revoked grant), the shop
    must be marked is_connected=False and the sync request must fail with a
    clear client error (not an opaque 500, and not a silent stale-token
    fallback that would have been the pre-fix behavior).
    """
    from app.models.etsy_shop import EtsyShop
    from sqlalchemy import select

    reg_token = await _register_and_login(client)

    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    org_id = result.scalar_one().organization_id

    expired = datetime.now(timezone.utc) - timedelta(hours=1)
    shop, _ = await _setup_shop_with_token(db_session, org_id, expired)
    shop_id = shop.id  # capture as plain str before expire_all() below

    with patch("app.services.etsy.httpx.AsyncClient", return_value=_mock_combined_http_client(refresh_raises=True)):
        r = await client.post(f"/api/v1/shops/{shop_id}/sync", headers={"Authorization": f"Bearer {reg_token}"})

    assert r.status_code in (401, 409)
    assert r.status_code < 500

    db_session.expire_all()
    result = await db_session.execute(select(EtsyShop).where(EtsyShop.id == shop_id))
    assert result.scalar_one().is_connected is False


async def test_disconnect_shop_404_unknown(client):
    token = await _register_and_login(client)
    import uuid
    r = await client.delete(f"/api/v1/etsy/shops/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


async def test_disconnect_shop_deletes_token_and_pauses_scheduled_jobs(client, db_session):
    """
    Regression test: disconnect must delete the stored EtsyToken row (not just
    flip is_connected) and pause active ScheduledJob rows referencing the
    shop. See ETSY_DATA_RETENTION.md §3 — this is what makes the Privacy
    Policy's "disconnecting revokes our stored tokens immediately" claim true.
    """
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.models.scheduled_job import ScheduledJob
    from app.models.organization_member import OrganizationMember
    from app.core.encryption import encrypt_token
    from sqlalchemy import select

    access_token = await _register_and_login(client)

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id

    shop = EtsyShop(
        organization_id=org_id,
        etsy_shop_id="disconnect_test_shop",
        shop_name="Disconnect Test Shop",
        is_connected=True,
    )
    db_session.add(shop)
    await db_session.flush()

    etsy_token = EtsyToken(
        etsy_shop_id=shop.id,
        access_token_enc=encrypt_token("fake_access"),
        refresh_token_enc=encrypt_token("fake_refresh"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scopes="listings_r listings_w shops_r profile_r",
    )
    db_session.add(etsy_token)

    job = ScheduledJob(
        organization_id=org_id,
        name="Nightly sync",
        job_type="etsy_sync",
        status="active",
        schedule_type="daily",
        schedule_payload={"hour": 3, "minute": 0},
        job_payload={"shop_id": shop.id},
    )
    db_session.add(job)
    await db_session.commit()
    shop_id, job_id = shop.id, job.id

    r = await client.delete(
        f"/api/v1/etsy/shops/{shop_id}", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert r.status_code in (200, 204)

    # The disconnect API call committed via its own DB session/dependency.
    # This fixture's session already has `shop`/`job` loaded in its identity
    # map (un-expired by the `shop.id`/`job.id` attribute access above), so a
    # fresh select() would return the cached, now-stale in-memory instances
    # rather than reflecting the disconnect's committed changes. Force a
    # reload from the DB before asserting on post-disconnect state.
    db_session.expire_all()

    token_result = await db_session.execute(select(EtsyToken).where(EtsyToken.etsy_shop_id == shop_id))
    assert token_result.scalar_one_or_none() is None

    shop_result = await db_session.execute(select(EtsyShop).where(EtsyShop.id == shop_id))
    assert shop_result.scalar_one().is_connected is False

    job_result = await db_session.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
    assert job_result.scalar_one().status == "paused"
