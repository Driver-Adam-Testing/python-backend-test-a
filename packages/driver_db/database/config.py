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

    ENVIRONMENT: str = "local"

    # NOTE: if DATABASE_URL is set, it overrides the other postgres params
    DATABASE_URL: str | None = None

    ASYNC_DATABASE_URL: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn | str:
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

    @computed_field
    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn | str:
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        else:
            url = MultiHostUrl.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=quote_plus(self.POSTGRES_PASSWORD),
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
                query=self.SSL_MODE,
            )
            return url

    @computed_field
    @property
    def SSL_MODE(self) -> str:
        return "sslmode=require" if self.ENVIRONMENT != "local" else ""


settings = Settings()  # type: ignore
