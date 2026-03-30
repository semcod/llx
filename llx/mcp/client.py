"""MCP SSE client for calling llx tools programmatically.

Upstreamed from pyqual — provides a thin async client that connects to an
llx MCP SSE endpoint and calls tools by name.
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from typing import Any

DEFAULT_ENDPOINT = "http://localhost:8000/sse"


class LlxMcpClient:
    """Thin MCP client for the llx SSE service."""

    def __init__(self, endpoint_url: str | None = None):
        self.endpoint_url = (
            endpoint_url
            or os.getenv("LLX_MCP_URL")
            or os.getenv("PYQUAL_LLX_MCP_URL")
            or DEFAULT_ENDPOINT
        )

    @asynccontextmanager
    async def _session(self):
        try:
            from mcp.client.session import ClientSession
            from mcp.client.sse import sse_client
        except ImportError as exc:
            raise RuntimeError(
                "mcp client is required. Install with: pip install llx[mcp]"
            ) from exc

        async with sse_client(self.endpoint_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                yield session

    @staticmethod
    def _extract_text_payload(result: Any) -> tuple[str, Any]:
        """Return the concatenated text and parsed JSON payload if possible."""
        text_parts: list[str] = []
        content = getattr(result, "content", []) or []
        for item in content:
            text = getattr(item, "text", None)
            if text:
                text_parts.append(text)

        combined = "\n".join(text_parts).strip()
        if not combined:
            return "", None

        try:
            return combined, json.loads(combined)
        except json.JSONDecodeError:
            return combined, combined

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call a named MCP tool and return a JSON-friendly payload."""
        async with self._session() as session:
            result = await session.call_tool(name, arguments or {})

        text, parsed = self._extract_text_payload(result)
        is_error = bool(getattr(result, "isError", False))
        return {
            "tool": name,
            "arguments": arguments or {},
            "is_error": is_error,
            "text": text,
            "data": parsed,
            "raw": result.model_dump(mode="json", by_alias=True, exclude_none=True),
        }

    async def analyze(self, project_path: str, toon_dir: str | None = None, task: str = "quick_fix") -> dict[str, Any]:
        """Run llx analysis and return the parsed payload."""
        payload = {"path": project_path, "task": task}
        if toon_dir:
            payload["toon_dir"] = toon_dir
        return await self.call_tool("llx_analyze", payload)

    async def fix_with_aider(
        self,
        project_path: str,
        prompt: str,
        model: str | None = None,
        files: list[str] | None = None,
        use_docker: bool = False,
        docker_args: list[str] | None = None,
    ) -> dict[str, Any]:
        """Invoke the llx `aider` tool with a prepared prompt."""
        payload: dict[str, Any] = {
            "path": project_path,
            "prompt": prompt,
            "use_docker": use_docker,
        }
        if model:
            payload["model"] = model
        if files:
            payload["files"] = files
        if docker_args:
            payload["docker_args"] = docker_args
        return await self.call_tool("aider", payload)
