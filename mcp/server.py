"""HTTP MCP server — sole enterprise tool boundary for ACSP agents."""

from __future__ import annotations

import json
import time

from fastapi import FastAPI
from pydantic import ValidationError

from gateway.masking.sensitive_data_masker import mask_sensitive_data
from mcp.registry import ToolRegistry, build_default_registry
from shared.config.settings import get_settings
from shared.logging.context import reset_correlation_id, set_correlation_id
from shared.logging.setup import get_logger
from shared.schemas.common import HealthResponse
from shared.schemas.mcp import (
    McpError,
    McpStatus,
    McpToolDescriptor,
    McpToolRequest,
    McpToolResponse,
)
from shared.utils.datetime import utc_now

logger = get_logger(__name__)


def create_mcp_app(registry: ToolRegistry | None = None) -> FastAPI:
    settings = get_settings()
    tool_registry = registry or build_default_registry()
    app = FastAPI(
        title=f"{settings.app_name} MCP",
        version="0.1.0",
        debug=settings.debug,
    )
    app.state.registry = tool_registry

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse(app_name=f"{settings.app_name} MCP", environment=settings.app_env)

    @app.get("/mcp/v1/tools", response_model=list[McpToolDescriptor], tags=["mcp"])
    def list_tools() -> list[McpToolDescriptor]:
        return tool_registry.list_tools()

    @app.post("/mcp/v1/tools/invoke", response_model=McpToolResponse, tags=["mcp"])
    def invoke_tool(payload: McpToolRequest) -> McpToolResponse:
        return _invoke(tool_registry, payload)

    return app


def _invoke(registry: ToolRegistry, request: McpToolRequest) -> McpToolResponse:
    started = time.perf_counter()
    token = set_correlation_id(str(request.correlation_id))

    try:
        _log_invocation("request", request)

        if not _customer_context_valid(request):
            return _finish(
                request,
                started,
                status=McpStatus.UNAUTHORIZED,
                code="invalid_customer_context",
                message="customerContext is missing required fields or failed validation",
            )

        tool = registry.get(request.tool_name)
        if tool is None:
            return _finish(
                request,
                started,
                status=McpStatus.UNAVAILABLE,
                code="tool_unavailable",
                message=f"Tool not registered: {request.tool_name}",
            )

        try:
            data = tool.run(request.parameters, request.customer_context)
        except ValidationError as exc:
            return _finish(
                request,
                started,
                status=McpStatus.ERROR,
                code="invalid_parameters",
                message=str(exc.errors()),
            )
        except Exception as exc:  # noqa: BLE001 — boundary converts to structured MCP error
            logger.exception("MCP tool execution failed: %s", request.tool_name)
            return _finish(
                request,
                started,
                status=McpStatus.ERROR,
                code="tool_execution_error",
                message=str(exc),
                retryable=True,
            )

        response = McpToolResponse(
            toolName=request.tool_name,
            correlationId=request.correlation_id,
            status=McpStatus.SUCCESS,
            data=data,
            error=None,
            executedAt=utc_now(),
            executionTimeMs=int((time.perf_counter() - started) * 1000),
        )
        _log_invocation("response", response)
        return response
    finally:
        reset_correlation_id(token)


def _finish(
    request: McpToolRequest,
    started: float,
    *,
    status: McpStatus,
    code: str,
    message: str,
    retryable: bool = False,
) -> McpToolResponse:
    response = McpToolResponse(
        toolName=request.tool_name,
        correlationId=request.correlation_id,
        status=status,
        data=None,
        error=McpError(code=code, message=message, retryable=retryable),
        executedAt=utc_now(),
        executionTimeMs=int((time.perf_counter() - started) * 1000),
    )
    _log_invocation("response", response)
    return response


def _customer_context_valid(request: McpToolRequest) -> bool:
    ctx = request.customer_context
    return bool(ctx.customer_id and ctx.session_id and ctx.auth_token)


def _log_invocation(kind: str, payload: McpToolRequest | McpToolResponse) -> None:
    body = payload.model_dump(mode="json", by_alias=True)
    masked = mask_sensitive_data(json.dumps(body, default=str))
    logger.info(
        "mcp_%s tool=%s correlation_id=%s payload=%s",
        kind,
        payload.tool_name,
        payload.correlation_id,
        masked,
    )


app = create_mcp_app()
