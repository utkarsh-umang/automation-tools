"""Central configuration via Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from env."""

    model_config = SettingsConfigDict(
        # Load from monorepo root .env first, then backend-app/local.env
        env_file=("../.env", "local.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──
    ENVIRONMENT: str = "local"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5174"]
    API_V1_STR: str = "/api/v1"

    # ── Postgres ──
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 54332
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "myapp"

    # ── MongoDB ──
    MONGO_LOCAL_URI: str = "mongodb://localhost:27017"
    MONGO_PROD_URI: str | None = None
    MONGO_DB_NAME: str = "myapp_docs"
    MONGO_TEST_DB_NAME: str = "myapp_docs_test"

    # ── Redis ──
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6383
    REDIS_PASSWORD: str | None = None

    # ── Celery / Flower (Flower UI for local dev; health checks this URL) ──
    FLOWER_URL: str = "http://localhost:5555"

    # ── Auth ──
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── YouTube ──
    YOUTUBE_API_KEY_V3: str = ""
    YOUTUBE_DAILY_CREDIT_LIMIT: int = 10000

    # ── GCP (optional) ──
    GCP_PROJECT_ID: str | None = None
    GCP_SECRET_NAME: str | None = None

    # ── Google Sheets ──
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"

    # ── Thumbnail pipeline (S3 upload from Celery worker) ──
    AWS_REGION: str = "ap-south-1"
    THUMBNAIL_S3_BUCKET: str = "thumbnail-generator-ai-agent"
    THUMBNAIL_S3_ENDPOINT_URL: str | None = None
    THUMBNAIL_S3_PUBLIC_BASE_URL: str | None = None
    THUMBNAIL_S3_USE_PRESIGNED_URL: bool = False
    THUMBNAIL_S3_PRESIGNED_EXPIRES_SECONDS: int = 3600
    THUMBNAIL_INPUT_MAX_BYTES: int = 10 * 1024 * 1024

    # ── Observability (optional) ──
    SENTRY_DSN: str | None = None

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Redis URL for Celery broker and result backend."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [v]
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


config = get_settings()
