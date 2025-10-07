import json
import logging
from datetime import datetime
from enum import StrEnum
from logging import Formatter, LogRecord
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult  # noqa: TCH002
from pydantic import BaseModel

from app.mcp.auth_middleware import get_organization_id, get_user, get_user_id


class _McpComponentType(StrEnum):
    TOOL = "tool"
    PROMPT = "prompt"
    RESOURCE = "resource"


class _McpLogData(BaseModel):
    component_name: str
    component_type: _McpComponentType
    params: dict[str, Any] | None
    response: str | None
    errors: list | None
    org_id: str
    org_name: str
    user_id: str
    user_email: str


class _McpJsonFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        json_record = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "name": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
                "taskName",
            }:
                json_record[key] = value

        return json.dumps(json_record)


class McpLoggingMiddleware(Middleware):
    def __init__(self) -> None:
        self._RESPONSE_MAX_LENGTH = 500
        self._logger = logging.getLogger(__name__)

        handler = logging.StreamHandler()
        handler.setFormatter(_McpJsonFormatter())
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    async def on_call_tool(self, ctx: MiddlewareContext, call_next: any) -> any:
        user = get_user(ctx.fastmcp_context)

        log_data = _McpLogData(
            component_name=ctx.message.name,
            component_type=_McpComponentType.TOOL,
            params=ctx.message.arguments,
            response=None,
            errors=None,
            org_id=get_organization_id(ctx.fastmcp_context),
            org_name=user["org_name"],
            user_id=get_user_id(ctx.fastmcp_context),
            user_email=user["user_email"],
        )

        try:
            tool_result: ToolResult = await call_next(ctx)
            log_data.response = (
                str(tool_result.content[0].text)[: self._RESPONSE_MAX_LENGTH] + "..."
            )
            self._logger.info(
                "Tool call completed without errors", extra=log_data.model_dump()
            )

        except ToolError as e:
            log_data.errors = [str(e)]
            self._logger.error(
                "Tool call completed with errors", extra=log_data.model_dump()
            )
            raise

        return tool_result

    async def on_get_prompt(self, ctx: MiddlewareContext, call_next: any) -> any:
        user = get_user(ctx.fastmcp_context)

        log_data = _McpLogData(
            component_name=ctx.message.name,
            component_type=_McpComponentType.PROMPT,
            params=None,
            response=None,
            errors=None,
            org_id=get_organization_id(ctx.fastmcp_context),
            org_name=user["org_name"],
            user_id=get_user_id(ctx.fastmcp_context),
            user_email=user["user_email"],
        )

        self._logger.info("Prompt requested", extra=log_data.model_dump())

        return await call_next(ctx)
