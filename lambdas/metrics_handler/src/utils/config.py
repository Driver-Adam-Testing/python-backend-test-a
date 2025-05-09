from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    ENVIRONMENT: Literal[
        "local", "ops", "development", "staging", "production", "cloud-local"
    ] = "local"
    DATABASE_URL: str | None = None
    DATABASE_URL_SECRET_NAME: str


settings = Settings()  # type: ignore
