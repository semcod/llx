"""Proxym integration MCP tools."""

from mcp.types import Tool

from llx.mcp.tools.base import McpTool


async def _handle_llx_proxy_status(args: dict) -> dict:
    """Get LiteLLM proxy health and metrics."""
    from llx.config import LlxConfig
    import httpx

    config = LlxConfig.load(args.get("path", "."))
    url = args.get("url", config.litellm_base_url)

    try:
        resp = httpx.get(f"{url}/health", timeout=10)
        return {
            "healthy": resp.status_code == 200,
            "status_code": resp.status_code,
            "url": url,
        }
    except Exception as e:
        return {"healthy": False, "error": str(e), "url": url}


tool_llx_proxy_status = McpTool(
    definition=Tool(
        name="llx_proxy_status",
        description="Check LiteLLM proxy health status.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "url": {"type": "string", "description": "Override proxy URL"},
            },
        },
    ),
    handler=_handle_llx_proxy_status,
)


async def _handle_llx_proxym_status(args: dict) -> dict:
    """Get detailed proxym proxy status."""
    from llx.integrations.proxym import ProxymClient
    from llx.config import LlxConfig
    config = LlxConfig.load(args.get("path", "."))
    url = args.get("url", config.litellm_base_url)
    client = ProxymClient(config, base_url=url)
    try:
        status = client.status()
        result = {
            "available": status.available,
            "url": status.url,
        }
        if status.available:
            result["version"] = status.version
            result["models_count"] = status.models_count
            if status.providers:
                result["providers"] = status.providers
            if status.daily_remaining is not None:
                result["daily_remaining_usd"] = status.daily_remaining
            if status.monthly_remaining is not None:
                result["monthly_remaining_usd"] = status.monthly_remaining
        else:
            result["error"] = status.error
        return result
    finally:
        client.close()


tool_llx_proxym_status = McpTool(
    definition=Tool(
        name="llx_proxym_status",
        description="Get detailed status of proxym intelligent AI proxy: availability, version, model count, providers, and budget remaining.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "url": {"type": "string", "description": "Proxym URL to check"},
            },
        },
    ),
    handler=_handle_llx_proxym_status,
)


async def _handle_llx_proxym_chat(args: dict) -> dict:
    """Analyze project + route through proxym with metrics headers."""
    from llx.integrations.proxym import ProxymClient

    path = args.get("path", ".")
    prompt = args["prompt"]

    client = ProxymClient()
    try:
        response = client.chat_with_analysis(
            prompt,
            project_path=path,
            toon_dir=args.get("toon_dir"),
            task_hint=args.get("task"),
            model=args.get("model"),
        )
        return {
            "model": response.model,
            "content": response.content,
            "usage": response.usage,
        }
    finally:
        client.close()


tool_llx_proxym_chat = McpTool(
    definition=Tool(
        name="llx_proxym_chat",
        description="Analyze project metrics, select optimal tier, and route through proxym with code-metrics-aware headers for intelligent model selection.",
        inputSchema={
            "type": "object",
            "required": ["prompt"],
            "properties": {
                "prompt": {"type": "string", "description": "The prompt to send"},
                "path": {"type": "string", "default": "."},
                "toon_dir": {"type": "string"},
                "task": {"type": "string", "enum": ["refactor", "explain", "quick_fix", "review"]},
                "model": {"type": "string", "description": "Override model selection"},
            },
        },
    ),
    handler=_handle_llx_proxym_chat,
)
