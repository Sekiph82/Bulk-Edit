import json
from typing import List
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

    # AI providers
    AI_PROVIDER: str = "mock"  # "mock" | "openai" | "anthropic"
    OPENAI_API_KEY: str = "openai_api_key_placeholder"
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = "anthropic_api_key_placeholder"
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"
    AI_REQUEST_TIMEOUT_SECONDS: int = 30

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
