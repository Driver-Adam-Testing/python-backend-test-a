import warnings
from typing import Annotated, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


DEFAULT_SECRET = "changethis"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    STUDIO_V1_STR: str = "/studio/v1"
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    AUTH0_DOMAIN: str = DEFAULT_SECRET
    AUTH0_CLIENT_ID: str = DEFAULT_SECRET
    AUTH0_AUDIENCE: str = DEFAULT_SECRET

    AUTH0_MGMT_API_DOMAIN: str = DEFAULT_SECRET
    AUTH0_MGMT_API_CLIENT_ID: str = DEFAULT_SECRET
    AUTH0_MGMT_API_CLIENT_SECRET: str = DEFAULT_SECRET
    AUTH0_MGMT_API_AUDIENCE: str = DEFAULT_SECRET

    AWS_ACCESS_KEY_ID: str = DEFAULT_SECRET
    AWS_SECRET_ACCESS_KEY: str = DEFAULT_SECRET
    AWS_REGION: str = DEFAULT_SECRET
    AWS_S3_ENDPOINT_URL: str | None = None
    AWS_S3_CODE_BUCKET_SUFFIX: str = DEFAULT_SECRET
    DROPZONE_BUCKET_NAME: str = DEFAULT_SECRET
    USE_LEGACY_DROPZONE: bool | None = True
    INSPECTOR_BUCKET_NAME: str = DEFAULT_SECRET

    PORT: int = 8000
    HOST: str = "127.0.0.1"

    GH_CLIENT_ID: str = DEFAULT_SECRET
    GH_CLIENT_SECRET: str = DEFAULT_SECRET
    GH_REDIRECT_URI: str = DEFAULT_SECRET
    GH_WEBHOOK_SECRET: str = DEFAULT_SECRET
    GH_CLIENT_PEM_SECRET: str = DEFAULT_SECRET

    MODAL_ENVIRONMENT: str = DEFAULT_SECRET

    SENTRY_DSN: str | None = None

    LOG_LEVEL: str = "INFO"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    PROJECT_NAME: str = DEFAULT_SECRET

    @model_validator(mode="after")
    def _check_non_default_secrets(self) -> Self:
        for field_name, field_info in self.model_fields.items():
            default_value = field_info.default
            actual_value = getattr(self, field_name)
            # Only check fields where default == DEFAULT_SECRET and actual value hasn't changed
            if (
                isinstance(default_value, str)
                and default_value == DEFAULT_SECRET
                and actual_value == DEFAULT_SECRET
            ):
                self._handle_default_secret(field_name)
        return self

    def _handle_default_secret(self, var_name: str) -> None:
        message = (
            f"The value of {var_name} is set to '{DEFAULT_SECRET}'. "
            "Please change it before deploying."
        )
        if self.ENVIRONMENT == "local":
            warnings.warn(message, stacklevel=1)
        else:
            raise ValueError(message)


settings = Settings()
