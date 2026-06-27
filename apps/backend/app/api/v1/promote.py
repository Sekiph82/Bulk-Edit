"""Promote — Pinterest and Instagram OAuth account connection."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_org_id, require_active_user
from app.core.encryption import encrypt_token
from app.db.session import get_db
from app.models.social_connection import SocialConnection
from app.models.social_oauth_state import SocialOAuthState

router = APIRouter(prefix="/promote", tags=["promote"])

_OAUTH_STATE_EXPIRY_MINUTES = 10


# --- Schemas ---

class PlatformStatus(BaseModel):
    platform: str
    # "app_not_configured" | "not_connected" | "connected" | "expired"
    state: str
    connected_at: Optional[str] = None
    expires_at: Optional[str] = None


class ConnectUrlResponse(BaseModel):
    url: str


# --- Helpers ---

def _is_pinterest_configured() -> bool:
    cid = settings.PINTEREST_CLIENT_ID
    return bool(cid and settings.PINTEREST_CLIENT_SECRET and settings.PINTEREST_REDIRECT_URI and "placeholder" not in cid)


def _is_instagram_configured() -> bool:
    app_id = settings.META_APP_ID
    return bool(app_id and settings.META_APP_SECRET and settings.INSTAGRAM_REDIRECT_URI and "placeholder" not in app_id)


async def _platform_status(platform: str, org_id: str, db: AsyncSession) -> PlatformStatus:
    configured = _is_pinterest_configured() if platform == "pinterest" else _is_instagram_configured()
    if not configured:
        return PlatformStatus(platform=platform, state="app_not_configured")

    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == platform,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        return PlatformStatus(platform=platform, state="not_connected")

    now = datetime.now(timezone.utc)
    if conn.expires_at and conn.expires_at < now:
        return PlatformStatus(
            platform=platform,
            state="expired",
            connected_at=conn.created_at.isoformat(),
            expires_at=conn.expires_at.isoformat(),
        )

    return PlatformStatus(
        platform=platform,
        state="connected",
        connected_at=conn.created_at.isoformat(),
        expires_at=conn.expires_at.isoformat() if conn.expires_at else None,
    )


async def _create_state(platform: str, org_id: str, user_id: str, db: AsyncSession) -> str:
    """Returns state_value (sent to OAuth). Stores SHA256(state_value) in DB."""
    state_value = secrets.token_urlsafe(32)
    state_hash = hashlib.sha256(state_value.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_OAUTH_STATE_EXPIRY_MINUTES)
    db.add(SocialOAuthState(
        organization_id=org_id,
        user_id=user_id,
        platform=platform,
        state_hash=state_hash,
        expires_at=expires_at,
    ))
    await db.commit()
    return state_value


async def _consume_state(state_value: str, platform: str, db: AsyncSession) -> SocialOAuthState:
    """Verifies and single-use consumes the state. Raises HTTPException on failure."""
    state_hash = hashlib.sha256(state_value.encode()).hexdigest()
    result = await db.execute(
        select(SocialOAuthState).where(
            SocialOAuthState.state_hash == state_hash,
            SocialOAuthState.platform == platform,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")
    now = datetime.now(timezone.utc)
    if record.consumed_at is not None:
        raise HTTPException(status_code=400, detail="OAuth state already consumed.")
    if record.expires_at < now:
        raise HTTPException(status_code=400, detail="OAuth state expired.")
    record.consumed_at = now
    await db.commit()
    return record


async def _upsert_connection(
    org_id: str,
    platform: str,
    access_token: str,
    token_type: str,
    scope: str,
    expires_in: Optional[int],
    db: AsyncSession,
) -> None:
    encrypted = encrypt_token(access_token)
    expires_at = None
    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == platform,
        )
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.access_token_encrypted = encrypted
        conn.token_type = token_type
        conn.scope = scope
        conn.expires_at = expires_at
    else:
        db.add(SocialConnection(
            organization_id=org_id,
            platform=platform,
            access_token_encrypted=encrypted,
            token_type=token_type,
            scope=scope,
            expires_at=expires_at,
        ))
    await db.commit()


# --- Pinterest ---

@router.get("/pinterest/status", response_model=PlatformStatus)
async def pinterest_status(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await _platform_status("pinterest", org_id, db)


@router.get("/pinterest/connect-url", response_model=ConnectUrlResponse)
async def pinterest_connect_url(
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not _is_pinterest_configured():
        raise HTTPException(status_code=503, detail="Pinterest app credentials are not configured.")
    state_value = await _create_state("pinterest", org_id, str(user.id), db)
    url = (
        "https://www.pinterest.com/oauth/"
        f"?client_id={settings.PINTEREST_CLIENT_ID}"
        f"&redirect_uri={settings.PINTEREST_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=boards:read,pins:write,user_accounts:read"
        f"&state={state_value}"
    )
    return ConnectUrlResponse(url=url)


@router.get("/pinterest/callback")
async def pinterest_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if not _is_pinterest_configured():
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=pinterest_not_configured")

    try:
        state_record = await _consume_state(state, "pinterest", db)
    except HTTPException:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=pinterest_invalid_state")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.pinterest.com/v5/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.PINTEREST_REDIRECT_URI,
                },
                auth=(settings.PINTEREST_CLIENT_ID, settings.PINTEREST_CLIENT_SECRET),
                headers={"Accept": "application/json"},
            )
        if not resp.is_success:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=pinterest_token_exchange_failed")
        data = resp.json()
    except Exception:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=pinterest_token_exchange_failed")

    access_token = data.get("access_token")
    if not access_token:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=pinterest_no_token")

    await _upsert_connection(
        org_id=state_record.organization_id,
        platform="pinterest",
        access_token=access_token,
        token_type=data.get("token_type", "Bearer"),
        scope=data.get("scope", ""),
        expires_in=data.get("expires_in"),
        db=db,
    )
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?connected=pinterest")


@router.delete("/pinterest/disconnect", status_code=204)
async def pinterest_disconnect(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == "pinterest",
        )
    )
    await db.commit()


# --- Instagram (Meta) ---

@router.get("/instagram/status", response_model=PlatformStatus)
async def instagram_status(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await _platform_status("instagram", org_id, db)


@router.get("/instagram/connect-url", response_model=ConnectUrlResponse)
async def instagram_connect_url(
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not _is_instagram_configured():
        raise HTTPException(status_code=503, detail="Instagram app credentials are not configured.")
    state_value = await _create_state("instagram", org_id, str(user.id), db)
    # Note: Instagram publishing requires a Business or Creator account
    url = (
        "https://www.facebook.com/dialog/oauth"
        f"?client_id={settings.META_APP_ID}"
        f"&redirect_uri={settings.INSTAGRAM_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=instagram_basic,instagram_content_publish"
        f"&state={state_value}"
    )
    return ConnectUrlResponse(url=url)


@router.get("/instagram/callback")
async def instagram_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if not _is_instagram_configured():
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=instagram_not_configured")

    try:
        state_record = await _consume_state(state, "instagram", db)
    except HTTPException:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=instagram_invalid_state")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://graph.facebook.com/oauth/access_token",
                data={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
        if not resp.is_success:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=instagram_token_exchange_failed")
        data = resp.json()
    except Exception:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=instagram_token_exchange_failed")

    access_token = data.get("access_token")
    if not access_token:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?error=instagram_no_token")

    await _upsert_connection(
        org_id=state_record.organization_id,
        platform="instagram",
        access_token=access_token,
        token_type=data.get("token_type", "Bearer"),
        scope=data.get("scope", "instagram_basic,instagram_content_publish"),
        expires_in=data.get("expires_in"),
        db=db,
    )
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/promote?connected=instagram")


@router.delete("/instagram/disconnect", status_code=204)
async def instagram_disconnect(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == "instagram",
        )
    )
    await db.commit()
