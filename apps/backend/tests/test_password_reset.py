"""Tests for forgot-password / reset-password. EMAIL_PROVIDER stays 'disabled'
in tests (default) — no real email is ever sent from this test file.
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
FORGOT_URL = "/api/v1/auth/forgot-password"
RESET_URL = "/api/v1/auth/reset-password"

USER = {
    "email": "reset_user@example.com",
    "password": "OriginalPass123!",
    "full_name": "Reset User",
    "organization_name": "Reset Org",
    "terms_accepted": True,
}


async def _get_reset_token_hash_for_user(db_session, email: str) -> str:
    """Fetch the token_hash row created by a forgot-password request, for
    tests that need to exercise reset-password without knowing the raw
    token (which is only ever sent via email, never returned by the API).
    """
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    user_result = await db_session.execute(select(User).where(User.email == email))
    user = user_result.scalar_one()
    token_result = await db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )
    return token_result.scalars().first()


@pytest.mark.anyio
async def test_forgot_password_existing_user_generic_response(client):
    await client.post(REGISTER_URL, json=USER)
    r = await client.post(FORGOT_URL, json={"email": USER["email"]})
    assert r.status_code == 200
    assert "message" in r.json()


@pytest.mark.anyio
async def test_forgot_password_unknown_user_same_generic_response(client):
    r1 = await client.post(FORGOT_URL, json={"email": "definitely-not-registered@example.com"})
    r2 = await client.post(FORGOT_URL, json={"email": "also-not-registered@example.com"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Identical response shape/content for existing vs unknown — no enumeration signal.
    assert r1.json() == r2.json()


@pytest.mark.anyio
async def test_forgot_password_creates_token_row_for_existing_user(client, db_session):
    email = "reset_row_check@example.com"
    await client.post(REGISTER_URL, json={**USER, "email": email})
    await client.post(FORGOT_URL, json={"email": email})

    row = await _get_reset_token_hash_for_user(db_session, email)
    assert row is not None
    assert row.used_at is None
    # The raw token must never be persisted — only its sha256 hash (64 hex chars).
    assert len(row.token_hash) == 64
    assert all(c in "0123456789abcdef" for c in row.token_hash)


@pytest.mark.anyio
async def test_forgot_password_no_token_row_for_unknown_email(client, db_session):
    from app.models.password_reset_token import PasswordResetToken

    before = await db_session.execute(select(PasswordResetToken))
    before_count = len(before.scalars().all())

    await client.post(FORGOT_URL, json={"email": "no-such-user-ever@example.com"})

    after = await db_session.execute(select(PasswordResetToken))
    after_count = len(after.scalars().all())
    assert after_count == before_count


@pytest.mark.anyio
async def test_reset_password_invalid_token_fails(client):
    r = await client.post(RESET_URL, json={"token": "not-a-real-token", "new_password": "NewPass123!"})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_reset_password_valid_token_works_and_is_single_use(client, db_session):
    from app.core.security import generate_refresh_token, hash_refresh_token
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    email = "reset_flow@example.com"
    await client.post(REGISTER_URL, json={**USER, "email": email})

    user_result = await db_session.execute(select(User).where(User.email == email))
    user = user_result.scalar_one()

    raw_token = generate_refresh_token()
    token_row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(token_row)
    await db_session.commit()

    r = await client.post(RESET_URL, json={"token": raw_token, "new_password": "BrandNewPass123!"})
    assert r.status_code == 200

    # New password works
    login_r = await client.post(LOGIN_URL, json={"email": email, "password": "BrandNewPass123!"})
    assert login_r.status_code == 200

    # Old password no longer works
    old_login_r = await client.post(LOGIN_URL, json={"email": email, "password": USER["password"]})
    assert old_login_r.status_code == 401

    # Token is single-use — reusing it must fail
    reuse_r = await client.post(RESET_URL, json={"token": raw_token, "new_password": "AnotherPass123!"})
    assert reuse_r.status_code == 400


@pytest.mark.anyio
async def test_reset_password_expired_token_fails(client, db_session):
    from app.core.security import generate_refresh_token, hash_refresh_token
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    email = "reset_expired@example.com"
    await client.post(REGISTER_URL, json={**USER, "email": email})

    user_result = await db_session.execute(select(User).where(User.email == email))
    user = user_result.scalar_one()

    raw_token = generate_refresh_token()
    token_row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),  # already expired
    )
    db_session.add(token_row)
    await db_session.commit()

    r = await client.post(RESET_URL, json={"token": raw_token, "new_password": "NewPass123!"})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_reset_password_used_token_fails(client, db_session):
    from app.core.security import generate_refresh_token, hash_refresh_token
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    email = "reset_used@example.com"
    await client.post(REGISTER_URL, json={**USER, "email": email})

    user_result = await db_session.execute(select(User).where(User.email == email))
    user = user_result.scalar_one()

    raw_token = generate_refresh_token()
    token_row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used_at=datetime.now(timezone.utc),  # already used
    )
    db_session.add(token_row)
    await db_session.commit()

    r = await client.post(RESET_URL, json={"token": raw_token, "new_password": "NewPass123!"})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_reset_password_weak_password_rejected(client, db_session):
    from app.core.security import generate_refresh_token, hash_refresh_token
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    email = "reset_weak@example.com"
    await client.post(REGISTER_URL, json={**USER, "email": email})

    user_result = await db_session.execute(select(User).where(User.email == email))
    user = user_result.scalar_one()

    raw_token = generate_refresh_token()
    token_row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(token_row)
    await db_session.commit()

    r = await client.post(RESET_URL, json={"token": raw_token, "new_password": "short"})
    assert r.status_code == 422
