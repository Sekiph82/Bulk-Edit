#!/usr/bin/env python3
"""
Production environment validation script for Bulk-Edit.

Usage:
    python scripts/validate_env.py [--env development|staging|production]

Checks required environment variables without printing secret values.
Exits non-zero if hard requirements are missing in production mode.
Warnings-only in development/staging mode.
"""
from __future__ import annotations

import argparse
import os
import sys

PASS = "\033[32mPASS\033[0m"
WARN = "\033[33mWARN\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def _mask(val: str) -> str:
    if not val:
        return "(empty)"
    if len(val) <= 8:
        return "***"
    return val[:4] + "***" + val[-2:]


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


results: list[tuple[str, str, str]] = []
errors = 0
warnings = 0


def ok(name: str, msg: str = "") -> None:
    results.append((PASS, name, msg))


def warn(name: str, msg: str) -> None:
    global warnings
    warnings += 1
    results.append((WARN, name, msg))


def fail(name: str, msg: str) -> None:
    global errors
    errors += 1
    results.append((FAIL, name, msg))


def check_required(key: str, env: str, extra_check=None, extra_msg="") -> str:
    val = _get(key)
    if not val:
        if env == "production":
            fail(key, "MISSING - required in production")
        else:
            warn(key, f"Not set - required in production (optional in {env})")
        return ""
    if extra_check and not extra_check(val):
        if env == "production":
            fail(key, extra_msg)
        else:
            warn(key, f"Value looks wrong: {extra_msg}")
        return val
    ok(key, f"Set ({_mask(val)})")
    return val


def check_optional(key: str, msg: str = "") -> str:
    val = _get(key)
    if not val:
        warn(key, f"Not set - {msg}")
        return ""
    ok(key, f"Set ({_mask(val)})")
    return val


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Bulk-Edit environment variables")
    parser.add_argument(
        "--env",
        default=os.environ.get("ENVIRONMENT", "development"),
        choices=["development", "staging", "production"],
        help="Target environment (default: ENVIRONMENT env var or 'development')",
    )
    args = parser.parse_args()
    env = args.env

    print(f"\n{'='*60}")
    print(f"  Bulk-Edit Environment Validation - {env.upper()}")
    print(f"{'='*60}\n")

    # ── Database ──────────────────────────────────────────────────
    print("[ Database ]")
    db_url = check_required(
        "DATABASE_URL",
        env,
        extra_check=lambda v: v.startswith("postgresql"),
        extra_msg="Must start with 'postgresql'",
    )
    if db_url and "password" not in db_url.lower() and env == "production":
        warn("DATABASE_URL", "No password detected in URL - verify credentials are present")

    # ── Redis + Celery ────────────────────────────────────────────
    print("\n[ Redis / Celery ]")
    check_required(
        "REDIS_URL",
        env,
        extra_check=lambda v: v.startswith("redis"),
        extra_msg="Must start with 'redis'",
    )
    check_required("CELERY_BROKER_URL", env)
    check_required("CELERY_RESULT_BACKEND", env)

    # ── Security ──────────────────────────────────────────────────
    print("\n[ Security ]")
    secret_key = check_required("JWT_SECRET", env)
    if secret_key and env == "production":
        weak = {"secret", "changeme", "dev", "test", "development", "ci-test", "change-me"}
        if any(w in secret_key.lower() for w in weak):
            fail("JWT_SECRET", "Looks like a dev/test placeholder - rotate before production")

    enc_key = check_required("ENCRYPTION_KEY", env)
    if enc_key and len(enc_key) < 32 and env == "production":
        fail(
            "ENCRYPTION_KEY",
            "Too short - generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
        )

    # ── CORS & URLs ───────────────────────────────────────────────
    print("\n[ CORS & URLs ]")
    cors = check_required("BACKEND_CORS_ORIGINS", env)
    if cors and "*" in cors and env == "production":
        fail("BACKEND_CORS_ORIGINS", "Wildcard (*) CORS is forbidden in production")

    check_required(
        "FRONTEND_URL",
        env,
        extra_check=lambda v: v.startswith("http"),
        extra_msg="Must be a full URL (http or https)",
    )

    # ── Stripe ────────────────────────────────────────────────────
    print("\n[ Stripe ]")
    stripe_key = _get("STRIPE_SECRET_KEY")
    if not stripe_key or "placeholder" in stripe_key.lower():
        if env == "production":
            fail("STRIPE_SECRET_KEY", "MISSING - required for billing in production")
        else:
            warn("STRIPE_SECRET_KEY", "Not set - billing endpoints will return 503")
    elif stripe_key.startswith("sk_test_") and env == "production":
        warn("STRIPE_SECRET_KEY", "Using TEST key in production - is this intentional?")
    elif stripe_key.startswith("sk_live_"):
        ok("STRIPE_SECRET_KEY", "Live key set")
    else:
        ok("STRIPE_SECRET_KEY", f"Set ({_mask(stripe_key)})")

    webhook = _get("STRIPE_WEBHOOK_SECRET")
    if not webhook or "placeholder" in webhook.lower():
        if env == "production":
            fail("STRIPE_WEBHOOK_SECRET", "MISSING - required for webhook verification in production")
        elif env == "staging":
            warn("STRIPE_WEBHOOK_SECRET", "Not set - set whsec_... from Stripe test webhook endpoint")
        else:
            check_optional("STRIPE_WEBHOOK_SECRET", "Needed for webhook validation in staging/production")
    else:
        ok("STRIPE_WEBHOOK_SECRET", f"Set ({_mask(webhook)})")

    for price_key in [
        "STRIPE_PRICE_BASIC_MONTHLY",
        "STRIPE_PRICE_PRO_MONTHLY",
        "STRIPE_PRICE_BASIC_YEARLY",
        "STRIPE_PRICE_PRO_YEARLY",
    ]:
        val = _get(price_key)
        if not val or "placeholder" in val.lower():
            warn(price_key, "Not set - required when billing plans are active")
        else:
            ok(price_key, f"Set ({_mask(val)})")

    # ── Etsy ──────────────────────────────────────────────────────
    print("\n[ Etsy OAuth ]")
    etsy_id = _get("ETSY_CLIENT_ID")
    if not etsy_id or "placeholder" in etsy_id.lower():
        if env == "production":
            fail("ETSY_CLIENT_ID", "MISSING - required for Etsy shop connections in production")
        else:
            warn("ETSY_CLIENT_ID", "Not set - Etsy shop connection disabled")
    else:
        ok("ETSY_CLIENT_ID", f"Set ({_mask(etsy_id)})")

    check_required(
        "ETSY_REDIRECT_URI",
        env,
        extra_check=lambda v: v.startswith("http"),
        extra_msg="Must be a full callback URL",
    ) if env != "development" else check_optional("ETSY_REDIRECT_URI", "Must point to your callback route")

    # ── AI Provider ───────────────────────────────────────────────
    print("\n[ AI Provider ]")
    ai_provider = _get("AI_PROVIDER", "mock")
    ok("AI_PROVIDER", f"Set to '{ai_provider}'")

    if ai_provider == "openai":
        openai_key = _get("OPENAI_API_KEY")
        if not openai_key or "placeholder" in openai_key.lower():
            fail("OPENAI_API_KEY", "MISSING - required when AI_PROVIDER=openai") if env == "production" else warn("OPENAI_API_KEY", "AI suggestions will fail")
        else:
            ok("OPENAI_API_KEY", f"Set ({_mask(openai_key)})")
    elif ai_provider == "anthropic":
        anth_key = _get("ANTHROPIC_API_KEY")
        if not anth_key or "placeholder" in anth_key.lower():
            fail("ANTHROPIC_API_KEY", "MISSING - required when AI_PROVIDER=anthropic") if env == "production" else warn("ANTHROPIC_API_KEY", "AI suggestions will fail")
        else:
            ok("ANTHROPIC_API_KEY", f"Set ({_mask(anth_key)})")
    elif ai_provider == "mock":
        if env == "production":
            warn("AI_PROVIDER", "Mock provider in production - AI features return placeholder responses")
        else:
            ok("AI_PROVIDER", "Mock provider - no API costs in dev/CI")
    else:
        fail("AI_PROVIDER", f"Unknown provider '{ai_provider}' - expected mock, openai, or anthropic")

    # ── Rate Limiting ─────────────────────────────────────────────
    print("\n[ Rate Limiting ]")
    rl_enabled = _get("RATE_LIMIT_ENABLED", "false").lower()
    if rl_enabled in ("false", "0") and env == "production":
        warn("RATE_LIMIT_ENABLED", "Rate limiting is DISABLED - set to true in production")
    else:
        ok("RATE_LIMIT_ENABLED", rl_enabled)

    rl_backend = _get("RATE_LIMIT_BACKEND", "memory")
    if rl_backend == "memory" and env == "production":
        warn("RATE_LIMIT_BACKEND", "Using in-memory backend - set to 'redis' for multi-worker support")
    else:
        ok("RATE_LIMIT_BACKEND", rl_backend)

    # ── Observability ─────────────────────────────────────────────
    print("\n[ Observability ]")
    sentry_dsn = _get("SENTRY_DSN")
    if not sentry_dsn:
        if env == "production":
            warn("SENTRY_DSN", "Not set - errors won't be tracked in Sentry")
        else:
            ok("SENTRY_DSN", "Not set (optional in dev/staging)")
    elif sentry_dsn.startswith("https://") and "sentry.io" in sentry_dsn:
        ok("SENTRY_DSN", f"Set ({_mask(sentry_dsn)})")
    else:
        warn("SENTRY_DSN", f"Value doesn't look like a Sentry DSN: {_mask(sentry_dsn)}")

    sentry_env = _get("SENTRY_ENVIRONMENT")
    if not sentry_env and env in ("staging", "production"):
        warn("SENTRY_ENVIRONMENT", f"Not set - set to '{env}' for correct error grouping in Sentry")
    elif sentry_env:
        ok("SENTRY_ENVIRONMENT", f"Set to '{sentry_env}'")

    # ── Video Renderer ────────────────────────────────────────────
    print("\n[ Video Renderer ]")
    vr_enabled = _get("VIDEO_RENDERER_ENABLED", "false").lower()
    if vr_enabled in ("true", "1"):
        ok("VIDEO_RENDERER_ENABLED", "Enabled")
        ffmpeg_path = _get("FFMPEG_PATH")
        if ffmpeg_path:
            ok("FFMPEG_PATH", "Override set (not validated here — checked at runtime)")
        else:
            ok("FFMPEG_PATH", "Not set — using system ffmpeg (default)")
        vod = _get("VIDEO_OUTPUT_DIR")
        if vod:
            ok("VIDEO_OUTPUT_DIR", "Override set")
        else:
            ok("VIDEO_OUTPUT_DIR", "Not set — using default /tmp/video_renders")
    else:
        if env == "production":
            warn("VIDEO_RENDERER_ENABLED", "Disabled — Video Generator will show unavailable modal to customers")
        else:
            ok("VIDEO_RENDERER_ENABLED", "Disabled (set to true to enable Video Generator)")

    # ── Social Integrations ───────────────────────────────────────
    print("\n[ Social Integrations ]")

    pinterest_id = _get("PINTEREST_CLIENT_ID")
    pinterest_secret = _get("PINTEREST_CLIENT_SECRET")
    pinterest_redirect = _get("PINTEREST_REDIRECT_URI")
    if pinterest_id and pinterest_secret and pinterest_redirect:
        ok("PINTEREST_CLIENT_ID", f"Set ({_mask(pinterest_id)})")
        ok("PINTEREST_CLIENT_SECRET", "Set (masked)")
        ok("PINTEREST_REDIRECT_URI", f"Set ({pinterest_redirect})")
    else:
        missing_p = [k for k, v in [
            ("PINTEREST_CLIENT_ID", pinterest_id),
            ("PINTEREST_CLIENT_SECRET", pinterest_secret),
            ("PINTEREST_REDIRECT_URI", pinterest_redirect),
        ] if not v]
        msg = f"Missing {len(missing_p)} var(s) — Pinterest Connect disabled"
        if env == "production":
            warn("Pinterest", msg)
        else:
            ok("Pinterest", f"Not configured ({msg})")

    meta_id = _get("META_APP_ID")
    meta_secret = _get("META_APP_SECRET")
    instagram_redirect = _get("INSTAGRAM_REDIRECT_URI")
    if meta_id and meta_secret and instagram_redirect:
        ok("META_APP_ID", f"Set ({_mask(meta_id)})")
        ok("META_APP_SECRET", "Set (masked)")
        ok("INSTAGRAM_REDIRECT_URI", f"Set ({instagram_redirect})")
    else:
        missing_m = [k for k, v in [
            ("META_APP_ID", meta_id),
            ("META_APP_SECRET", meta_secret),
            ("INSTAGRAM_REDIRECT_URI", instagram_redirect),
        ] if not v]
        msg = f"Missing {len(missing_m)} var(s) — Instagram Connect disabled"
        if env == "production":
            warn("Instagram/Meta", msg)
        else:
            ok("Instagram/Meta", f"Not configured ({msg})")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  Results")
    print(f"{'='*60}")
    for status, name, msg in results:
        line = f"  {status}  {name}"
        if msg:
            line += f"\n     {msg}"
        print(line)

    print(f"\n{'='*60}")
    if errors == 0 and warnings == 0:
        print(f"  [{PASS}]  All checks passed ({env})")
    elif errors == 0:
        print(f"  [{WARN}]  {warnings} warning(s), 0 errors ({env})")
    else:
        print(f"  [{FAIL}]  {errors} error(s), {warnings} warning(s) ({env})")
    print(f"{'='*60}\n")

    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()
