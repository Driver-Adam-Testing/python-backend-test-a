import logging
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = uuid.uuid4()
        logger.info(
            f"Request ID {request_id} from {request.client.host} : {request.method} {request.url}"
        )
        response = await call_next(request)
        logger.info(
            f"Response ID {request_id} from {request.client.host} : {response.status_code}"
        )
        return response
