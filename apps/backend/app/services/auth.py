import logging
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    decode_access_token,
)
from app.core.config import settings
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.email import send_password_reset_email

logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def register_user(data: RegisterRequest, db: AsyncSession) -> tuple[User, str, str]:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise AuthError("Email already registered", 409)

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()

    org_name = data.organization_name or f"{data.full_name or data.email}'s workspace"
    org = Organization(name=org_name, owner_id=user.id)
    db.add(org)
    await db.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
    db.add(member)
    await db.flush()

    access_token, refresh_token = await _issue_tokens(user.id, db)
    await db.commit()
    return user, access_token, refresh_token


async def login_user(data: LoginRequest, db: AsyncSession) -> tuple[User, str, str]:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise AuthError("Invalid email or password", 401)
    if not user.is_active:
        raise AuthError("Account inactive", 403)

    access_token, refresh_token = await _issue_tokens(user.id, db)
    await db.commit()
    return user, access_token, refresh_token


async def refresh_tokens(raw_token: str, db: AsyncSession) -> tuple[str, str]:
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise AuthError("Invalid or expired refresh token", 401)

    stored.revoked = True
    db.add(stored)
    await db.flush()

    access_token, new_refresh = await _issue_tokens(stored.user_id, db)
    await db.commit()
    return access_token, new_refresh


async def logout_user(raw_token: str, db: AsyncSession) -> None:
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked = True
        db.add(stored)
        await db.commit()


async def request_password_reset(email: str, db: AsyncSession) -> None:
    """Always completes successfully regardless of whether the email exists —
    callers must not be able to distinguish the two cases (no user enumeration).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        logger.info("Password reset requested for unknown email (no-op, no enumeration signal)")
        return

    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

    reset_token = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    db.add(reset_token)
    await db.commit()

    reset_url = f"{settings.APP_PUBLIC_URL}/reset-password?token={raw_token}"
    send_password_reset_email(user.email, reset_url)


async def reset_password(token: str, new_password: str, db: AsyncSession) -> None:
    token_hash = hash_refresh_token(token)
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise AuthError("Invalid or expired reset token", 400)
    if reset_token.used_at is not None:
        raise AuthError("Invalid or expired reset token", 400)
    if reset_token.expires_at < datetime.now(timezone.utc):
        raise AuthError("Invalid or expired reset token", 400)

    user_result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise AuthError("Invalid or expired reset token", 400)

    user.password_hash = hash_password(new_password)
    reset_token.used_at = datetime.now(timezone.utc)

    # Revoke all existing sessions — a password reset should invalidate
    # every previously issued refresh token for this user.
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked == False)  # noqa: E712
        .values(revoked=True)
    )

    await db.commit()


async def get_user_by_id(user_id: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_memberships(user_id: str, db: AsyncSession) -> list[OrganizationMember]:
    result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user_id)
    )
    return list(result.scalars().all())


async def _issue_tokens(user_id: str, db: AsyncSession) -> tuple[str, str]:
    access_token = create_access_token(subject=user_id)
    raw_refresh = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rt)
    await db.flush()
    return access_token, raw_refresh
