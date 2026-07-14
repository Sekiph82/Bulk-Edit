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
from app.models.terms_acceptance import TermsAcceptance
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.email import send_password_reset_email

logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str | None = None):
        self.message = message
        self.status_code = status_code
        self.code = code  # stable machine-readable error code; None for endpoints that don't need one
        super().__init__(message)


async def register_user(data: RegisterRequest, db: AsyncSession) -> tuple[User, str, str]:
    if not data.terms_accepted:
        # Defense in depth: the Pydantic validator on RegisterRequest already
        # rejects this with a 422, but the service layer must not depend
        # solely on schema validation for a compliance-relevant guarantee.
        raise AuthError("You must agree to the Terms of Service and Privacy Policy", 422)

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

    db.add(TermsAcceptance(
        user_id=user.id,
        terms_version=settings.TERMS_VERSION,
        privacy_version=settings.PRIVACY_VERSION,
        acceptance_source="web_registration",
    ))
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

    # SQLite (used in tests) returns DateTime(timezone=True) columns as
    # naive datetimes — normalize before comparing, same fix already used
    # in app/api/v1/promote.py for the same class of bug.
    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
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


async def delete_account(user_id: str, password: str, db: AsyncSession) -> None:
    """
    Self-service account deletion. Requires password re-confirmation.

    Billing safety gate (owner decision, 2026-07-13 third session): Stripe
    subscriptions are never auto-canceled here. Every organization this user
    owns is checked via assert_account_deletion_billing_safe() BEFORE any
    row is touched — if any owned organization has an active or billable
    subscription, the whole request is rejected (AuthError, 409,
    code=ACTIVE_SUBSCRIPTION_MUST_BE_CANCELED or BILLING_PORTAL_UNAVAILABLE)
    and nothing is deleted. This keeps the operation trivially transactional:
    no partial deletion is possible because no delete is issued until every
    check has already passed.

    Once past the gate: deletes every Organization this user owns — since
    this app has no team/invite feature (one owner per organization,
    confirmed by grep — no invite endpoint exists), this is always safe: no
    other user's data is affected. Deleting the Organization cascades via
    DB-level ON DELETE CASCADE to every org-scoped table (EtsyShop,
    EtsyToken, Listing, bulk-edit/media/variation sessions and snapshots,
    SocialConnection, AISession/AISuggestion/AIUsageLog, Subscription, etc.)
    — this is the same FK convention used throughout the schema (see
    DECISIONS.md: "All foreign keys must have ON DELETE behavior defined").
    Stripe's own customer/subscription record in Stripe itself is NOT
    deleted here — it remains in Stripe per Stripe's own retention/
    compliance behavior; only the local `Subscription` row is removed by
    the cascade. Verified end-to-end against real PostgreSQL, not just
    SQLite — see ETSY_DATA_RETENTION.md §4a.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("Incorrect password", 401)

    from app.services.billing import assert_account_deletion_billing_safe, AccountDeletionBillingStatus

    owned_orgs_result = await db.execute(select(Organization).where(Organization.owner_id == user_id))
    owned_orgs = list(owned_orgs_result.scalars().all())

    for org in owned_orgs:
        check = await assert_account_deletion_billing_safe(org.id, db)
        if not check.safe:
            code = (
                "BILLING_PORTAL_UNAVAILABLE"
                if check.status == AccountDeletionBillingStatus.BLOCKED_NO_PORTAL_ACCESS
                else "ACTIVE_SUBSCRIPTION_MUST_BE_CANCELED"
            )
            raise AuthError(
                "Account deletion is blocked while a paid subscription is active. "
                "Manage or cancel the subscription first; deletion becomes available "
                "after the subscription has ended.",
                409,
                code=code,
            )

    for org in owned_orgs:
        await db.delete(org)
    await db.flush()

    # Memberships in organizations owned by someone else (not applicable
    # today with no invite feature, but handled defensively).
    await db.execute(
        OrganizationMember.__table__.delete().where(OrganizationMember.user_id == user_id)
    )

    await db.delete(user)
    await db.commit()


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
