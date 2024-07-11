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

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_S3_ENDPOINT_URL: str | None = None
    AWS_S3_CODE_BUCKET_SUFFIX: str | None = None

settings = Settings()  # type: ignore
