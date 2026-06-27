import asyncio
import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.core.config import settings

_store: dict[str, list[float]] = defaultdict(list)
_lock = asyncio.Lock()


async def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    now = time.time()
    async with _lock:
        _store[key] = [t for t in _store[key] if now - t < window_seconds]
        if len(_store[key]) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(window_seconds)},
            )
        _store[key].append(now)


async def login_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    await check_rate_limit(
        f"login:{ip}",
        limit=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
        window_seconds=60,
    )


async def register_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    await check_rate_limit(
        f"register:{ip}",
        limit=settings.RATE_LIMIT_REGISTER_PER_MINUTE,
        window_seconds=60,
    )
