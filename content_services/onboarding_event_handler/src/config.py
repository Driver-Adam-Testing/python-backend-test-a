import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_URL: str
    AUTH0_URL: str
    CLIENT_ID_SECRET: str
    CLIENT_SECRET_SECRET: str
    ENVIRONMENT: Literal["local"]

settings = Settings()  # type: ignore
