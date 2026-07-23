"""Worker MCP client — sole outbound path to enterprise tools."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from shared.config.settings import get_settings
from shared.schemas.mcp import (
    CustomerContext,
    McpError,
    McpStatus,
    McpToolRequest,
    McpToolResponse,
)
from shared.utils.datetime import utc_now
from worker.manifest import tools_for_intent


class McpClient:
    """Policy-aware HTTP client for the MCP server.

    Responsibilities:
    - enforce intent tool manifest
    - enforce per-workflow invocation budget
    - inject immutable customerContext on every call
    """

    def __init__(
        self,
        allowed_tools: frozenset[str] | set[str],
        *,
        base_url: str | None = None,
        max_invocations: int | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.mcp_server_url).rstrip("/")
        self._allowed_tools = frozenset(allowed_tools)
        self._max_invocations = (
            max_invocations
            if max_invocations is not None
            else settings.mcp_max_invocations
        )
        self._timeout = timeout_seconds
        self._invocations = 0

    @classmethod
    def for_intent(cls, intent: str, **kwargs: Any) -> McpClient:
        return cls(tools_for_intent(intent), **kwargs)

    @property
    def allowed_tools(self) -> frozenset[str]:
        return self._allowed_tools

    @property
    def invocation_count(self) -> int:
        return self._invocations

    def invoke(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
        *,
        customer_context: CustomerContext,
        correlation_id: UUID,
    ) -> McpToolResponse:
        if tool_name not in self._allowed_tools:
            return _denied(
                tool_name,
                correlation_id,
                status=McpStatus.UNAUTHORIZED,
                code="tool_not_in_manifest",
                message=f"Tool '{tool_name}' is not allowed for this workflow",
            )

        if self._invocations >= self._max_invocations:
            return _denied(
                tool_name,
                correlation_id,
                status=McpStatus.UNAUTHORIZED,
                code="invocation_limit_exceeded",
                message=f"Maximum MCP invocations ({self._max_invocations}) exceeded",
            )

        self._invocations += 1
        request = McpToolRequest(
            toolName=tool_name,
            correlationId=correlation_id,
            customerContext=customer_context,
            parameters=parameters or {},
            requestedAt=utc_now(),
        )

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    f"{self._base_url}/mcp/v1/tools/invoke",
                    json=request.model_dump(mode="json", by_alias=True),
                )
                response.raise_for_status()
                return McpToolResponse.model_validate(response.json())
        except httpx.HTTPError as exc:
            return _denied(
                tool_name,
                correlation_id,
                status=McpStatus.ERROR,
                code="mcp_transport_error",
                message=str(exc),
                retryable=True,
            )


def _denied(
    tool_name: str,
    correlation_id: UUID,
    *,
    status: McpStatus,
    code: str,
    message: str,
    retryable: bool = False,
) -> McpToolResponse:
    return McpToolResponse(
        toolName=tool_name,
        correlationId=correlation_id,
        status=status,
        data=None,
        error=McpError(code=code, message=message, retryable=retryable),
        executedAt=utc_now(),
        executionTimeMs=0,
    )
