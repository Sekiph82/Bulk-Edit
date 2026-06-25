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
