import hashlib
import secrets
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, cast, String

from app.core.config import settings
from app.core.encryption import encrypt_token, decrypt_token
from app.models.etsy_shop import EtsyShop
from app.models.etsy_token import EtsyToken
from app.models.etsy_oauth_state import EtsyOAuthState
from app.models.scheduled_job import ScheduledJob
from app.services.etsy_http import EtsyConfigurationError, etsy_api_key_header

logger = logging.getLogger(__name__)


class EtsyOAuthError(Exception):
    """
    Raised for a categorized OAuth callback failure. Carries only a safe
    category/stage/status_code for logging — never the request/response data
    (code, state, tokens, secrets) that caused it.
    """

    def __init__(self, category: str, stage: str, status_code: int | None = None):
        self.category = category
        self.stage = stage
        self.status_code = status_code
        super().__init__(category)


ETSY_AUTH_URL = "https://www.etsy.com/oauth/connect"
ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
ETSY_API_BASE = "https://openapi.etsy.com/v3"


def generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


async def create_authorization_session(org_id: str, user_id: str, db: AsyncSession) -> str:
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    oauth_state = EtsyOAuthState(
        state=state,
        code_verifier=verifier,
        organization_id=org_id,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(oauth_state)
    await db.commit()

    params = {
        "response_type": "code",
        "client_id": settings.ETSY_CLIENT_ID,
        "redirect_uri": settings.ETSY_REDIRECT_URI,
        "scope": settings.ETSY_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    from urllib.parse import urlencode
    return f"{ETSY_AUTH_URL}?{urlencode(params)}"


def _derive_etsy_user_id(token_data: dict[str, Any]) -> str:
    """
    Etsy's token response never includes a `user_id` field (confirmed against
    Etsy's own docs) -- the numeric user id is embedded as the access token's
    `{user_id}.{opaque_token}` prefix. Validate it's actually present and
    numeric before it's ever used in a request URL, instead of trusting it
    blind.
    """
    raw_user_id = token_data.get("user_id")
    if raw_user_id is None:
        access_token = token_data.get("access_token") or ""
        raw_user_id = access_token.split(".", 1)[0] if "." in access_token else None

    etsy_user_id = str(raw_user_id or "").strip()

    if not etsy_user_id.isdigit():
        raise EtsyOAuthError("etsy_oauth_user_id_missing_or_invalid", stage="user_id_derivation")

    return etsy_user_id


async def handle_oauth_callback(code: str, state: str, db: AsyncSession) -> None:
    result = await db.execute(select(EtsyOAuthState).where(EtsyOAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if not oauth_state:
        raise EtsyOAuthError("etsy_oauth_state_not_found", stage="state_lookup")
    if oauth_state.consumed_at is not None:
        raise EtsyOAuthError("etsy_oauth_state_consumed", stage="state_lookup")
    if datetime.now(timezone.utc) > oauth_state.expires_at.replace(tzinfo=timezone.utc):
        raise EtsyOAuthError("etsy_oauth_state_expired", stage="state_lookup")

    oauth_state.consumed_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        token_data = await exchange_code_for_token(code, oauth_state.code_verifier)
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        status_code = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else None
        raise EtsyOAuthError("etsy_oauth_token_exchange_failed", stage="token_exchange", status_code=status_code) from e

    if not isinstance(token_data, dict) or not token_data.get("access_token") or not token_data.get("refresh_token"):
        raise EtsyOAuthError("etsy_oauth_token_response_invalid", stage="token_exchange")

    etsy_user_id = _derive_etsy_user_id(token_data)
    try:
        shop_info = await fetch_etsy_shop(etsy_user_id, token_data["access_token"])
    except EtsyConfigurationError as e:
        raise EtsyOAuthError("etsy_oauth_configuration_error", stage="shop_lookup") from e
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        status_code = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else None
        raise EtsyOAuthError("etsy_oauth_shop_lookup_failed", stage="shop_lookup", status_code=status_code) from e
    except ValueError as e:
        raise EtsyOAuthError("etsy_oauth_shop_not_found", stage="shop_lookup") from e

    etsy_shop_id = str(shop_info["shop_id"])
    shop_name = shop_info.get("shop_name")

    result = await db.execute(select(EtsyShop).where(EtsyShop.etsy_shop_id == etsy_shop_id))
    shop = result.scalar_one_or_none()

    if shop is None:
        shop = EtsyShop(
            organization_id=oauth_state.organization_id,
            etsy_shop_id=etsy_shop_id,
            shop_name=shop_name,
            is_connected=True,
        )
        db.add(shop)
        await db.flush()
    else:
        shop.shop_name = shop_name
        shop.is_connected = True
        shop.organization_id = oauth_state.organization_id

    access_enc = encrypt_token(token_data["access_token"])
    refresh_enc = encrypt_token(token_data["refresh_token"])
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))

    result = await db.execute(select(EtsyToken).where(EtsyToken.etsy_shop_id == shop.id))
    token_row = result.scalar_one_or_none()

    granted_scopes = token_data.get("scope") or settings.ETSY_SCOPES

    if token_row is None:
        token_row = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=access_enc,
            refresh_token_enc=refresh_enc,
            expires_at=expires_at,
            scopes=granted_scopes,
        )
        db.add(token_row)
    else:
        token_row.access_token_enc = access_enc
        token_row.refresh_token_enc = refresh_enc
        token_row.expires_at = expires_at
        token_row.scopes = granted_scopes

    try:
        await db.commit()
    except Exception as e:
        raise EtsyOAuthError("etsy_oauth_token_storage_failed", stage="token_storage") from e


async def exchange_code_for_token(code: str, code_verifier: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            ETSY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.ETSY_CLIENT_ID,
                "redirect_uri": settings.ETSY_REDIRECT_URI,
                "code": code,
                "code_verifier": code_verifier,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_etsy_shop(user_id: str, access_token: str) -> dict[str, Any]:
    """
    GET /v3/application/users/{user_id}/shops (getShopByOwnerUserId) returns a
    single Shop object directly -- not a {count, results: [...]} page, unlike
    list endpoints such as findShops (confirmed against Etsy's own OpenAPI
    spec, see issue #80).
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ETSY_API_BASE}/application/users/{user_id}/shops",
            headers={"Authorization": f"Bearer {access_token}", "x-api-key": etsy_api_key_header()},
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or not data.get("shop_id"):
            raise ValueError("No Etsy shop found for user")
        return data


async def list_connected_shops(org_id: str, db: AsyncSession) -> list[EtsyShop]:
    result = await db.execute(
        select(EtsyShop).where(EtsyShop.organization_id == org_id, EtsyShop.is_connected == True)
    )
    return list(result.scalars().all())


async def disconnect_shop(shop_id: str, org_id: str, db: AsyncSession) -> None:
    """
    Disconnects an Etsy shop: deletes the stored access/refresh token immediately
    (matches the Privacy Policy's "disconnecting revokes our stored tokens
    immediately" claim — this must stay true of the implementation, not just
    the marketing copy) and pauses any scheduled jobs referencing this shop so
    a disconnected shop's sync/draft jobs don't keep firing against a shop we
    no longer have a valid token for.
    """
    result = await db.execute(
        select(EtsyShop).where(EtsyShop.id == shop_id, EtsyShop.organization_id == org_id)
    )
    shop = result.scalar_one_or_none()
    if not shop:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Shop not found")

    shop.is_connected = False
    await db.execute(delete(EtsyToken).where(EtsyToken.etsy_shop_id == shop.id))

    payload_text = cast(ScheduledJob.job_payload, String)
    await db.execute(
        ScheduledJob.__table__.update()
        .where(
            ScheduledJob.organization_id == org_id,
            ScheduledJob.status == "active",
            payload_text.ilike('%"shop_id"%'),
            payload_text.ilike(f'%{shop.id}%'),
        )
        .values(status="paused")
    )

    await db.commit()


async def refresh_etsy_token(shop_id: str, db: AsyncSession) -> str:
    """Refresh Etsy access token using stored refresh token. Returns new access token."""
    result = await db.execute(select(EtsyToken).where(EtsyToken.etsy_shop_id == shop_id))
    token_row = result.scalar_one_or_none()
    if not token_row:
        raise ValueError("No token found for shop")

    refresh_token = decrypt_token(token_row.refresh_token_enc)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            ETSY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": settings.ETSY_CLIENT_ID,
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    token_row.access_token_enc = encrypt_token(data["access_token"])
    token_row.refresh_token_enc = encrypt_token(data["refresh_token"])
    token_row.expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
    await db.commit()

    return data["access_token"]
