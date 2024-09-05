from typing import Literal
from urllib.parse import quote_plus

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    POSTGRES_SERVER: str | None = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str = ""
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    SSL_MODE: str = "" if ENVIRONMENT == "local" else "sslmode=require"

    # NOTE: if DATABASE_URL is set, it overrides the other postgres params
    DATABASE_URL: str | None = None

    ASYNC_DATABASE_URL: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        else:
            url = MultiHostUrl.build(
                scheme="postgresql+psycopg2",
                username=self.POSTGRES_USER,
                password=quote_plus(self.POSTGRES_PASSWORD),
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
                query=self.SSL_MODE,
            )
            return url


settings = Settings()  # type: ignore
