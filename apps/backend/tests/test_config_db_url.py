"""Tests for DATABASE_URL scheme normalization in Settings.

Managed Postgres providers (Render/Neon/Supabase/Heroku/DigitalOcean) return
``postgres://`` or ``postgresql://`` URLs, but the async engine needs
``postgresql+asyncpg://``. The validator rewrites the scheme so a raw provider
URL works unchanged while leaving an explicit ``+driver`` alone.

Many providers also append a libpq-style ``sslmode`` query param. asyncpg's
``connect()`` has no ``sslmode`` keyword (only ``ssl``, which accepts the same
libpq mode strings), so the validator renames the key rather than passing
``sslmode`` straight through — otherwise the connection raises
``TypeError: unexpected keyword argument 'sslmode'``.
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


def test_local_url_without_sslmode_unchanged_besides_scheme():
    assert _url("postgresql://u:p@localhost:55432/bulkedit") == (
        "postgresql+asyncpg://u:p@localhost:55432/bulkedit"
    )


def test_digitalocean_style_sslmode_require_becomes_ssl():
    assert _url("postgresql://u:p@host:25060/db?sslmode=require") == (
        "postgresql+asyncpg://u:p@host:25060/db?ssl=require"
    )


def test_heroku_style_postgres_scheme_with_sslmode_require():
    assert _url("postgres://u:p@host:5432/db?sslmode=require") == (
        "postgresql+asyncpg://u:p@host:5432/db?ssl=require"
    )


def test_sslmode_verify_full_becomes_ssl_verify_full():
    assert _url("postgresql://u:p@host/db?sslmode=verify-full") == (
        "postgresql+asyncpg://u:p@host/db?ssl=verify-full"
    )


def test_sslmode_verify_ca_becomes_ssl_verify_ca():
    assert _url("postgresql://u:p@host/db?sslmode=verify-ca") == (
        "postgresql+asyncpg://u:p@host/db?ssl=verify-ca"
    )


def test_sslmode_disable_does_not_become_true():
    result = _url("postgresql://u:p@host/db?sslmode=disable")
    assert result == "postgresql+asyncpg://u:p@host/db?ssl=disable"
    assert "true" not in result


def test_explicit_asyncpg_driver_with_sslmode_is_also_translated():
    assert _url("postgresql+asyncpg://u:p@host/db?sslmode=require") == (
        "postgresql+asyncpg://u:p@host/db?ssl=require"
    )


def test_other_query_params_preserved_alongside_sslmode():
    result = _url("postgresql://u:p@host/db?sslmode=require&application_name=api")
    assert result == "postgresql+asyncpg://u:p@host/db?application_name=api&ssl=require"


def test_existing_ssl_param_takes_precedence_over_sslmode():
    result = _url("postgresql://u:p@host/db?ssl=false&sslmode=require")
    assert "sslmode" not in result
    assert "ssl=false" in result


def test_unrecognized_sslmode_value_is_dropped_not_passed_through():
    result = _url("postgresql://u:p@host/db?sslmode=bogus")
    assert "sslmode" not in result
    assert "ssl=" not in result


def test_password_with_special_characters_is_not_corrupted():
    v = "postgresql://u:p%40ss%3Aword@host:5432/db?sslmode=require"
    assert _url(v) == "postgresql+asyncpg://u:p%40ss%3Aword@host:5432/db?ssl=require"
