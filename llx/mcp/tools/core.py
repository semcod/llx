"""Core LLX MCP tools: analyze, select, chat."""

from mcp.types import Tool

from llx.mcp.tools.base import McpTool


async def _handle_llx_analyze(args: dict) -> dict:
    """Analyze project and recommend model."""
    from llx.analysis.collector import analyze_project
    from llx.routing.selector import select_with_context_check
    from llx.config import LlxConfig

    path = args.get("path", ".")
    toon_dir = args.get("toon_dir")
    task_hint = args.get("task")

    config = LlxConfig.load(path)
    metrics = analyze_project(path, toon_dir=toon_dir)
    result = select_with_context_check(metrics, config, task_hint=task_hint)

    return {
        "metrics": {
            "total_files": metrics.total_files,
            "total_lines": metrics.total_lines,
            "total_functions": metrics.total_functions,
            "avg_cc": metrics.avg_cc,
            "max_cc": metrics.max_cc,
            "critical_count": metrics.critical_count,
            "god_modules": metrics.god_modules,
            "max_fan_out": metrics.max_fan_out,
            "dependency_cycles": metrics.dependency_cycles,
            "task_scope": metrics.task_scope,
        },
        "selection": {
            "tier": result.tier.value,
            "model_id": result.model_id,
            "reasons": result.reasons,
        },
    }


tool_llx_analyze = McpTool(
    definition=Tool(
        name="llx_analyze",
        description="Analyze a project and recommend the optimal LLM model based on code metrics (files, complexity, coupling, duplication).",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path to analyze", "default": "."},
                "toon_dir": {"type": "string", "description": "Directory with .toon analysis files (optional)"},
                "task": {"type": "string", "enum": ["refactor", "explain", "quick_fix", "review"], "description": "Task hint for model selection"},
            },
        },
    ),
    handler=_handle_llx_analyze,
)


async def _handle_llx_select(args: dict) -> dict:
    """Quick model selection."""
    from llx.analysis.collector import analyze_project
    from llx.routing.selector import select_model
    from llx.config import LlxConfig

    path = args.get("path", ".")
    config = LlxConfig.load(path)
    metrics = analyze_project(path, toon_dir=args.get("toon_dir"))
    result = select_model(metrics, config, task_hint=args.get("task"))
    return {"tier": result.tier.value, "model_id": result.model_id, "reasons": result.reasons}


tool_llx_select = McpTool(
    definition=Tool(
        name="llx_select",
        description="Quick model selection from existing analysis files. Returns tier and model_id.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "toon_dir": {"type": "string"},
                "task": {"type": "string", "enum": ["refactor", "explain", "quick_fix", "review"]},
            },
        },
    ),
    handler=_handle_llx_select,
)


async def _handle_llx_chat(args: dict) -> dict:
    """Send chat message via selected model."""
    from llx.routing.client import LlxClient, ChatMessage
    from llx.config import LlxConfig

    messages = [ChatMessage(role="user", content=args["message"])]
    config = LlxConfig.load(args.get("path", "."))
    client = LlxClient(config=config)

    response = client.chat(
        messages=messages,
        model=args.get("model"),
        temperature=args.get("temperature", 0.7),
    )

    return {
        "content": response.content,
        "model": response.model,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
        } if response.usage else None,
    }


tool_llx_chat = McpTool(
    definition=Tool(
        name="llx_chat",
        description="Send a chat message through llx's model router with automatic model selection based on context.",
        inputSchema={
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {"type": "string", "description": "The message to send"},
                "path": {"type": "string", "default": ".", "description": "Project path for context-aware selection"},
                "model": {"type": "string", "description": "Override model (optional)"},
                "temperature": {"type": "number", "default": 0.7},
            },
        },
    ),
    handler=_handle_llx_chat,
)
