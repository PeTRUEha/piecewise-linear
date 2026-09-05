"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend process."""

    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "Piecewise Linear API"
    database_url: PostgresDsn = Field(
        default=PostgresDsn(
            "postgresql+asyncpg://piecewise_linear:piecewise_linear@localhost:5432/piecewise_linear"
        ),
        validation_alias="DATABASE_URL",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
