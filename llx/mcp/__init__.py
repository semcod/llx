"""MCP server for llx — exposes all wronai tools as MCP endpoints.

Submodules:
    server   — MCP stdio/SSE server with tool dispatch
    service  — Persistent SSE service with /health and /metrics
    client   — Async MCP SSE client for calling llx tools
    tools    — MCP tool definitions and handlers
"""

from llx.mcp.client import LlxMcpClient
from llx.mcp.service import McpServiceState, create_service_app, run_service

__all__ = [
    "LlxMcpClient",
    "McpServiceState",
    "create_service_app",
    "run_service",
]
