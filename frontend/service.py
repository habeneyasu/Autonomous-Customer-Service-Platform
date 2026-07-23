"""Shared chat service for the ACSP customer-care web UI."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import httpx

from orchestrator.llm import KnowledgeScriptProvider
from orchestrator.loop import run_tool_loop
from shared.config.settings import get_settings
from shared.schemas.mcp import CustomerContext

INTENTS = [
    {"label": "Auto-detect", "value": "Auto"},
    {"label": "General inquiry", "value": "GENERAL_INQUIRY"},
    {"label": "Balance inquiry", "value": "BALANCE_INQUIRY"},
    {"label": "Transaction history", "value": "TRANSACTION_HISTORY"},
    {"label": "Fund transfer", "value": "FUND_TRANSFER"},
    {"label": "Account management", "value": "ACCOUNT_MANAGEMENT"},
]

EXAMPLES = [
    {"label": "Branch hours", "prompt": "What are your branch hours?"},
    {"label": "OTP requirements", "prompt": "Is OTP required for a wallet transfer?"},
    {"label": "Transfer limits", "prompt": "What are the wallet transfer limits?"},
    {"label": "Contact support", "prompt": "How can I contact customer support?"},
]

WELCOME = (
    "Welcome. I’m your ACSP Customer Care assistant.\n\n"
    "I can help with branch hours, wallet limits, OTP requirements, "
    "and support channels. Replies are retrieved through secured enterprise "
    "tools — not generated from unverified model memory.\n\n"
    "How can I help you today?"
)

_TOOL_LABELS = {
    "search_knowledge_base": "Knowledge Base",
    "get_account_balance": "Account Balance",
    "get_transaction_history": "Transaction History",
    "freeze_account": "Account Freeze",
    "execute_p2p_transfer": "P2P Transfer",
}


def _context(session_id: str | None = None) -> CustomerContext:
    return CustomerContext(
        customerId="demo-customer",
        sessionId=session_id or f"web-{uuid4().hex[:10]}",
        authToken="demo-token",
        authenticatedAt=datetime.now(timezone.utc),
        channelType="WEB_CHAT",
    )


def intent_value(label: str) -> str | None:
    for item in INTENTS:
        if item["label"] == label or item["value"] == label:
            return None if item["value"] == "Auto" else item["value"]
    return None


def mcp_health() -> dict:
    url = get_settings().mcp_server_url.rstrip("/")
    try:
        ok = httpx.get(f"{url}/health", timeout=1.5).status_code == 200
    except httpx.HTTPError:
        ok = False
    return {
        "ok": ok,
        "url": url,
        "label": "Secure tools online" if ok else "Secure tools offline",
    }


def _status_of(item) -> str:
    return item.status.value if hasattr(item.status, "value") else str(item.status)


def _format_trace(result) -> str:
    tools = ", ".join(f"{i.tool_name}:{_status_of(i)}" for i in result.tool_results) or "none"
    return (
        f"intent          {result.intent}\n"
        f"tools           {tools}\n"
        f"rounds          {result.rounds}\n"
        f"correlation_id  {result.correlation_id}\n"
        f"session_id      {result.session_id}"
    )


def _status_line(result) -> str:
    if not result.tool_results:
        return "Response completed. No enterprise tool was required for this turn."
    if any(_status_of(i) != "SUCCESS" for i in result.tool_results):
        return "We could not complete a required tool call. Please try again or start a new session."
    names = ", ".join(i.tool_name for i in result.tool_results)
    return f"Verified via enterprise tools: {names}."


def _tool_via(result) -> str | None:
    ok = [i for i in result.tool_results if _status_of(i) == "SUCCESS"]
    if not ok:
        return None
    for item in ok:
        if item.tool_name == "search_knowledge_base" and isinstance(item.data, dict):
            results = item.data.get("results") or []
            title = str((results[0] or {}).get("title") or "").strip() if results else ""
            if title:
                return title
    first = ok[0].tool_name
    return _TOOL_LABELS.get(first, first.replace("_", " ").title())


def _resolve_llm(mode: str):
    if mode.startswith("Demo") or mode == "demo":
        return KnowledgeScriptProvider()
    if not get_settings().llm_api_key:
        raise ValueError(
            "Live assistant requires LLM_API_KEY in .env. "
            "Switch to Demo mode, or add your key and restart."
        )
    return None


def create_session() -> dict:
    ctx = _context()
    return {
        "session_id": ctx.session_id,
        "welcome": WELCOME,
        "status": "New session started.",
        "trace": (
            "intent          -\n"
            "tools           none\n"
            "rounds          0\n"
            "correlation_id  -\n"
            f"session_id      {ctx.session_id}"
        ),
        "health": mcp_health(),
        "examples": EXAMPLES,
        "intents": INTENTS,
    }


def chat(
    *,
    message: str,
    session_id: str,
    mode: str = "Demo replies (offline)",
    intent: str = "Auto-detect",
) -> dict:
    text = (message or "").strip()
    if not text:
        raise ValueError("Message is required.")

    result = run_tool_loop(
        text,
        customer_context=_context(session_id),
        intent=intent_value(intent),
        llm=_resolve_llm(mode),
    )
    return {
        "reply": result.reply,
        "status": _status_line(result),
        "trace": _format_trace(result),
        "session_id": result.session_id,
        "intent": result.intent,
        "via": _tool_via(result),
    }
