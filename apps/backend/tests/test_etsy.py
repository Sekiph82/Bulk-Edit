import logging
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
# x-api-key header (issue #80 follow-up: Etsy Open API v3 requires
# "<keystring>:<shared_secret>", not the keystring alone)
# ---------------------------------------------------------------------------

def test_etsy_api_key_header_is_keystring_colon_secret():
    from app.services.etsy_http import etsy_api_key_header

    mock_settings = MagicMock()
    mock_settings.ETSY_CLIENT_ID = "test_keystring_123"
    mock_settings.ETSY_CLIENT_SECRET = "test_shared_secret_456"
    with patch("app.services.etsy_http.settings", mock_settings):
        header = etsy_api_key_header()
    assert header == "test_keystring_123:test_shared_secret_456"


def test_etsy_api_key_header_raises_when_secret_missing():
    from app.services.etsy_http import etsy_api_key_header, EtsyConfigurationError

    mock_settings = MagicMock()
    mock_settings.ETSY_CLIENT_ID = "test_keystring_123"
    mock_settings.ETSY_CLIENT_SECRET = ""
    with patch("app.services.etsy_http.settings", mock_settings):
        with pytest.raises(EtsyConfigurationError):
            etsy_api_key_header()


def test_etsy_api_key_header_raises_when_secret_is_placeholder():
    from app.services.etsy_http import etsy_api_key_header, EtsyConfigurationError

    mock_settings = MagicMock()
    mock_settings.ETSY_CLIENT_ID = "test_keystring_123"
    mock_settings.ETSY_CLIENT_SECRET = "etsy_client_secret_placeholder"
    with patch("app.services.etsy_http.settings", mock_settings):
        with pytest.raises(EtsyConfigurationError):
            etsy_api_key_header()


def test_etsy_api_key_header_raises_when_client_id_missing():
    from app.services.etsy_http import etsy_api_key_header, EtsyConfigurationError

    mock_settings = MagicMock()
    mock_settings.ETSY_CLIENT_ID = ""
    mock_settings.ETSY_CLIENT_SECRET = "test_shared_secret_456"
    with patch("app.services.etsy_http.settings", mock_settings):
        with pytest.raises(EtsyConfigurationError):
            etsy_api_key_header()


async def test_callback_configuration_error_logs_category_and_no_secret(client, db_session, caplog):
    """Shop lookup with a missing shared secret -> safe categorized failure, no header/secret value logged."""
    state_val = await _seed_valid_state(db_session)

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {
        "access_token": "99999.opaque_part_never_logged",
        "refresh_token": "etsy_refresh_token_value",
        "expires_in": 3600,
    }
    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(side_effect=AssertionError("shop lookup must not be called without a configured x-api-key"))

    mock_settings = MagicMock()
    mock_settings.ETSY_CLIENT_ID = "test_keystring_123"
    mock_settings.ETSY_CLIENT_SECRET = ""  # simulates the missing-in-this-env case

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        patch("app.services.etsy_http.settings", mock_settings),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_configuration_error" in caplog.text
    mock_http.get.assert_not_called()
    assert "test_keystring_123" not in caplog.text
    assert "opaque_part_never_logged" not in caplog.text


async def test_token_exchange_does_not_send_x_api_key_and_uses_client_id_unchanged():
    """Regression: the OAuth token exchange (PKCE, no shared secret needed) must be untouched by this fix."""
    from app.services.etsy import exchange_code_for_token

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"access_token": "1.tok", "refresh_token": "r", "expires_in": 3600}

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http):
        await exchange_code_for_token("some_code", "some_verifier")

    mock_http.post.assert_called_once()
    _, kwargs = mock_http.post.call_args
    assert "headers" not in kwargs or "x-api-key" not in (kwargs.get("headers") or {})
    assert "client_id" in kwargs["data"]


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

async def test_callback_redirects_on_error_param(client, caplog):
    with caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"):
        r = await client.get(f"{CALLBACK_URL}?error=access_denied", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_provider_error_param" in caplog.text
    assert "access_denied" not in caplog.text


async def test_callback_redirects_on_missing_code(client, caplog):
    with caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"):
        r = await client.get(f"{CALLBACK_URL}?state=somestate_never_logged", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_missing_params" in caplog.text
    assert "somestate_never_logged" not in caplog.text


async def test_callback_redirects_on_invalid_state(client, caplog):
    with caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"):
        r = await client.get(f"{CALLBACK_URL}?code=abc_code_never_logged&state=nonexistent_state", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_state_not_found" in caplog.text
    assert "abc_code_never_logged" not in caplog.text
    assert "nonexistent_state" not in caplog.text


async def test_callback_state_consumed_logs_category(client, db_session, caplog):
    from app.models.etsy_oauth_state import EtsyOAuthState
    from app.services.etsy import generate_code_verifier
    import uuid

    state_val = "already_consumed_state"
    record = EtsyOAuthState(
        state=state_val,
        code_verifier=generate_code_verifier(),
        organization_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        consumed_at=datetime.now(timezone.utc),
    )
    db_session.add(record)
    await db_session.commit()

    with caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"):
        r = await client.get(f"{CALLBACK_URL}?code=somecode&state={state_val}", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_state_consumed" in caplog.text


async def test_callback_state_expired_logs_category(client, db_session, caplog):
    from app.models.etsy_oauth_state import EtsyOAuthState
    from app.services.etsy import generate_code_verifier
    import uuid

    state_val = "expired_state"
    record = EtsyOAuthState(
        state=state_val,
        code_verifier=generate_code_verifier(),
        organization_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db_session.add(record)
    await db_session.commit()

    with caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"):
        r = await client.get(f"{CALLBACK_URL}?code=somecode&state={state_val}", follow_redirects=False)
    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_state_expired" in caplog.text


async def _seed_valid_state(db_session) -> str:
    from app.models.etsy_oauth_state import EtsyOAuthState
    from app.services.etsy import generate_code_verifier
    import uuid

    state_val = f"valid_state_{uuid.uuid4().hex[:8]}"
    db_session.add(EtsyOAuthState(
        state=state_val,
        code_verifier=generate_code_verifier(),
        organization_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    ))
    await db_session.commit()
    return state_val


async def test_callback_token_exchange_http_error_logs_category(client, db_session, caplog):
    import httpx as httpx_module

    state_val = await _seed_valid_state(db_session)

    error_resp = MagicMock()
    error_resp.status_code = 400
    error_resp.raise_for_status = MagicMock(
        side_effect=httpx_module.HTTPStatusError("bad request", request=MagicMock(), response=error_resp)
    )
    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=error_resp)

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=secret_auth_code&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_token_exchange_failed" in caplog.text
    assert "status_code=400" in caplog.text
    assert "secret_auth_code" not in caplog.text


async def test_callback_token_response_invalid_logs_category(client, db_session, caplog):
    state_val = await _seed_valid_state(db_session)

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {"expires_in": 3600}  # missing access_token/refresh_token

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_token_response_invalid" in caplog.text


async def test_callback_user_id_missing_logs_category_and_skips_shop_lookup(client, db_session, caplog):
    """access_token has no dot and token_data has no explicit user_id -> invalid, shop lookup never called."""
    state_val = await _seed_valid_state(db_session)

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {
        "access_token": "malformed_token_no_dot_never_logged",
        "refresh_token": "etsy_refresh_token_value",
        "expires_in": 3600,
    }

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(side_effect=AssertionError("shop lookup must not be called for an invalid user_id"))

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_user_id_missing_or_invalid" in caplog.text
    assert "user_id_derivation" in caplog.text
    mock_http.get.assert_not_called()
    assert "malformed_token_no_dot_never_logged" not in caplog.text


async def test_callback_user_id_non_numeric_logs_category_and_skips_shop_lookup(client, db_session, caplog):
    """access_token prefix before the dot is not all-digits -> invalid, shop lookup never called."""
    state_val = await _seed_valid_state(db_session)

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {
        "access_token": "abc123not_numeric.opaque_part_never_logged",
        "refresh_token": "etsy_refresh_token_value",
        "expires_in": 3600,
    }

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(side_effect=AssertionError("shop lookup must not be called for a non-numeric user_id"))

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_user_id_missing_or_invalid" in caplog.text
    mock_http.get.assert_not_called()
    assert "abc123not_numeric" not in caplog.text
    assert "opaque_part_never_logged" not in caplog.text


async def test_callback_user_id_from_numeric_access_token_prefix_proceeds_to_shop_lookup(client, db_session):
    """access_token = '{numeric_user_id}.{opaque}' (Etsy's real format, no explicit user_id key) -> shop lookup is called and succeeds."""
    state_val = await _seed_valid_state(db_session)

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {
        "access_token": "55512345.opaque_token_part_never_logged",
        "refresh_token": "etsy_refresh_token_value",
        "expires_in": 3600,
    }
    mock_shop_resp = MagicMock()
    mock_shop_resp.raise_for_status = MagicMock()
    mock_shop_resp.json.return_value = {
        "count": 1,
        "results": [{"shop_id": 55512345, "shop_name": "Numeric Prefix Shop"}],
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
    mock_http.get.assert_called_once()
    called_url = mock_http.get.call_args.args[0]
    assert "/users/55512345/shops" in called_url


async def test_callback_shop_lookup_http_error_logs_category(client, db_session, caplog):
    import httpx as httpx_module

    state_val = await _seed_valid_state(db_session)

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {
        "access_token": "etsy_access_token_value",
        "refresh_token": "etsy_refresh_token_value",
        "expires_in": 3600,
        "user_id": "12345",
    }
    shop_error_resp = MagicMock()
    shop_error_resp.status_code = 500
    shop_error_resp.raise_for_status = MagicMock(
        side_effect=httpx_module.HTTPStatusError("server error", request=MagicMock(), response=shop_error_resp)
    )

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(return_value=shop_error_resp)

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_shop_lookup_failed" in caplog.text
    assert "status_code=500" in caplog.text
    assert "etsy_access_token_value" not in caplog.text


async def test_callback_shop_not_found_logs_category(client, db_session, caplog):
    state_val = await _seed_valid_state(db_session)

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
    mock_shop_resp.json.return_value = {"count": 0, "results": []}

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(return_value=mock_shop_resp)

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_shop_not_found" in caplog.text
    assert "etsy_access_token_value" not in caplog.text


async def test_callback_unknown_exception_logs_category(client, db_session, caplog):
    state_val = await _seed_valid_state(db_session)

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
        "results": [{"shop_id": 77777, "shop_name": "Unknown Failure Shop"}],
    }
    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_token_resp)
    mock_http.get = AsyncMock(return_value=mock_shop_resp)

    with (
        patch("app.services.etsy.httpx.AsyncClient", return_value=mock_http),
        patch("app.services.etsy.encrypt_token", side_effect=RuntimeError("unexpected encryption failure")),
        caplog.at_level(logging.WARNING, logger="app.api.v1.etsy"),
    ):
        r = await client.get(f"{CALLBACK_URL}?code=authcode&state={state_val}", follow_redirects=False)

    assert r.status_code == 302
    assert "error=etsy_connect_failed" in r.headers["location"]
    assert "etsy_oauth_unknown" in caplog.text
    assert "RuntimeError" in caplog.text


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
        "access_token": "88888.etsy_access_token_value",
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
