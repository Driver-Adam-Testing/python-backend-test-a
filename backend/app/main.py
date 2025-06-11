"""main.py - FastAPI application bootstrap

Mount order:
1. **unprotected_router** - no auth required.
2. **studio_router**      - JWT-protected via `require_jwt`.
3. **api_router**         - API-key-protected via `require_api_key`.

The Sentry and logging setup is unchanged.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from logging import Formatter, LogRecord
from typing import TYPE_CHECKING, Literal

import sentry_sdk
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.api_router import api_router
from app.api.logging_middleware import LoggingMiddleware
from app.api.studio_router import studio_router
from app.api.unprotected_router import unprotected_router  # NEW
from app.auth.api_key_middleware import require_api_key
from app.auth.jwt_middleware import require_jwt
from app.core.config import settings

if TYPE_CHECKING:
    from fastapi.routing import APIRoute

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Logging & Sentry
# ---------------------------------------------------------------------------


class JsonFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        json_record = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            json_record["traceback"] = self.formatException(record.exc_info)
        return json.dumps(json_record)


def _configure_logging() -> None:
    log_level = settings.LOG_LEVEL.upper()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=log_level, handlers=[handler])
    logging.info("Log Level set to %s", log_level)


def _configure_sentry(
    env: Literal["local", "development", "staging", "production"], dsn: str
) -> None:
    if env == "local":
        return

    sample_rate = {"development": 1.0, "staging": 0.5, "production": 0.1}[env]
    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        send_default_pii=False,
        traces_sample_rate=sample_rate,
        _experiments={"continuous_profiling_auto_start": env != "production"},
    )


_configure_logging()
_configure_sentry(settings.ENVIRONMENT, settings.SENTRY_DSN)


# ---------------------------------------------------------------------------
#  FastAPI app
# ---------------------------------------------------------------------------


def _unique_id(route: APIRoute) -> str:  # pragma: no cover - deterministic IDs
    # TODO: this is a hack to make the api router work with the studio router
    return f"{route.tags[0]}-{route.name}"


# we should probably be documenting the api router, not the studio router
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.STUDIO_V1_STR}/openapi.json",
    generate_unique_id_function=_unique_id,
)

# CORS ----------------------------------------------------------------------
if settings.BACKEND_CORS_ORIGINS:
    logging.info("Setting CORS to %s", settings.BACKEND_CORS_ORIGINS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o).strip("/") for o in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware -----------------------------------------------------------------
app.add_middleware(LoggingMiddleware)

# Routers --------------------------------------------------------------------
# TODO: move unprotected router to unprefixed
app.include_router(
    unprotected_router,
    prefix=settings.STUDIO_V1_STR,  # no auth
)
app.include_router(
    studio_router, prefix=settings.STUDIO_V1_STR, dependencies=[Depends(require_jwt)]
)
app.include_router(
    api_router, prefix=settings.API_V1_STR, dependencies=[Depends(require_api_key)]
)


# ---------------------------------------------------------------------------
#  Global error handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content="Something went wrong. This error has been logged and the team will be investigating.",
    )
