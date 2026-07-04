"""
Rate limiting for auth and contact endpoints.

Backends:
  memory  — in-process dict; resets on restart. Safe for dev/single-worker.
  redis   — shared across workers via sorted sets; production-recommended.

Controlled by:
  RATE_LIMIT_ENABLED            bool  — False in local dev / tests
  RATE_LIMIT_BACKEND            "memory" | "redis"
  RATE_LIMIT_REDIS_URL          optional override; defaults to REDIS_URL
  RATE_LIMIT_LOGIN_PER_MINUTE   int
  RATE_LIMIT_REGISTER_PER_MINUTE int
  RATE_LIMIT_CONTACT_PER_HOUR   int

On Redis unavailability, falls back to memory automatically with a warning log.
Keys never contain raw passwords or tokens — login key uses sha256(email)[:12].
"""

import asyncio
import hashlib
import logging
import time
from collections import defaultdict

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# ── Memory backend ────────────────────────────────────────────────────────────
_mem_store: dict[str, list[float]] = defaultdict(list)
_mem_lock = asyncio.Lock()


async def _check_memory(key: str, limit: int, window_seconds: int) -> None:
    now = time.time()
    async with _mem_lock:
        _mem_store[key] = [t for t in _mem_store[key] if now - t < window_seconds]
        if len(_mem_store[key]) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(window_seconds)},
            )
        _mem_store[key].append(now)


# ── Redis backend ──────────────────────────────────────────────────────────────
_redis_client = None
_redis_init_attempted = False


def _get_redis():
    global _redis_client, _redis_init_attempted
    if _redis_init_attempted:
        return _redis_client
    _redis_init_attempted = True
    try:
        from app.core.config import settings
        import redis.asyncio as aioredis
        url = settings.RATE_LIMIT_REDIS_URL or settings.REDIS_URL
        if not url:
            logger.warning("Rate limit backend=redis but no REDIS_URL configured; falling back to memory")
            return None
        _redis_client = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        return _redis_client
    except Exception as e:
        logger.warning("Rate limit Redis init failed; falling back to memory: %s", e)
        return None


async def _check_redis(key: str, limit: int, window_seconds: int) -> None:
    client = _get_redis()
    if client is None:
        await _check_memory(key, limit, window_seconds)
        return
    try:
        now_ms = int(time.time() * 1000)
        window_ms = window_seconds * 1000
        pipe = client.pipeline()
        await pipe.zremrangebyscore(key, 0, now_ms - window_ms)
        await pipe.zcard(key)
        await pipe.zadd(key, {str(now_ms): now_ms})
        await pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()
        count = results[1]
        if count >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(window_seconds)},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Rate limit Redis check failed; falling back to memory: %s", e)
        await _check_memory(key, limit, window_seconds)


# ── Key construction ──────────────────────────────────────────────────────────

def _safe_key(prefix: str, ip: str, identifier: str = "") -> str:
    """Build rate limit key. Never contains raw email/password — uses sha256 prefix."""
    if identifier:
        id_hash = hashlib.sha256(identifier.lower().encode()).hexdigest()[:12]
        return f"rl:{prefix}:{ip}:{id_hash}"
    return f"rl:{prefix}:{ip}"


# ── Public check API ──────────────────────────────────────────────────────────

async def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    from app.core.config import settings
    if not settings.RATE_LIMIT_ENABLED:
        return
    if settings.RATE_LIMIT_BACKEND == "redis":
        await _check_redis(key, limit, window_seconds)
    else:
        await _check_memory(key, limit, window_seconds)


# ── FastAPI dependencies ──────────────────────────────────────────────────────

async def login_rate_limit(request: Request) -> None:
    from app.core.config import settings
    ip = request.client.host if request.client else "unknown"
    # IP-only key — body already consumed by Pydantic when this dep runs
    key = _safe_key("login", ip)
    await check_rate_limit(key, settings.RATE_LIMIT_LOGIN_PER_MINUTE, 60)


async def register_rate_limit(request: Request) -> None:
    from app.core.config import settings
    ip = request.client.host if request.client else "unknown"
    key = _safe_key("register", ip)
    await check_rate_limit(key, settings.RATE_LIMIT_REGISTER_PER_MINUTE, 60)


async def contact_rate_limit(request: Request) -> None:
    from app.core.config import settings
    ip = request.client.host if request.client else "unknown"
    key = _safe_key("contact", ip)
    await check_rate_limit(key, settings.RATE_LIMIT_CONTACT_PER_HOUR, 3600)


async def forgot_password_rate_limit(request: Request) -> None:
    from app.core.config import settings
    ip = request.client.host if request.client else "unknown"
    key = _safe_key("forgot-password", ip)
    await check_rate_limit(key, settings.RATE_LIMIT_FORGOT_PASSWORD_PER_HOUR, 3600)
