"""Intent-scoped MCP tool manifests."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "mcp" / "manifests" / "tool_permissions.yaml"


@lru_cache
def load_tool_permissions() -> dict[str, frozenset[str]]:
    raw = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8")) or {}
    return {intent: frozenset(tools or []) for intent, tools in raw.items()}


def tools_for_intent(intent: str) -> frozenset[str]:
    permissions = load_tool_permissions()
    if intent not in permissions:
        raise KeyError(f"Unknown intent: {intent}")
    return permissions[intent]
