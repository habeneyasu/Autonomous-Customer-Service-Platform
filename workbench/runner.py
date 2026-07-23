"""Instrumented ACSP runs that produce a 4-zone workbench snapshot."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from mcp.tools import DEFAULT_TOOLS
from orchestrator.intent import infer_intent
from orchestrator.llm import KnowledgeScriptProvider, LlmProvider, LlmTurn, ScriptedProvider, ToolCall
from orchestrator.loop import assistant_tool_message
from orchestrator.tools import openai_tools_for
from security.tokenizer import get_tokenizer
from shared.config.settings import get_settings
from shared.schemas.mcp import CustomerContext, McpStatus, McpToolResponse
from worker.manifest import tools_for_intent
from worker.mcp_client import McpClient
from workbench.models import ToolCard, TraceStep, WorkbenchSnapshot

_WRITE_TOOLS = frozenset({"execute_p2p_transfer", "freeze_account"})
_CATALOGUE = frozenset(tool.name for tool in DEFAULT_TOOLS)
_SYSTEM = (
    "You are a bank and wallet customer-service assistant. "
    "Use MCP tools for factual claims. Never invent account data or policy."
)


class _Clock:
    def __init__(self) -> None:
        self._t0 = time.perf_counter()

    def ms(self) -> int:
        return int((time.perf_counter() - self._t0) * 1000)


def _endpoint() -> str:
    return f"POST {get_settings().mcp_server_url.rstrip('/')}/mcp/v1/tools/invoke"


def _context(session_id: str) -> CustomerContext:
    return CustomerContext(
        customerId="demo-customer",
        sessionId=session_id,
        authToken="demo-token",
        authenticatedAt=datetime.now(timezone.utc),
        channelType="WEB_CHAT",
    )


def _step(timeline: list[TraceStep], clock: _Clock, label: str, detail: str = "", kind: str = "info") -> None:
    timeline.append(TraceStep(clock.ms(), label, detail, kind))


def _status(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _card(
    *,
    name: str,
    llm_params: dict[str, Any],
    rehydrated: dict[str, Any],
    result: McpToolResponse,
    blocked: bool = False,
) -> ToolCard:
    err = result.error
    status = _status(result.status)
    return ToolCard(
        tool_name=name,
        endpoint=_endpoint(),
        llm_parameters=llm_params,
        rehydrated_parameters=rehydrated,
        status=status,
        error_code=err.code if err else None,
        error_message=err.message if err else None,
        blocked=blocked or status == McpStatus.UNAUTHORIZED.value,
    )


def run_observed_turn(
    message: str,
    *,
    scenario: str,
    intent: str | None = None,
    llm: LlmProvider | None = None,
    force_tool: str | None = None,
    otp_listening: bool = False,
    max_rounds: int = 4,
) -> WorkbenchSnapshot:
    clock = _Clock()
    timeline: list[TraceStep] = []
    tokenizer = get_tokenizer()
    correlation_id = uuid4()
    tool_cards: list[ToolCard] = []
    reply = ""
    saw_write = False

    _step(timeline, clock, "Gateway Ingress (HTTP 202)", "Accepted customer message", "ok")
    tokenized = tokenizer.tokenize(message)
    ctx = _context(tokenized.session_id)
    _step(
        timeline,
        clock,
        "Tokenized PII & Vaulted Session",
        f"session={tokenized.session_id}; tokens={len(tokenized.tokens)}",
        "ok",
    )

    resolved = intent or infer_intent(message)
    allowed = sorted(tools_for_intent(resolved))
    blocked = sorted(_CATALOGUE - set(allowed))
    _step(timeline, clock, "Intent Classified → Loaded Manifest", f"{resolved} → {allowed}", "ok")

    if force_tool:
        reply = _run_abuse(
            clock, timeline, tool_cards, force_tool, allowed, tokenizer, tokenized.session_id, ctx, correlation_id, resolved
        )
    else:
        provider = llm or _provider(resolved, tokenized.tokenized_text)
        client = McpClient.for_intent(resolved)
        tools = openai_tools_for(client.allowed_tools)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": tokenized.tokenized_text},
        ]

        for _ in range(max_rounds):
            turn = provider.complete(messages, tools=tools or None)
            if not turn.tool_calls:
                reply = (turn.content or "").strip() or "How can I help you today?"
                break

            _step(timeline, clock, "LLM Proposed Tool Call", ", ".join(c.name for c in turn.tool_calls), "ok")
            messages.append(assistant_tool_message(turn))

            for call in turn.tool_calls:
                llm_params = dict(call.arguments)
                rehydrated = tokenizer.rehydrate_mapping(
                    llm_params, session_id=tokenized.session_id, allow_secrets=False
                )
                if call.name in _WRITE_TOOLS:
                    saw_write = True
                    _step(timeline, clock, "State Change Detected → OTP Challenge", "OTP Gate LISTENING", "otp")
                _step(timeline, clock, "MCP Client Rehydrated & Invoked :8001", f"tool={call.name}", "ok")
                result = client.invoke(
                    call.name, rehydrated, customer_context=ctx, correlation_id=correlation_id
                )
                tool_cards.append(
                    _card(name=call.name, llm_params=llm_params, rehydrated=rehydrated, result=result)
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result.model_dump(mode="json", by_alias=True), default=str),
                    }
                )

            if saw_write:
                _step(timeline, clock, "MCP Executed Write Path", "Write tool reached MCP boundary", "ok")
        else:
            reply = reply or "I wasn't able to finish that request. Please try again."

        _step(timeline, clock, "Audit Event Emitted", f"correlationId={correlation_id}; tools={len(tool_cards)}", "ok")

    otp_on = otp_listening or saw_write
    host = get_settings().mcp_server_url.rstrip("/")
    return WorkbenchSnapshot(
        scenario=scenario,
        customer_id=ctx.customer_id,
        correlation_id=str(correlation_id),
        session_id=tokenized.session_id,
        modes={
            "Ingress Tokenization": "ACTIVE",
            "MCP Protocol Boundary": f"ENFORCED ({host})",
            "OTP Gate": "LISTENING" if otp_on else "IDLE",
        },
        raw_message=message,
        tokenized_message=tokenized.tokenized_text,
        token_map=dict(tokenized.tokens),
        intent=resolved,
        allowed_tools=allowed,
        blocked_tools=blocked,
        tool_cards=tool_cards,
        timeline=timeline,
        reply=reply,
        otp_listening=otp_on,
    )


def _run_abuse(
    clock: _Clock,
    timeline: list[TraceStep],
    tool_cards: list[ToolCard],
    force_tool: str,
    allowed: list[str],
    tokenizer: Any,
    session_id: str,
    ctx: CustomerContext,
    correlation_id: UUID,
    intent: str,
) -> str:
    _step(timeline, clock, "LLM Proposed Tool Call", f"Proposed {force_tool} (abuse simulation)", "warn")
    llm_params = {"reason": "simulated prompt-injection tool abuse"}
    rehydrated = tokenizer.rehydrate_mapping(llm_params, session_id=session_id, allow_secrets=False)
    _step(timeline, clock, "MCP Client Rehydrated & Invoked :8001", f"Manifest check for {force_tool}", "warn")
    result = McpClient.for_intent(intent).invoke(
        force_tool, rehydrated, customer_context=ctx, correlation_id=correlation_id
    )
    tool_cards.append(
        _card(name=force_tool, llm_params=llm_params, rehydrated=rehydrated, result=result, blocked=True)
    )
    detail = (result.error.message if result.error else f"Tool '{force_tool}' not permitted in {intent} manifest.")
    _step(timeline, clock, "Manifest Gate Blocked Tool", detail, "block")
    _step(timeline, clock, "Audit Event Emitted", f"correlationId={correlation_id}", "ok")
    if force_tool not in allowed:
        return f"UNAUTHORIZED: Tool '{force_tool}' not permitted in {intent} manifest."
    return f"Tool '{force_tool}' returned {_status(result.status)}."


def _provider(intent: str, tokenized_text: str) -> LlmProvider:
    if intent == "BALANCE_INQUIRY":
        return ScriptedProvider(
            [
                LlmTurn(tool_calls=[ToolCall(id="call_bal", name="get_account_balance", arguments={})]),
                LlmTurn(content="Here is your verified balance from the account tool."),
            ]
        )
    if intent == "FUND_TRANSFER":
        return ScriptedProvider(
            [
                LlmTurn(
                    tool_calls=[
                        ToolCall(
                            id="call_xfer",
                            name="execute_p2p_transfer",
                            arguments={
                                "senderAccountId": "00000000-0000-0000-0000-000000000001",
                                "receiverAccountId": "00000000-0000-0000-0000-000000000002",
                                "amount": "500",
                                "currency": "ETB",
                                "otpCode": "[REDACTED_OTP]",
                                "context": tokenized_text,
                            },
                        )
                    ]
                ),
                LlmTurn(
                    content=(
                        "Transfer is blocked until the OTP gate verifies a real code. "
                        "Raw OTP never enters the LLM context."
                    )
                ),
            ]
        )
    return KnowledgeScriptProvider()
