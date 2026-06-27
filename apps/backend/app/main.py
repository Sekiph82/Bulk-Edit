import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security_headers import SecurityHeadersMiddleware
from app.api.v1.router import api_router
from app.db.session import AsyncSessionLocal
from app.services.local_seed import seed_on_startup

setup_logging()
_logger = logging.getLogger(__name__)


def _scrub_sentry_event(event: dict, hint: dict) -> dict:
    """Remove sensitive fields before sending to Sentry."""
    _SENSITIVE = {
        "password", "password_hash", "access_token", "refresh_token",
        "etsy_access_token", "etsy_refresh_token", "stripe_secret_key",
        "openai_api_key", "anthropic_api_key", "secret_key",
        "authorization", "cookie",
    }

    def _scrub(obj):
        if isinstance(obj, dict):
            return {
                k: "[REDACTED]" if k.lower() in _SENSITIVE else _scrub(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(i) for i in obj]
        return obj

    return _scrub(event)


def _init_sentry() -> None:
    """Initialize Sentry if DSN is configured. Safe no-op when missing."""
    dsn = settings.SENTRY_DSN
    if not dsn or "placeholder" in dsn.lower() or dsn.startswith("YOUR_"):
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            before_send=_scrub_sentry_event,
        )
        _logger.info("Sentry initialized (environment=%s)", settings.SENTRY_ENVIRONMENT)
    except Exception as e:
        _logger.warning("Sentry init failed (backend continues normally): %s", e)


_init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with AsyncSessionLocal() as db:
            await seed_on_startup(db)
    except Exception as exc:
        _logger.warning("Startup seed hook failed (backend continues normally): %s", exc)
    yield


app = FastAPI(
    title="Bulk Edit API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "bulk-edit-api",
        "version": "0.1.0",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }
