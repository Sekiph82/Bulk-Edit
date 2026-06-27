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
