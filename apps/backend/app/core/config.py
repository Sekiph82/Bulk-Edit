import json
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://bulkedit:bulkedit_password@localhost:55432/bulkedit"
    REDIS_URL: str = "redis://localhost:56379/0"

    FRONTEND_URL: str = "http://localhost:3100"
    BACKEND_URL: str = "http://localhost:8100"

    # Accepts plain string, comma-separated, or JSON array string.
    BACKEND_CORS_ORIGINS: str = "http://localhost:3100"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    STRIPE_SECRET_KEY: str = "stripe_secret_key_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "webhook_secret_placeholder"
    STRIPE_PRICE_BASIC_MONTHLY: str = "price_placeholder_basic_monthly"
    STRIPE_PRICE_PRO_MONTHLY: str = "price_placeholder_pro_monthly"
    STRIPE_PRICE_BASIC_YEARLY: str = "price_placeholder_basic_yearly"
    STRIPE_PRICE_PRO_YEARLY: str = "price_placeholder_pro_yearly"

    # Fernet key for encrypting Etsy tokens. Must be 32 url-safe base64 bytes.
    # WARNING: default is a dev-only fallback — never use in production.
    ENCRYPTION_KEY: str = "ZGV2X2VuY3J5cHRpb25fa2V5X3BsYWNlaG9sZGVyISE="

    ETSY_CLIENT_ID: str = "etsy_client_id_placeholder"
    ETSY_REDIRECT_URI: str = "http://localhost:8100/api/v1/etsy/callback"
    ETSY_SCOPES: str = "listings_r listings_w shops_r profile_r"

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = False  # Enable in production; off by default for local dev / tests
    RATE_LIMIT_BACKEND: str = "memory"  # "memory" or "redis"
    RATE_LIMIT_REDIS_URL: str = ""  # defaults to REDIS_URL if empty
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_REGISTER_PER_MINUTE: int = 5
    RATE_LIMIT_CONTACT_PER_HOUR: int = 5

    # Sentry error monitoring (optional)
    SENTRY_DSN: str = ""  # leave empty to disable
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    # AI providers
    AI_PROVIDER: str = "mock"  # "mock" | "openai" | "anthropic"
    OPENAI_API_KEY: str = "openai_api_key_placeholder"
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = "anthropic_api_key_placeholder"
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"
    AI_REQUEST_TIMEOUT_SECONDS: int = 30

    # Etsy API rate limit guidance
    ETSY_API_REQUESTS_PER_SECOND: float = 5.0
    ETSY_API_DAILY_LIMIT: int = 5000
    ETSY_API_BURST_LIMIT: int = 10
    ETSY_BULK_WRITE_BATCH_SIZE: int = 10
    ETSY_BULK_WRITE_DELAY_MS: int = 200
    ETSY_RETRY_MAX_ATTEMPTS: int = 3

    # Social integrations (optional — empty = not configured)
    PINTEREST_CLIENT_ID: str = ""
    PINTEREST_CLIENT_SECRET: str = ""
    PINTEREST_REDIRECT_URI: str = ""
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    INSTAGRAM_REDIRECT_URI: str = ""

    # Video renderer
    VIDEO_RENDERER_ENABLED: bool = False
    FFMPEG_PATH: str = "ffmpeg"
    VIDEO_OUTPUT_DIR: str = "/tmp/video_renders"
    VIDEO_MAX_DURATION_SECONDS: int = 30
    VIDEO_MAX_IMAGES: int = 20

    def is_openai_configured(self) -> bool:
        key = self.OPENAI_API_KEY
        return bool(key) and "placeholder" not in key.lower() and key.startswith("sk-")

    def is_anthropic_configured(self) -> bool:
        key = self.ANTHROPIC_API_KEY
        return bool(key) and "placeholder" not in key.lower() and key.startswith("sk-ant-")

    def is_etsy_configured(self) -> bool:
        cid = self.ETSY_CLIENT_ID
        return bool(cid) and "placeholder" not in cid.lower() and cid != "REPLACE_ME"

    def is_stripe_configured(self) -> bool:
        key = self.STRIPE_SECRET_KEY
        return key.startswith("sk_test_") or key.startswith("sk_live_")

    def is_stripe_webhook_configured(self) -> bool:
        return self.STRIPE_WEBHOOK_SECRET.startswith("whsec_")

    def get_stripe_price_id(self, plan: str) -> str | None:
        mapping = {
            "basic_monthly": self.STRIPE_PRICE_BASIC_MONTHLY,
            "pro_monthly": self.STRIPE_PRICE_PRO_MONTHLY,
            "basic_yearly": self.STRIPE_PRICE_BASIC_YEARLY,
            "pro_yearly": self.STRIPE_PRICE_PRO_YEARLY,
        }
        price_id = mapping.get(plan)
        if price_id and "placeholder" not in price_id:
            return price_id
        return None

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _force_asyncpg_driver(cls, v: str) -> str:
        """Normalize the DB scheme to the async driver.

        Managed Postgres providers (Render, Neon, Supabase, Heroku) hand out
        connection strings as ``postgres://`` or ``postgresql://``. SQLAlchemy's
        async engine requires the ``postgresql+asyncpg://`` scheme. Rewrite the
        scheme so a raw provider URL works unchanged; leave any explicit
        ``+driver`` (e.g. the local ``postgresql+asyncpg://``) untouched.
        """
        if v.startswith("postgresql+"):
            return v
        if v.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v[len("postgresql://"):]
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[len("postgres://"):]
        return v

    def get_cors_origins(self) -> List[str]:
        v = self.BACKEND_CORS_ORIGINS.strip()
        if v.startswith("["):
            try:
                result = json.loads(v)
                if isinstance(result, list):
                    return [str(o) for o in result]
            except json.JSONDecodeError:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


settings = Settings()
