"""llx MCP Server — orchestrates code2llm, redup, vallm as MCP tools.

Start:
    python -m llx.mcp.server          # stdio mode (for Claude Desktop)
    python -m llx.mcp.server --sse    # SSE mode (for web clients)

Claude Desktop config:
    {
      "mcpServers": {
        "llx": {
          "command": "python3",
          "args": ["-m", "llx.mcp.server"]
        }
      }
    }
"""

import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent

from llx.mcp.tools import (
    tool_llx_analyze,
    tool_llx_select,
    tool_llx_chat,
    tool_code2llm_analyze,
    tool_redup_scan,
    tool_vallm_validate,
    tool_llx_proxy_status,
)

server = Server("llx")

TOOLS = [
    tool_llx_analyze,
    tool_llx_select,
    tool_llx_chat,
    tool_code2llm_analyze,
    tool_redup_scan,
    tool_vallm_validate,
    tool_llx_proxy_status,
]

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [t.definition for t in TOOLS]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = {t.definition.name: t.handler for t in TOOLS}.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    result = await handler(arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

def main_sync():
    """Synchronous entry point for CLI."""
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()
