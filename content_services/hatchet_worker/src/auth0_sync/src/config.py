from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    # Database
    # TODO: Remove default value - it bypasses validation and allows invalid config.
    # Tests should mock settings or set env vars properly instead of relying on defaults.
    DATABASE_URL: str = "postgresql://localhost/test"

    # Auth0
    AUTH0_MGMT_API_DOMAIN: str
    AUTH0_MGMT_API_CLIENT_ID: str
    AUTH0_MGMT_API_CLIENT_SECRET: str
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str


settings = Settings()  # type: ignore
