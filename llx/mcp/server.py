"""llx MCP Server — orchestrates code2llm, redup, vallm as MCP tools.

Start:
    python -m llx.mcp                  # stdio mode (for Claude Desktop)
    python -m llx.mcp --sse            # SSE mode on /sse and /messages/
    python -m llx.mcp --sse --port 8000

Claude Desktop config:
    {
      "mcpServers": {
        "llx": {
          "command": "python3",
          "args": ["-m", "llx.mcp"]
        }
      }
    }
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from llx.mcp.tools import MCP_TOOLS

server = Server("llx")

TOOLS = MCP_TOOLS

_TOOL_HANDLERS = {tool.definition.name: tool.handler for tool in TOOLS}

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [t.definition for t in TOOLS]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = _TOOL_HANDLERS.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    result = await handler(arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def run_stdio_server() -> None:
    """Run the MCP server over stdio for desktop clients."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def create_app() -> Any:
    """Create an ASGI app that exposes the MCP server over SSE."""
    try:
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        from mcp.server.sse import SseServerTransport
    except ImportError as exc:  # pragma: no cover - dependency error
        raise RuntimeError(
            "SSE mode requires the MCP runtime dependencies. Install llx with the 'mcp' extra "
            "or install mcp, starlette, sse-starlette, and uvicorn."
        ) from exc

    transport = SseServerTransport("/messages/")

    async def handle_sse(request: Any) -> Response:
        async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )
        return Response()

    async def handle_post_message(scope: Any, receive: Any, send: Any) -> None:
        await transport.handle_post_message(scope, receive, send)

    return Starlette(
        routes=[
            Route("/sse", handle_sse, methods=["GET"]),
            Mount("/messages/", app=handle_post_message),
        ]
    )


def run_sse_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the MCP server over SSE for web clients."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - dependency error
        raise RuntimeError(
            "SSE mode requires uvicorn. Install llx with the 'mcp' extra or install uvicorn."
        ) from exc

    uvicorn.run(create_app(), host=host, port=port, log_level="info")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the MCP server."""
    parser = argparse.ArgumentParser(description="Run the llx MCP server.")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Expose the MCP server over SSE at /sse and /messages/.",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("LLX_MCP_HOST", "0.0.0.0"),
        help="Host interface to bind to in SSE mode.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("LLX_MCP_PORT", "8000")),
        help="Port to listen on in SSE mode.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the llx MCP server."""
    args = build_parser().parse_args(argv)
    if args.sse:
        run_sse_server(host=args.host, port=args.port)
    else:
        asyncio.run(run_stdio_server())
    return 0

def main_sync(argv: list[str] | None = None):
    """Synchronous entry point for CLI."""
    return main(argv)

if __name__ == "__main__":
    raise SystemExit(main())
