"""
Shared retry/backoff wrapper for outbound Etsy API calls, plus write pacing.

Etsy's API Terms require respecting documented rate limits and using safe
retries. `etsy_get`/`etsy_patch`/`etsy_put` all wrap a request with
exponential backoff honoring `Retry-After` when Etsy sends one, using the
retry-count setting in app.core.config (ETSY_RETRY_MAX_ATTEMPTS).

Originally only `etsy_get` existed — every Etsy WRITE call (PATCH listing,
PUT inventory) used `httpx` directly with zero retry handling, which is
exactly what let the owner's Bulk Edit apply hit a live, unretried
HTTP 429 ("Exceeded per second rate limit") — 2026-08-28. `etsy_patch`/
`etsy_put` close that gap using the same proven retry core.

`sleep_before_etsy_write()` is a separate concern from per-call retry: it
paces the gap BETWEEN different listings' write attempts in an apply/revert
job, so a fast sequential loop doesn't outrun Etsy's rate limit before any
single call gets a chance to retry. See its docstring for why it's not
built into etsy_get/etsy_patch/etsy_put directly.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Awaitable, Callable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# Status → safe category, shared by every write-error diagnostics builder.
# 429 is the only category this module retries; the rest are terminal.
_NON_RETRYABLE_STATUS_CATEGORY = {
    400: "validation_rejected",
    401: "access_denied",
    403: "access_denied",
    404: "not_found",
}


def classify_etsy_write_status(status_code: int) -> str:
    """Safe category for an Etsy write failure status code. Never inspects
    the response body (which may need sanitizing separately)."""
    if status_code == 429:
        return "rate_limited"
    if status_code in _NON_RETRYABLE_STATUS_CATEGORY:
        return _NON_RETRYABLE_STATUS_CATEGORY[status_code]
    if status_code >= 500:
        return "server_error"
    return "unknown"


def parse_retry_after_seconds(header_value: str | None) -> float | None:
    """
    Parse Etsy's Retry-After header. Only the delay-seconds form (e.g. "3")
    is supported — Etsy has only ever been observed sending that form, not
    an HTTP-date. Returns None for missing/invalid/negative values.
    """
    if not header_value:
        return None
    try:
        seconds = float(header_value)
    except (TypeError, ValueError):
        return None
    return seconds if seconds >= 0 else None


def compute_backoff_delay(
    attempt: int,
    retry_after_seconds: float | None,
    *,
    base_delay: float = 2.0,
    jitter_fn: Callable[[], float] = lambda: random.uniform(0.85, 1.15),
) -> float:
    """
    Delay before retrying after `attempt` (1-indexed) has failed.
    Honors Retry-After when Etsy sends one — Etsy told us exactly how long
    to wait, so no jitter is applied to that value. Otherwise exponential:
    base_delay * 2**(attempt-1), with jitter to avoid a thundering herd if
    multiple write loops back off at the same moment. Pass jitter_fn=lambda: 1.0
    in tests for determinism.
    """
    if retry_after_seconds is not None:
        return max(0.0, retry_after_seconds)
    return base_delay * (2 ** (attempt - 1)) * jitter_fn()


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


async def _request_with_retry(
    make_request: Callable[[], Awaitable[httpx.Response]],
    label: str,
    *,
    sleep_fn: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> httpx.Response:
    """
    Shared retry core for GET/PATCH/PUT: exponential backoff on 429/5xx,
    honoring Retry-After. On final failure (retries exhausted or a non-
    retryable status), returns the response as-is — callers decide whether
    resp.status_code >= 400 is an error. Only network-level TransportErrors
    are raised, and only after every attempt is exhausted.
    sleep_fn is injectable so tests never sleep for real time.
    """
    attempts = max(1, settings.ETSY_RETRY_MAX_ATTEMPTS)
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            resp = await make_request()
        except httpx.TransportError as exc:
            last_exc = exc
        else:
            if resp.status_code not in _RETRYABLE_STATUS:
                return resp
            if attempt == attempts:
                return resp
            retry_after = parse_retry_after_seconds(resp.headers.get("Retry-After"))
            wait = compute_backoff_delay(attempt, retry_after)
            logger.warning(
                "Etsy API %s returned %s (attempt %s/%s) — retrying in %.1fs",
                label, resp.status_code, attempt, attempts, wait,
            )
            await sleep_fn(wait)
            continue
        if attempt == attempts:
            raise last_exc if last_exc is not None else RuntimeError(
                f"_request_with_retry({label}): retry loop exhausted with no captured exception"
            )
        await sleep_fn(compute_backoff_delay(attempt, None))
    raise last_exc if last_exc is not None else RuntimeError(
        f"_request_with_retry({label}): retry loop exited without raising or returning"
    )  # pragma: no cover — unreachable in practice, guards against raising None


async def etsy_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """GET with exponential backoff on 429/5xx. Returns final response even on unresolved failure."""
    return await _request_with_retry(lambda: client.get(url, **kwargs), url)


async def etsy_patch(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """PATCH with exponential backoff on 429/5xx. Returns final response even on unresolved failure."""
    return await _request_with_retry(lambda: client.patch(url, **kwargs), url)


async def etsy_put(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """PUT with exponential backoff on 429/5xx. Returns final response even on unresolved failure."""
    return await _request_with_retry(lambda: client.put(url, **kwargs), url)


# ── Write pacing ────────────────────────────────────────────────────────────
# Separate from the per-call retry above: this enforces a minimum spacing
# BETWEEN different Etsy write attempts across an entire apply/revert job's
# item loop, so a fast sequential loop over many listings doesn't burst past
# Etsy's per-second limit before any single call even gets a chance to retry.
# Deliberately NOT applied inside etsy_get/etsy_patch/etsy_put themselves —
# those are also used for plain listing sync reads, which must stay fast;
# only call sites inside the actual write flow (apply/revert) should pace.
# Per-process, keyed by shop — good enough for this single-worker sprint;
# a multi-worker deployment would need a shared (e.g. Redis) clock instead.

_last_write_at: dict[str, float] = {}
_write_pace_lock = asyncio.Lock()


async def sleep_before_etsy_write(
    shop_key: str,
    *,
    min_interval_seconds: float | None = None,
    sleep_fn: Callable[[float], Awaitable[None]] = asyncio.sleep,
    now_fn: Callable[[], float] = time.monotonic,
) -> float:
    """
    Block until at least min_interval_seconds have passed since the last
    Etsy write for this shop, then record this call as the new last-write
    time. Returns the number of seconds actually slept (0.0 if none needed).
    sleep_fn/now_fn are injectable so tests never sleep for real time.
    """
    interval = (
        min_interval_seconds
        if min_interval_seconds is not None
        else settings.ETSY_BULK_WRITE_DELAY_MS / 1000.0
    )
    async with _write_pace_lock:
        now = now_fn()
        last = _last_write_at.get(shop_key)
        wait = 0.0
        if last is not None:
            elapsed = now - last
            if elapsed < interval:
                wait = interval - elapsed
        if wait > 0:
            await sleep_fn(wait)
            now = now_fn()
        _last_write_at[shop_key] = now
    return wait
