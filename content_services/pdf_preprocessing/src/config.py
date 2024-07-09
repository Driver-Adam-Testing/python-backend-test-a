import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    ENVIRONMENT: Literal["local", "ops", "development", "production"]
    OPENAI_API_KEY: str


settings = Settings()  # type: ignore
