import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "development", "production"] = "local"
    AUTH0_DOMAIN: str | None = None
    AUTH0_CLIENT_ID: str | None = None
    AUTH0_AUDIENCE: str | None = None

    AUTH0_MGMT_API_CLIENT_ID: str | None = None
    AUTH0_MGMT_API_CLIENT_SECRET: str | None = None
    AUTH0_MGMT_API_AUDIENCE: str | None = None

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_S3_ENDPOINT_URL: str | None = None
    AWS_S3_CODE_BUCKET_SUFFIX: str | None = None

    PORT: int | None = None
    HOST: str | None = None

    GH_CLIENT_ID: str | None = None
    GH_CLIENT_SECRET: str | None = None
    GH_REDIRECT_URI: str | None = None
    GH_WEBHOOK_SECRET: str | None = None

    OPENAI_API_KEY: str | None = None

    MODAL_ENVIRONMENT: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    BUCKET_NAME: str | None = None

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)


settings = Settings()  # type: ignore
