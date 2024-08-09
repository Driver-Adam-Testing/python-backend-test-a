import logging
import uuid
from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = uuid.uuid4()
        now = datetime.now()
        response = await call_next(request)
        response_time = datetime.now() - now
        client_host = request.client.host if request.client and request.client.host else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For", client_host)
        logger.info(
            f"{request_id} {request.method} {request.url.path} {forwarded_for} Status={response.status_code} ResponseTime={int(response_time.total_seconds() * 1000)}ms"
        )
        return response