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
