from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is two levels up from this file (backend/app/config.py)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    APP_NAME: str = "Council of Agents"
    DEBUG: bool = True


settings = Settings()
