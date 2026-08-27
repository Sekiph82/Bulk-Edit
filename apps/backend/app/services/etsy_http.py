"""
Shared retry/backoff wrapper for outbound Etsy API calls.

Etsy's API Terms require respecting documented rate limits and using safe
retries — prior to this module, every Etsy call in the codebase used
`httpx` directly with no 429/5xx handling at all (raise_for_status only).
This wraps a request with exponential backoff honoring `Retry-After` when
Etsy sends it, using the retry-count/rate settings already defined (but
previously unused) in app.core.config.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class EtsyConfigurationError(Exception):
    """Raised when Etsy API credentials aren't fully configured. Never carries
    the secret value itself -- only a safe, static message."""


def etsy_api_key_header() -> str:
    """
    Build the x-api-key header value required on every Etsy Open API v3
    request: "<keystring>:<shared_secret>" (Etsy's docs, see the comment on
    ETSY_CLIENT_SECRET in app.core.config -- NOT the keystring alone). Raises
    EtsyConfigurationError instead of silently returning a malformed value if
    either half is missing, so a misconfigured deploy fails loudly at the
    call site rather than sending Etsy a header that will always 403.
    """
    keystring = settings.ETSY_CLIENT_ID
    shared_secret = settings.ETSY_CLIENT_SECRET
    if not keystring or "placeholder" in keystring.lower():
        raise EtsyConfigurationError("ETSY_CLIENT_ID is not configured")
    if not shared_secret or "placeholder" in shared_secret.lower():
        raise EtsyConfigurationError("ETSY_CLIENT_SECRET is not configured")
    return f"{keystring}:{shared_secret}"


async def etsy_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """GET with exponential backoff on 429/5xx. Raises on final failure."""
    attempts = max(1, settings.ETSY_RETRY_MAX_ATTEMPTS)
    delay = 1.0
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            resp = await client.get(url, **kwargs)
        except httpx.TransportError as exc:
            last_exc = exc
        else:
            if resp.status_code not in _RETRYABLE_STATUS:
                return resp
            retry_after = resp.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
            if attempt == attempts:
                return resp
            logger.warning(
                "Etsy API %s returned %s (attempt %s/%s) — retrying in %.1fs",
                url, resp.status_code, attempt, attempts, wait,
            )
            await asyncio.sleep(wait)
            delay *= 2
            continue
        if attempt == attempts:
            raise last_exc if last_exc is not None else RuntimeError(
                "etsy_get: retry loop exhausted with no captured exception"
            )
        await asyncio.sleep(delay)
        delay *= 2
    raise last_exc if last_exc is not None else RuntimeError(
        "etsy_get: retry loop exited without raising or returning"
    )  # pragma: no cover — unreachable in practice, guards against raising None
