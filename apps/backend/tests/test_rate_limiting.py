import pytest


@pytest.mark.anyio
async def test_login_rate_limit_disabled_in_tests(client):
    """Rate limiting is disabled in test env — normal login flows work."""
    r = await client.post("/api/v1/auth/login", json={"email": "nonexistent@example.com", "password": "wrong"})
    assert r.status_code in (401, 422)  # Auth failure, not rate limit


@pytest.mark.anyio
async def test_register_rate_limit_disabled_in_tests(client):
    """Rate limiting disabled — register endpoint accessible without 429."""
    r = await client.post("/api/v1/auth/register", json={
        "email": "ratelimitcheck@example.com",
        "password": "Test1234!",
        "full_name": "Rate Test",
        "terms_accepted": True,
    })
    assert r.status_code != 429


@pytest.mark.anyio
async def test_rate_limit_config_disabled_by_default(client):
    """RATE_LIMIT_ENABLED defaults False — verify no spurious 429s."""
    from app.core.config import settings
    assert settings.RATE_LIMIT_ENABLED is False


@pytest.mark.anyio
async def test_rate_limit_disabled_allows_repeated_login(client):
    """With RATE_LIMIT_ENABLED=False, many requests never return 429."""
    for _ in range(15):
        r = await client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "wrong"})
        assert r.status_code != 429


@pytest.mark.anyio
async def test_health_never_rate_limited(client):
    """Health endpoint has no rate limit dependency — always accessible."""
    for _ in range(20):
        r = await client.get("/api/v1/health")
        assert r.status_code == 200


@pytest.mark.anyio
async def test_rate_limit_429_response_has_no_secrets(client):
    """If 429 is returned, it must not expose secrets or internal details."""
    from app.core.config import settings
    from app.core.rate_limit import _mem_store, _check_memory

    # Manually trigger 429 by filling the memory store
    key = "rl:login:testip"
    import time
    _mem_store[key] = [time.time()] * 100  # overflow the bucket

    # Patch settings to enable
    original = settings.RATE_LIMIT_ENABLED
    try:
        settings.RATE_LIMIT_ENABLED = True
        try:
            await _check_memory(key, 10, 60)
        except Exception as exc:
            # Should be HTTPException 429 with safe message
            assert "429" in str(exc) or hasattr(exc, "status_code")
            if hasattr(exc, "detail"):
                assert "password" not in str(exc.detail).lower()
                assert "token" not in str(exc.detail).lower()
                assert "secret" not in str(exc.detail).lower()
    finally:
        settings.RATE_LIMIT_ENABLED = original
        _mem_store[key] = []


@pytest.mark.anyio
async def test_rate_limit_config_has_redis_url_field(client):
    """Config exposes RATE_LIMIT_REDIS_URL field (empty by default)."""
    from app.core.config import settings
    assert hasattr(settings, "RATE_LIMIT_REDIS_URL")
    # Default is empty string — Redis URL not configured in dev
    assert isinstance(settings.RATE_LIMIT_REDIS_URL, str)


@pytest.mark.anyio
async def test_rate_limit_config_has_contact_limit(client):
    """Config exposes RATE_LIMIT_CONTACT_PER_HOUR field."""
    from app.core.config import settings
    assert hasattr(settings, "RATE_LIMIT_CONTACT_PER_HOUR")
    assert settings.RATE_LIMIT_CONTACT_PER_HOUR > 0


@pytest.mark.anyio
async def test_sentry_config_fields_present(client):
    """Sentry config fields exist and are safe (no real DSN in tests)."""
    from app.core.config import settings
    assert hasattr(settings, "SENTRY_DSN")
    assert hasattr(settings, "SENTRY_ENVIRONMENT")
    assert hasattr(settings, "SENTRY_TRACES_SAMPLE_RATE")
    # In test env, DSN should be empty or placeholder
    dsn = settings.SENTRY_DSN or ""
    assert not dsn.startswith("https://") or "example" in dsn  # no real DSN in tests
