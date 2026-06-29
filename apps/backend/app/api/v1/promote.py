"""Promote — Pinterest and Instagram OAuth account connection and product sharing."""

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_org_id, require_active_user
from app.core.encryption import encrypt_token
from app.db.session import get_db
from app.models.listing import Listing
from app.models.listing_image import ListingImage
from app.models.social_connection import SocialConnection
from app.models.social_oauth_state import SocialOAuthState

router = APIRouter(prefix="/promote", tags=["promote"])

_OAUTH_STATE_EXPIRY_MINUTES = 10


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PlatformStatus(BaseModel):
    platform: str
    state: str  # "app_not_configured" | "not_connected" | "connected" | "expired"
    connected: bool = False
    connected_at: Optional[str] = None
    expires_at: Optional[str] = None
    account_name: Optional[str] = None
    username: Optional[str] = None
    external_account_id: Optional[str] = None


class ConnectUrlResponse(BaseModel):
    url: str
    platform: str


class ConfigStatus(BaseModel):
    pinterest_configured: bool
    instagram_configured: bool


class PinterestShareRequest(BaseModel):
    listing_id: Optional[str] = None
    image_url: Optional[str] = None
    caption: str
    board_id: Optional[str] = None
    destination_url: Optional[str] = None


class InstagramShareRequest(BaseModel):
    listing_id: Optional[str] = None
    image_url: Optional[str] = None
    caption: str


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _pinterest_missing_vars() -> list[str]:
    missing = []
    if not (settings.PINTEREST_CLIENT_ID and "placeholder" not in settings.PINTEREST_CLIENT_ID):
        missing.append("PINTEREST_CLIENT_ID")
    if not settings.PINTEREST_CLIENT_SECRET:
        missing.append("PINTEREST_CLIENT_SECRET")
    if not settings.PINTEREST_REDIRECT_URI:
        missing.append("PINTEREST_REDIRECT_URI")
    return missing


def _instagram_missing_vars() -> list[str]:
    missing = []
    if not (settings.META_APP_ID and "placeholder" not in settings.META_APP_ID):
        missing.append("META_APP_ID")
    if not settings.META_APP_SECRET:
        missing.append("META_APP_SECRET")
    if not settings.INSTAGRAM_REDIRECT_URI:
        missing.append("INSTAGRAM_REDIRECT_URI")
    return missing


def _is_pinterest_configured() -> bool:
    return len(_pinterest_missing_vars()) == 0


def _is_instagram_configured() -> bool:
    return len(_instagram_missing_vars()) == 0


# ---------------------------------------------------------------------------
# Popup HTML helpers — postMessage never includes tokens
# ---------------------------------------------------------------------------

def _popup_success_html(platform: str, message: str) -> str:
    p = json.dumps(platform)
    m = json.dumps(message)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Connecting…</title></head>
<body>
<script>
(function() {{
  var msg = {{ type: "bulk-edit-social-oauth", platform: {p}, status: "success", message: {m} }};
  if (window.opener && !window.opener.closed) {{
    window.opener.postMessage(msg, window.location.origin);
  }}
  setTimeout(function() {{ window.close(); }}, 200);
}})();
</script>
<p style="font-family:sans-serif;color:#555;text-align:center;margin-top:60px;">
  Connected successfully. This window will close automatically.
</p>
</body>
</html>"""


def _popup_error_html(platform: str, message: str) -> str:
    p = json.dumps(platform)
    m = json.dumps(message)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Connection failed</title></head>
<body>
<script>
(function() {{
  var msg = {{ type: "bulk-edit-social-oauth", platform: {p}, status: "error", message: {m} }};
  if (window.opener && !window.opener.closed) {{
    window.opener.postMessage(msg, window.location.origin);
  }}
  setTimeout(function() {{ window.close(); }}, 800);
}})();
</script>
<p style="font-family:sans-serif;color:#777;text-align:center;margin-top:60px;">
  Connection failed. This window will close automatically.
</p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _platform_status(platform: str, org_id: str, db: AsyncSession) -> PlatformStatus:
    configured = _is_pinterest_configured() if platform == "pinterest" else _is_instagram_configured()
    if not configured:
        return PlatformStatus(platform=platform, state="app_not_configured", connected=False)

    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == platform,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn or conn.status == "revoked":
        return PlatformStatus(platform=platform, state="not_connected", connected=False)

    now = datetime.now(timezone.utc)
    if conn.expires_at and conn.expires_at < now:
        return PlatformStatus(
            platform=platform,
            state="expired",
            connected=False,
            connected_at=conn.created_at.isoformat(),
            expires_at=conn.expires_at.isoformat(),
            account_name=conn.account_name,
            username=conn.username,
            external_account_id=conn.external_account_id,
        )

    return PlatformStatus(
        platform=platform,
        state="connected",
        connected=True,
        connected_at=conn.created_at.isoformat(),
        expires_at=conn.expires_at.isoformat() if conn.expires_at else None,
        account_name=conn.account_name,
        username=conn.username,
        external_account_id=conn.external_account_id,
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
    # SQLite returns naive datetimes; normalise before comparison
    expires_at = record.expires_at
    if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
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
    account_name: Optional[str],
    username: Optional[str],
    external_account_id: Optional[str],
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
        conn.status = "connected"
        conn.account_name = account_name
        conn.username = username
        conn.external_account_id = external_account_id
        conn.disconnected_at = None
    else:
        db.add(SocialConnection(
            organization_id=org_id,
            platform=platform,
            access_token_encrypted=encrypted,
            token_type=token_type,
            scope=scope,
            expires_at=expires_at,
            status="connected",
            account_name=account_name,
            username=username,
            external_account_id=external_account_id,
        ))
    await db.commit()


async def _get_connected_connection(platform: str, org_id: str, db: AsyncSession) -> SocialConnection:
    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == platform,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn or conn.status != "connected":
        raise HTTPException(status_code=403, detail=f"{platform.capitalize()} account not connected.")
    return conn


# ---------------------------------------------------------------------------
# Platform account info helpers — called after token exchange
# ---------------------------------------------------------------------------

async def _fetch_pinterest_account(access_token: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.pinterest.com/v5/user_account",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.is_success:
            data = resp.json()
            uname = data.get("username")
            return {
                "account_name": uname,
                "username": uname,
                "external_account_id": data.get("id"),
            }
    except Exception:
        pass
    return {}


async def _fetch_instagram_account(access_token: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://graph.facebook.com/me",
                params={"fields": "name,id", "access_token": access_token},
            )
        if resp.is_success:
            data = resp.json()
            name = data.get("name")
            fb_id = data.get("id")
            return {
                "account_name": name,
                "username": name,
                "external_account_id": fb_id,
            }
    except Exception:
        pass
    return {}


# ---------------------------------------------------------------------------
# Endpoints — Config
# ---------------------------------------------------------------------------

@router.get("/config-status", response_model=ConfigStatus)
async def config_status():
    """Public endpoint — checks if social platform env vars are configured."""
    return ConfigStatus(
        pinterest_configured=_is_pinterest_configured(),
        instagram_configured=_is_instagram_configured(),
    )


# ---------------------------------------------------------------------------
# Endpoints — Pinterest
# ---------------------------------------------------------------------------

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
    return ConnectUrlResponse(url=url, platform="pinterest")


@router.get("/pinterest/callback")
async def pinterest_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if error or not code or not state:
        return HTMLResponse(content=_popup_error_html(
            "pinterest", "Pinterest connection was cancelled or failed. Please try again."
        ))

    if not _is_pinterest_configured():
        return HTMLResponse(content=_popup_error_html(
            "pinterest", "Pinterest is not configured on this server."
        ))

    try:
        state_record = await _consume_state(state, "pinterest", db)
    except HTTPException as exc:
        return HTMLResponse(content=_popup_error_html("pinterest", exc.detail))

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
            return HTMLResponse(content=_popup_error_html(
                "pinterest", "Token exchange failed. Please try again."
            ))
        data = resp.json()
    except Exception:
        return HTMLResponse(content=_popup_error_html(
            "pinterest", "Token exchange failed. Please try again."
        ))

    access_token = data.get("access_token")
    if not access_token:
        return HTMLResponse(content=_popup_error_html(
            "pinterest", "Pinterest did not return an access token."
        ))

    account_info = await _fetch_pinterest_account(access_token)

    await _upsert_connection(
        org_id=state_record.organization_id,
        platform="pinterest",
        access_token=access_token,
        token_type=data.get("token_type", "Bearer"),
        scope=data.get("scope", ""),
        expires_in=data.get("expires_in"),
        account_name=account_info.get("account_name"),
        username=account_info.get("username"),
        external_account_id=account_info.get("external_account_id"),
        db=db,
    )

    return HTMLResponse(content=_popup_success_html(
        "pinterest", "Pinterest connected successfully."
    ))


@router.delete("/pinterest/disconnect", status_code=204)
async def pinterest_disconnect(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == "pinterest",
        )
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.access_token_encrypted = None
        conn.status = "revoked"
        conn.disconnected_at = datetime.now(timezone.utc)
        await db.commit()


@router.delete("/pinterest/connection", status_code=204)
async def pinterest_connection_delete(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Alias for /pinterest/disconnect."""
    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == "pinterest",
        )
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.access_token_encrypted = None
        conn.status = "revoked"
        conn.disconnected_at = datetime.now(timezone.utc)
        await db.commit()


@router.post("/pinterest/share")
async def pinterest_share(
    req: PinterestShareRequest,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_connected_connection("pinterest", org_id, db)

    if req.listing_id:
        listing_result = await db.execute(
            select(Listing).where(
                Listing.id == req.listing_id,
                Listing.organization_id == org_id,
            )
        )
        if not listing_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Listing not found.")

    return {
        "success": False,
        "message": "Pinterest Pin creation is not fully enabled yet. You can copy the caption or download the image.",
        "deferred": True,
        "caption": req.caption,
    }


# ---------------------------------------------------------------------------
# Endpoints — Instagram
# ---------------------------------------------------------------------------

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
    url = (
        "https://www.facebook.com/dialog/oauth"
        f"?client_id={settings.META_APP_ID}"
        f"&redirect_uri={settings.INSTAGRAM_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=instagram_basic,instagram_content_publish"
        f"&state={state_value}"
    )
    return ConnectUrlResponse(url=url, platform="instagram")


@router.get("/instagram/callback")
async def instagram_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if error or not code or not state:
        return HTMLResponse(content=_popup_error_html(
            "instagram", "Instagram connection was cancelled or failed. Please try again."
        ))

    if not _is_instagram_configured():
        return HTMLResponse(content=_popup_error_html(
            "instagram", "Instagram is not configured on this server."
        ))

    try:
        state_record = await _consume_state(state, "instagram", db)
    except HTTPException as exc:
        return HTMLResponse(content=_popup_error_html("instagram", exc.detail))

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
            return HTMLResponse(content=_popup_error_html(
                "instagram", "Token exchange failed. Please try again."
            ))
        data = resp.json()
    except Exception:
        return HTMLResponse(content=_popup_error_html(
            "instagram", "Token exchange failed. Please try again."
        ))

    access_token = data.get("access_token")
    if not access_token:
        return HTMLResponse(content=_popup_error_html(
            "instagram", "Instagram did not return an access token."
        ))

    account_info = await _fetch_instagram_account(access_token)

    await _upsert_connection(
        org_id=state_record.organization_id,
        platform="instagram",
        access_token=access_token,
        token_type=data.get("token_type", "Bearer"),
        scope=data.get("scope", "instagram_basic,instagram_content_publish"),
        expires_in=data.get("expires_in"),
        account_name=account_info.get("account_name"),
        username=account_info.get("username"),
        external_account_id=account_info.get("external_account_id"),
        db=db,
    )

    return HTMLResponse(content=_popup_success_html(
        "instagram", "Instagram connected successfully."
    ))


@router.delete("/instagram/disconnect", status_code=204)
async def instagram_disconnect(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == "instagram",
        )
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.access_token_encrypted = None
        conn.status = "revoked"
        conn.disconnected_at = datetime.now(timezone.utc)
        await db.commit()


@router.delete("/instagram/connection", status_code=204)
async def instagram_connection_delete(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Alias for /instagram/disconnect."""
    result = await db.execute(
        select(SocialConnection).where(
            SocialConnection.organization_id == org_id,
            SocialConnection.platform == "instagram",
        )
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.access_token_encrypted = None
        conn.status = "revoked"
        conn.disconnected_at = datetime.now(timezone.utc)
        await db.commit()


@router.post("/instagram/share")
async def instagram_share(
    req: InstagramShareRequest,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_connected_connection("instagram", org_id, db)

    if req.listing_id:
        listing_result = await db.execute(
            select(Listing).where(
                Listing.id == req.listing_id,
                Listing.organization_id == org_id,
            )
        )
        if not listing_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Listing not found.")

    return {
        "success": False,
        "message": "Instagram publishing is not fully enabled yet. Instagram publishing requires Meta app review. You can copy the caption or download the image.",
        "deferred": True,
        "caption": req.caption,
    }


# ---------------------------------------------------------------------------
# Endpoints — Listings for Promote page
# ---------------------------------------------------------------------------

@router.get("/listings")
async def promote_listings(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Listing)
        .where(Listing.organization_id == org_id)
        .where(Listing.state == "active")
        .order_by(Listing.updated_at.desc())
        .limit(50)
    )
    listings = result.scalars().all()

    items = []
    for listing in listings:
        img_result = await db.execute(
            select(ListingImage)
            .where(ListingImage.listing_id == listing.id)
            .order_by(ListingImage.rank.asc())
            .limit(1)
        )
        primary_image = img_result.scalar_one_or_none()

        price_str = None
        if listing.price_amount is not None and listing.price_divisor:
            price_str = f"{listing.price_amount / listing.price_divisor:.2f}"

        items.append({
            "listing_id": listing.id,
            "title": listing.title or "",
            "price": price_str,
            "currency_code": listing.currency_code,
            "primary_image_url": primary_image.url_fullxfull if primary_image else None,
            "etsy_listing_url": listing.url,
        })

    return {
        "listings": items,
        "empty": len(items) == 0,
        "message": "Sync your Etsy listings first to promote products." if not items else None,
    }
