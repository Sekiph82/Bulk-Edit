from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return {"status": "ok", "service": "bulk-edit-api"}


@router.get("/db")
async def health_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "unreachable",
                "detail": str(exc),
            },
        )


@router.get("/redis")
async def health_redis():
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        return {"status": "ok", "redis": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "redis": "unreachable",
                "detail": str(exc),
            },
        )
