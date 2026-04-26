"""Base types for MCP tools."""

from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from mcp.types import Tool


@dataclass
class McpTool:
    definition: Tool
    handler: Callable[[dict], Coroutine[Any, Any, dict]]
