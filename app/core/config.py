"""Application configuration loaded from environment."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for all external integrations."""

    deepgram_api_key: str = "test_deepgram_key"
    elevenlabs_api_key: str = "test_elevenlabs_key"
    openai_api_key: str = "test_openai_key"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "voice_interview"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("deepgram_api_key", "elevenlabs_api_key", "openai_api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        """Validate API keys are non-empty strings."""

        if not value or len(value.strip()) < 8:
            raise ValueError("API keys must be at least 8 characters")
        return value


@lru_cache

def get_settings() -> Settings:
    """Return cached settings singleton."""

    return Settings()


settings = get_settings()
