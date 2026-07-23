"""LLM ↔ MCP tool-calling loop.

Flow: tokenize → LLM proposes tools → rehydrate → McpClient.invoke → LLM reply.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from orchestrator.intent import infer_intent
from orchestrator.llm import LlmProvider, LlmTurn, OpenAICompatibleProvider, ToolCall
from orchestrator.tools import openai_tools_for
from security.tokenizer import Tokenizer, get_tokenizer
from shared.config.settings import get_settings
from shared.schemas.mcp import CustomerContext, McpToolResponse
from worker.mcp_client import McpClient

_SYSTEM = (
    "You are a bank and wallet customer-service assistant.\n"
    "Use MCP tools for any factual claim about policy, balances, history, or transfers.\n"
    "Never invent account data or policy. If a tool returns no useful data, say so.\n"
    "Never mention tool names or internal systems to the customer.\n"
    "Keep answers concise and in plain language."
)


@dataclass
class AgentResult:
    reply: str
    intent: str
    correlation_id: UUID
    session_id: str
    tool_results: list[McpToolResponse] = field(default_factory=list)
    rounds: int = 0


def run_tool_loop(
    user_message: str,
    *,
    customer_context: CustomerContext,
    intent: str | None = None,
    correlation_id: UUID | None = None,
    llm: LlmProvider | None = None,
    tokenizer: Tokenizer | None = None,
    max_rounds: int | None = None,
) -> AgentResult:
    """Run one agent turn with MCP as the only enterprise tool boundary."""
    settings = get_settings()
    resolved_intent = intent or infer_intent(user_message)
    cid = correlation_id or uuid4()
    tok = tokenizer or get_tokenizer()
    provider = llm or OpenAICompatibleProvider()
    rounds_limit = max_rounds or settings.llm_max_tool_rounds

    tokenized = tok.tokenize(
        user_message,
        session_id=customer_context.session_id,
    )
    client = McpClient.for_intent(resolved_intent)
    tools = openai_tools_for(client.allowed_tools)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": tokenized.tokenized_text},
    ]
    tool_results: list[McpToolResponse] = []

    for round_idx in range(1, rounds_limit + 1):
        turn = provider.complete(messages, tools=tools or None)
        if not turn.tool_calls:
            return AgentResult(
                reply=(turn.content or "").strip() or "How can I help you today?",
                intent=resolved_intent,
                correlation_id=cid,
                session_id=tokenized.session_id,
                tool_results=tool_results,
                rounds=round_idx,
            )

        messages.append(assistant_tool_message(turn))
        for call in turn.tool_calls:
            result = _execute_tool_call(
                call,
                client=client,
                tokenizer=tok,
                session_id=tokenized.session_id,
                customer_context=customer_context,
                correlation_id=cid,
            )
            tool_results.append(result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(
                        result.model_dump(mode="json", by_alias=True),
                        default=str,
                    ),
                }
            )

    return AgentResult(
        reply="I wasn't able to finish that request. Please try again.",
        intent=resolved_intent,
        correlation_id=cid,
        session_id=tokenized.session_id,
        tool_results=tool_results,
        rounds=rounds_limit,
    )


def _execute_tool_call(
    call: ToolCall,
    *,
    client: McpClient,
    tokenizer: Tokenizer,
    session_id: str,
    customer_context: CustomerContext,
    correlation_id: UUID,
) -> McpToolResponse:
    parameters = tokenizer.rehydrate_mapping(
        call.arguments,
        session_id=session_id,
        allow_secrets=False,
    )
    return client.invoke(
        call.name,
        parameters,
        customer_context=customer_context,
        correlation_id=correlation_id,
    )


def assistant_tool_message(turn: LlmTurn) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": turn.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments),
                },
            }
            for call in turn.tool_calls
        ],
    }
