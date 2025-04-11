from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str

    NGROK_API_KEY: str
    AUTH0_URL: str
    AUTH0_DOMAIN: str
    AUTH0_MGMT_API_CLIENT_ID: str
    AUTH0_MGMT_API_CLIENT_SECRET: str
    AUTH0_MGMT_API_AUDIENCE: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    OPENAI_API_KEY: str

    MODAL_TOKEN_ID: str
    MODAL_TOKEN_SECRET: str


settings = Settings()  # type: ignore
