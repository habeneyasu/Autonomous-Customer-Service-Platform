"""Map MCP tools to OpenAI function-calling schemas."""

from __future__ import annotations

from typing import Any

from mcp.tools import DEFAULT_TOOLS

# Minimal JSON Schema per tool — keep flat and explicit for the prototype.
_PARAMETERS: dict[str, dict[str, Any]] = {
    "search_knowledge_base": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "searchType": {
                "type": "string",
                "enum": ["SEMANTIC", "KEYWORD", "HYBRID"],
            },
            "maxResults": {"type": "integer"},
            "minRelevanceScore": {"type": "number"},
        },
        "required": ["query"],
    },
    "get_account_balance": {"type": "object", "properties": {}},
    "get_transaction_history": {
        "type": "object",
        "properties": {
            "limit": {"type": "integer"},
            "offset": {"type": "integer"},
        },
    },
    "freeze_account": {
        "type": "object",
        "properties": {
            "accountId": {"type": "string"},
            "otpCode": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["accountId", "otpCode"],
    },
    "execute_p2p_transfer": {
        "type": "object",
        "properties": {
            "senderAccountId": {"type": "string"},
            "receiverAccountId": {"type": "string"},
            "amount": {"type": "string"},
            "currency": {"type": "string"},
            "otpCode": {"type": "string"},
        },
        "required": ["senderAccountId", "receiverAccountId", "amount", "otpCode"],
    },
}


def openai_tools_for(allowed: frozenset[str] | set[str]) -> list[dict[str, Any]]:
    """Build OpenAI tool defs for the intent-scoped MCP catalogue."""
    tools: list[dict[str, Any]] = []
    for tool in DEFAULT_TOOLS:
        if tool.name not in allowed:
            continue
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": _PARAMETERS.get(
                        tool.name, {"type": "object", "properties": {}}
                    ),
                },
            }
        )
    return tools
