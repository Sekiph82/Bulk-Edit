import pytest


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"

VALID_USER = {
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "organization_name": "Test Org",
}


async def test_register_success(client):
    r = await client.post(REGISTER_URL, json=VALID_USER)
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client):
    await client.post(REGISTER_URL, json=VALID_USER)
    r = await client.post(REGISTER_URL, json=VALID_USER)
    assert r.status_code == 409


async def test_register_weak_password(client):
    r = await client.post(REGISTER_URL, json={**VALID_USER, "password": "short"})
    assert r.status_code == 422


async def test_register_invalid_email(client):
    r = await client.post(REGISTER_URL, json={**VALID_USER, "email": "not-an-email"})
    assert r.status_code == 422


async def test_login_success(client):
    await client.post(REGISTER_URL, json=VALID_USER)
    r = await client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client):
    await client.post(REGISTER_URL, json=VALID_USER)
    r = await client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": "wrongpassword"})
    assert r.status_code == 401


async def test_login_unknown_email(client):
    r = await client.post(LOGIN_URL, json={"email": "nobody@example.com", "password": "password123"})
    assert r.status_code == 401


async def test_refresh_success(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    refresh_token = reg.json()["refresh_token"]
    r = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token  # rotated


async def test_refresh_token_rotation_invalidates_old(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    old_refresh = reg.json()["refresh_token"]
    await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    r = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert r.status_code == 401


async def test_logout_success(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    refresh_token = reg.json()["refresh_token"]
    r = await client.post(LOGOUT_URL, json={"refresh_token": refresh_token})
    assert r.status_code == 204


async def test_logout_then_refresh_fails(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    refresh_token = reg.json()["refresh_token"]
    await client.post(LOGOUT_URL, json={"refresh_token": refresh_token})
    r = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert r.status_code == 401


async def test_me_success(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    access_token = reg.json()["access_token"]
    r = await client.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["email"] == VALID_USER["email"]
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["role"] == "owner"


async def test_me_no_token(client):
    r = await client.get(ME_URL)
    assert r.status_code == 403


async def test_me_invalid_token(client):
    r = await client.get(ME_URL, headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401
