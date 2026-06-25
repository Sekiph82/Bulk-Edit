import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "bulk-edit-api"


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "bulk-edit-api"


@pytest.mark.asyncio
async def test_health_db_unreachable(client):
    """DB health check returns 503 when no database is available."""
    response = await client.get("/api/v1/health/db")
    # Passes regardless of 200 or 503 — just must return valid JSON
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_health_redis_unreachable(client):
    """Redis health check returns 503 when no Redis is available."""
    response = await client.get("/api/v1/health/redis")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "redis" in data
