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

async def test_disconnect_shop_404_unknown(client):
    token = await _register_and_login(client)
    import uuid
    r = await client.delete(f"/api/v1/etsy/shops/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
