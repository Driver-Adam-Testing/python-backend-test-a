import json
import logging
import logging.handlers
from datetime import datetime
from logging import Formatter, LogRecord

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.auth import AuthMiddleware
from app.api.logging_middleware import LoggingMiddleware
from app.api.main import api_router
from app.core.config import settings


class JsonFormatter(Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record: LogRecord):
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


def configure_logging():
    log_level = settings.LOG_LEVEL.upper()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=log_level, handlers=[handler])
    logging.info(f"Log Level set to {log_level}")


configure_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
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
app.add_middleware(AuthMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error("Unhandled exception", exc_info=exc)
    # Return the JSON response with the appropriate status code
    return JSONResponse(
        status_code=500,
        content="Something went wrong. This error has been logged and the team will be investigating.",
    )
