import os
from typing import Literal
from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlmodel import create_engine
from urllib.parse import quote_plus


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""
    ENVIRONMENT: Literal["local", "development", "production"] = "local"
    SSL_MODE: str = "" if ENVIRONMENT == "local" else "sslmode=require"

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        url = MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=quote_plus(self.POSTGRES_PASSWORD),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
            query=self.SSL_MODE
        )
        return url


settings = Settings()  # type: ignore

def init_engine():
    SSL_MODE: str = settings.SSL_MODE
    # Connect to the default database to check if the target database exists and create it if not
    default_engine = create_engine(
        f"postgresql://{settings.POSTGRES_USER}:{quote_plus(settings.POSTGRES_PASSWORD)}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres?{SSL_MODE}"
    )
    with default_engine.connect() as connection:
        connection.execute(text("COMMIT"))
        result = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": settings.POSTGRES_DB},
        ).fetchone()
        if not result:
            connection.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
            print(f"Database {settings.POSTGRES_DB} created.")