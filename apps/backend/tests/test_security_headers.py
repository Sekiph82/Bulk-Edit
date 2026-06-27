import pytest


@pytest.mark.anyio
async def test_health_has_security_headers(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "permissions-policy" in r.headers


@pytest.mark.anyio
async def test_api_response_has_security_headers(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"


@pytest.mark.anyio
async def test_cors_still_works(client):
    r = await client.get("/api/v1/health", headers={"Origin": "http://localhost:3100"})
    assert r.status_code == 200
    assert "x-content-type-options" in r.headers
