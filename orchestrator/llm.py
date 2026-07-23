"""OpenAI-compatible LLM provider for tool calling."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from shared.config.settings import get_settings


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LlmTurn:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LlmProvider(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LlmTurn:
        ...


class OpenAICompatibleProvider:
    """Chat Completions client (OpenAI, Azure OpenAI, Ollama-compatible, etc.)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.llm_api_key
        self._base_url = (base_url or settings.llm_base_url).rstrip("/")
        self._model = model or settings.llm_model
        self._timeout = timeout_seconds or settings.llm_timeout_seconds
        if not self._api_key:
            raise ValueError("LLM_API_KEY is required")

    def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LlmTurn:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            payload = response.json()

        message = payload["choices"][0]["message"]
        tool_calls: list[ToolCall] = []
        for item in message.get("tool_calls") or []:
            raw_args = item["function"].get("arguments") or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError:
                arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            tool_calls.append(
                ToolCall(
                    id=item["id"],
                    name=item["function"]["name"],
                    arguments=arguments,
                )
            )
        return LlmTurn(content=message.get("content"), tool_calls=tool_calls)


class ScriptedProvider:
    """Deterministic provider for tests and offline demos."""

    def __init__(self, turns: list[LlmTurn]) -> None:
        self._turns = list(turns)
        self._index = 0

    def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LlmTurn:
        _ = messages, tools
        if self._index >= len(self._turns):
            return LlmTurn(content="I couldn't complete that request.")
        turn = self._turns[self._index]
        self._index += 1
        return turn


class KnowledgeScriptProvider:
    """Offline knowledge demo: call search_knowledge_base, then answer from MCP data."""

    def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LlmTurn:
        _ = tools
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        if not tool_msgs:
            user = next(
                (m.get("content") or "" for m in reversed(messages) if m.get("role") == "user"),
                "customer question",
            )
            return LlmTurn(
                tool_calls=[
                    ToolCall(
                        id="call_kb_1",
                        name="search_knowledge_base",
                        arguments={
                            "query": user,
                            "searchType": "HYBRID",
                            "maxResults": 3,
                            "minRelevanceScore": 0.1,
                        },
                    )
                ]
            )

        try:
            payload = json.loads(tool_msgs[-1].get("content") or "{}")
        except json.JSONDecodeError:
            payload = {}

        status = payload.get("status")
        data = payload.get("data") or {}
        results = data.get("results") or []
        if status != "SUCCESS" or not results:
            return LlmTurn(
                content=(
                    "I couldn't find verified information for that in our knowledge base. "
                    "Please rephrase the question, or ask to speak with a human agent."
                )
            )

        top = results[0]
        title = str(top.get("title") or "our policies").strip()
        excerpt = _clean_excerpt(str(top.get("excerpt") or ""))
        if not excerpt:
            reply = (
                f"I found a verified policy section on “{title}”. "
                "Please ask a more specific question if you need more detail."
            )
        else:
            reply = excerpt

        if len(results) > 1:
            related = ", ".join(
                str(item.get("title") or "Related topic") for item in results[1:3]
            )
            reply += f"\n\nRelated help topics: {related}."
        return LlmTurn(content=reply)


def _clean_excerpt(text: str) -> str:
    """Turn markdown policy snippets into plain customer-facing sentences."""
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = line.lstrip("-*• ").strip()
        line = line.replace("**", "").replace("*", "").replace("`", "")
        if line:
            lines.append(line.rstrip("."))
    if not lines:
        return ""
    body = ". ".join(lines).strip()
    if body and not body.endswith("."):
        body += "."
    return body
