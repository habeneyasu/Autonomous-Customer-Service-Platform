from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from shared.schemas.mcp import CustomerContext, McpToolDescriptor


class McpTool(Protocol):
    name: str
    description: str
    state_modifying: bool
    authorized_intents: list[str]

    def run(self, parameters: dict[str, Any], customer_context: CustomerContext) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    state_modifying: bool
    authorized_intents: list[str]
    handler: Callable[[dict[str, Any], CustomerContext], dict[str, Any]]

    @classmethod
    def from_tool(cls, tool: McpTool) -> RegisteredTool:
        return cls(
            name=tool.name,
            description=tool.description,
            state_modifying=tool.state_modifying,
            authorized_intents=list(tool.authorized_intents),
            handler=tool.run,
        )

    def run(self, parameters: dict[str, Any], customer_context: CustomerContext) -> dict[str, Any]:
        return self.handler(parameters, customer_context)

    def descriptor(self) -> McpToolDescriptor:
        return McpToolDescriptor(
            name=self.name,
            description=self.description,
            stateModifying=self.state_modifying,
            authorizedIntents=list(self.authorized_intents),
        )


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, tool: McpTool | RegisteredTool) -> None:
        registered = tool if isinstance(tool, RegisteredTool) else RegisteredTool.from_tool(tool)
        if registered.name in self._tools:
            raise ValueError(f"Tool already registered: {registered.name}")
        self._tools[registered.name] = registered

    def get(self, name: str) -> RegisteredTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[McpToolDescriptor]:
        return [tool.descriptor() for tool in self._tools.values()]

    def names(self) -> list[str]:
        return sorted(self._tools)


def build_default_registry() -> ToolRegistry:
    from mcp.tools import DEFAULT_TOOLS

    registry = ToolRegistry()
    for tool in DEFAULT_TOOLS:
        registry.register(tool)
    return registry
