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
        logger.info(
            f"{request_id} {request.headers["X-Fowarded-For"] if "X-Fowarded-For" in request.headers.keys() else request.client.host} Status={response.status_code} ResponseTime={int(response_time.total_seconds() * 1000)}ms"
        )
        return response
