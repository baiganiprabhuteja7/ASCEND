from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/skills_to_impact.db"
    cors_origins: str = "http://localhost:5173"
    llm_api_key: str | None = None
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_model: str = "gemini-3.8-flash"
    llm_timeout_seconds: float = 30
    llm_connect_timeout_seconds: float = 5

    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def llm_api_key_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_api_key.strip())

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
