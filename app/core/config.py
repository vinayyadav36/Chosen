"""Application configuration via environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.constants import DEFAULT_BACKUP_THRESHOLD, DEFAULT_HIRE_THRESHOLD


class Settings(BaseSettings):
    """Settings model loaded from .env."""

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    deepgram_api_key: str | None = Field(default=None, alias="DEEPGRAM_API_KEY")
    elevenlabs_api_key: str | None = Field(default=None, alias="ELEVENLABS_API_KEY")

    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="hybrid_interview_db", alias="MONGODB_DB_NAME")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=True, alias="DEBUG")
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"], alias="ALLOWED_ORIGINS")

    default_question_count: int = Field(default=8, alias="DEFAULT_QUESTION_COUNT")
    score_hire_threshold: float = Field(default=DEFAULT_HIRE_THRESHOLD, alias="SCORE_HIRE_THRESHOLD")
    score_backup_threshold: float = Field(default=DEFAULT_BACKUP_THRESHOLD, alias="SCORE_BACKUP_THRESHOLD")

    voice_sample_rate: int = Field(default=16000, alias="VOICE_SAMPLE_RATE")
    voice_channels: int = Field(default=1, alias="VOICE_CHANNELS")
    voice_encoding: str = Field(default="linear16", alias="VOICE_ENCODING")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, populate_by_name=True)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        """Parse ALLOWED_ORIGINS from comma-separated env value."""

        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""

    return Settings()


settings = get_settings()
