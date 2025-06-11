import json
import logging
import logging.handlers
from datetime import datetime
from logging import Formatter, LogRecord
from typing import Literal

import sentry_sdk
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.api_router import api_router
from app.api.auth import require_api_key, require_jwt
from app.api.logging_middleware import LoggingMiddleware
from app.api.studio_router import studio_router
from app.core.config import settings

logger = logging.getLogger(__name__)


class JsonFormatter(Formatter):
    def __init__(self) -> None:
        super().__init__()

    def format(self, record: LogRecord) -> str:
        json_record = {}
        json_record["level"] = record.levelname
        json_record["timestamp"] = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        json_record["name"] = record.name
        json_record["message"] = record.getMessage()
        if record.exc_info:
            json_record["traceback"] = self.formatException(record.exc_info)
        return json.dumps(json_record)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


def configure_logging() -> None:
    log_level = settings.LOG_LEVEL.upper()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=log_level, handlers=[handler])
    logging.info(f"Log Level set to {log_level}")


def configure_sentry(
    environment: Literal["local", "development", "staging", "production"], dsn: str
) -> None:
    match environment:
        case "local":
            pass

        case "development":
            sentry_sdk.init(
                dsn=dsn,
                environment="development",
                send_default_pii=False,
                traces_sample_rate=1.0,
                _experiments={
                    "continuous_profiling_auto_start": True,
                },
            )
        case "staging":
            sentry_sdk.init(
                dsn=dsn,
                environment="staging",
                send_default_pii=False,
                traces_sample_rate=0.5,  # Arbitrarily set, but tests dialing down the rate
                _experiments={
                    "continuous_profiling_auto_start": True,
                },
            )
        case "production":
            sentry_sdk.init(
                dsn=dsn,
                environment="production",
                send_default_pii=False,
                traces_sample_rate=0.1,
                _experiments={
                    "continuous_profiling_auto_start": False,
                },
            )
        case _:
            logger.warning(
                "Unrecognized environment '%s'; Sentry is not configured",
                environment,
            )


configure_logging()

configure_sentry(settings.ENVIRONMENT, settings.SENTRY_DSN)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.STUDIO_V1_STR}/openapi.json",  # TODO: This will need to change to only include public endpoints...
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    logging.info(f"Setting CORS to {settings.BACKEND_CORS_ORIGINS}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(LoggingMiddleware)

app.include_router(
    studio_router, prefix=settings.STUDIO_V1_STR, dependencies=[Depends(require_jwt)]
)
app.include_router(
    api_router, prefix=settings.API_V1_STR, dependencies=[Depends(require_api_key)]
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.error("Unhandled exception", exc_info=exc)
    # Return the JSON response with the appropriate status code
    return JSONResponse(
        status_code=500,
        content="Something went wrong. This error has been logged and the team will be investigating.",
    )
