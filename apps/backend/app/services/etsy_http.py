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
            raise last_exc
        await asyncio.sleep(delay)
        delay *= 2
    raise last_exc  # pragma: no cover — unreachable, satisfies type checkers
