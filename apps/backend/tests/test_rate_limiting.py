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
    })
    assert r.status_code != 429


@pytest.mark.anyio
async def test_rate_limit_config_disabled_by_default(client):
    """RATE_LIMIT_ENABLED defaults False — verify no spurious 429s."""
    from app.core.config import settings
    assert settings.RATE_LIMIT_ENABLED is False
