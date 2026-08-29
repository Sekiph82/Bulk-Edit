import os

# Deterministic, valid, NON-SECRET Fernet key for tests only. Set before app
# config/encryption is imported below. `setdefault` means an explicit env var
# (e.g. CI) still wins, and production never loads conftest, so the real
# ENCRYPTION_KEY requirement is unaffected.
os.environ.setdefault("ENCRYPTION_KEY", "uOv7K6PYL6v4G77O0WqJrA5BrM42x3NCAQZUSO2rTio=")

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"


@pytest.fixture(autouse=True)
def _reset_etsy_write_pacing_state():
    """
    etsy_http.sleep_before_etsy_write() tracks the last write time per shop
    in a module-level dict and enforces settings.ETSY_BULK_WRITE_DELAY_MS
    (1100ms in production) between writes to the same shop — so a fast
    sequential apply/revert loop paces itself against Etsy's rate limit.
    Many tests reuse the same literal shop_etsy_id (e.g. "99999999") across
    dozens of call sites, and some tests write to one listing more than
    once (title PATCH + inventory PUT). Without neutralizing this, those
    would trigger real (non-injected) multi-second asyncio.sleep calls,
    silently slowing and flaking the suite — exactly what the task asked
    tests to never do. Sets the interval to 0 for the whole test process
    (production's real default is untouched — this only patches the
    Settings instance the app already constructed) and clears any state
    between tests for good measure. Runs before every test.
    """
    from app.core.config import settings as _settings
    from app.services import etsy_http

    original_delay_ms = _settings.ETSY_BULK_WRITE_DELAY_MS
    _settings.ETSY_BULK_WRITE_DELAY_MS = 0
    etsy_http._last_write_at.clear()
    yield
    _settings.ETSY_BULK_WRITE_DELAY_MS = original_delay_ms
    etsy_http._last_write_at.clear()


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        # Import models so tables are registered
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
