from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None

    NGROK_API_KEY: str
    AUTH0_URL: str | None = None
    AUTH0_DOMAIN: str | None = None
    AUTH0_MGMT_API_CLIENT_ID: str | None = None
    AUTH0_MGMT_API_CLIENT_SECRET: str | None = None
    AUTH0_MGMT_API_AUDIENCE: str | None = None

    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None

    OPENAI_API_KEY: str | None = None

    MODAL_TOKEN_ID: str | None = None
    MODAL_TOKEN_SECRET: str | None = None


settings = Settings()  # type: ignore
