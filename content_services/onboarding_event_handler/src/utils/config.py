from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_URL: str
    AUTH0_URL: str
    AUTH0_AUDIENCE: str
    CLIENT_ID_SECRET: str
    CLIENT_SECRET_SECRET: str
    ENVIRONMENT: Literal[
        "local", "ops", "development", "staging", "production", "cloud-local", "pms"
    ]
    AWS_S3_ENDPOINT_URL: str | None = None
    AWS_S3_CODE_BUCKET_SUFFIX: str = "codebase-dropzone"
    USE_LEGACY_DROPZONE: bool = True
    DROPZONE_BUCKET_NAME: str | None = None


settings = Settings()  # type: ignore
