from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Groq
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    groq_router_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_ROUTER_MODEL")
    groq_max_tokens: int = Field(default=1024, alias="GROQ_MAX_TOKENS")
    groq_temperature: float = Field(default=0.2, alias="GROQ_TEMPERATURE")

    # Langfuse
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_base_url: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_BASE_URL")
    langfuse_host: str | None = Field(default=None, alias="LANGFUSE_HOST")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    session_ttl_seconds: int = Field(default=3600, alias="SESSION_TTL_SECONDS")

    # Database
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # App
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    data_dir: str = Field(default="data", alias="DATA_DIR")


@lru_cache
def get_settings() -> Settings:
    return Settings()
