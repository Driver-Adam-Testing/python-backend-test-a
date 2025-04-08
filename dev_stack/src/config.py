from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    NGROK_API_KEY: str
    AUTH0_DOMAIN: str
    AUTH0_MGMT_API_CLIENT_ID: str
    AUTH0_MGMT_API_CLIENT_SECRET: str
    AUTH0_MGMT_API_AUDIENCE: str


settings = Settings()  # type: ignore
