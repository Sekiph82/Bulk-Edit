"""Tests for DATABASE_URL scheme normalization in Settings.

Managed Postgres providers (Render/Neon/Supabase/Heroku) return
``postgres://`` or ``postgresql://`` URLs, but the async engine needs
``postgresql+asyncpg://``. The validator rewrites the scheme so a raw provider
URL works unchanged while leaving an explicit ``+driver`` alone.
"""
from app.core.config import Settings


def _url(value: str) -> str:
    return Settings(DATABASE_URL=value).DATABASE_URL


def test_bare_postgresql_scheme_gets_asyncpg():
    assert _url("postgresql://u:p@host:5432/db") == "postgresql+asyncpg://u:p@host:5432/db"


def test_heroku_style_postgres_scheme_gets_asyncpg():
    assert _url("postgres://u:p@host:5432/db") == "postgresql+asyncpg://u:p@host:5432/db"


def test_explicit_asyncpg_driver_untouched():
    v = "postgresql+asyncpg://bulkedit:bulkedit_password@localhost:55432/bulkedit"
    assert _url(v) == v


def test_query_params_preserved():
    assert (
        _url("postgresql://u:p@host/db?sslmode=require")
        == "postgresql+asyncpg://u:p@host/db?sslmode=require"
    )
