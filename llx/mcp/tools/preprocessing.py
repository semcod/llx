"""Preprocessing MCP tools: llx_preprocess, llx_context."""

from mcp.types import Tool

from llx.mcp.tools.base import McpTool


async def _handle_llx_preprocess(args: dict) -> dict:
    """Preprocess a query using preLLM's small→large LLM pipeline."""
    from llx.prellm.core import preprocess_and_execute

    query = args["query"]
    small_llm = args.get("small_llm", "ollama/qwen2.5:3b")
    large_llm = args.get("large_llm", "gpt-5.4-mini")
    strategy = args.get("strategy", "auto")
    execute = args.get("execute", False)

    result = await preprocess_and_execute(
        query=query,
        small_llm=small_llm,
        large_llm=large_llm,
        strategy=strategy,
        skip_execution=not execute,
    )

    output = {
        "content": result.content,
        "model_used": result.model_used,
        "small_model_used": result.small_model_used,
    }
    if result.decomposition:
        output["decomposition"] = {
            "strategy": result.decomposition.strategy.value,
            "composed_prompt": result.decomposition.composed_prompt,
            "sub_queries": result.decomposition.sub_queries,
            "matched_rule": result.decomposition.matched_rule,
        }
        if result.decomposition.classification:
            output["decomposition"]["classification"] = {
                "intent": result.decomposition.classification.intent,
                "confidence": result.decomposition.classification.confidence,
                "domain": result.decomposition.classification.domain,
            }
    return output


tool_llx_preprocess = McpTool(
    definition=Tool(
        name="llx_preprocess",
        description="Preprocess a query using preLLM's two-agent pipeline: small LLM classifies/decomposes the query, optionally large LLM executes it. Returns decomposition details and optional response.",
        inputSchema={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "description": "The query to preprocess"},
                "small_llm": {"type": "string", "default": "ollama/qwen2.5:3b"},
                "large_llm": {"type": "string", "default": "gpt-5.4-mini"},
                "strategy": {"type": "string", "enum": ["auto", "decompose", "direct"], "default": "auto"},
                "execute": {"type": "boolean", "default": False, "description": "Also execute with large LLM"},
            },
        },
    ),
    handler=_handle_llx_preprocess,
)


async def _handle_llx_context(args: dict) -> dict:
    """Gather project context for LLM queries."""
    from llx.prellm.context.codebase_indexer import CodebaseIndexer
    from llx.prellm.context.shell_collector import ShellCollector
    from llx.prellm.context.sensitive_filter import SensitiveFilter

    path = args.get("path", ".")
    include_shell = args.get("include_shell", True)
    include_codebase = args.get("include_codebase", True)

    context_parts = []

    if include_shell:
        shell = ShellCollector()
        shell_context = shell.collect()
        if shell_context:
            context_parts.append("## Shell Context\n" + shell_context)

    if include_codebase:
        indexer = CodebaseIndexer(root_path=path)
        summary = indexer.get_project_summary()
        context_parts.append(f"## Codebase Summary\n{summary}")

    # Filter sensitive data
    combined = "\n\n".join(context_parts)
    sensitive_filter = SensitiveFilter()
    filtered = sensitive_filter.filter(combined)

    return {
        "context": filtered.text,
        "sensitive_findings": filtered.findings,
        "sources": ["shell" if include_shell else None, "codebase" if include_codebase else None],
    }


tool_llx_context = McpTool(
    definition=Tool(
        name="llx_context",
        description="Gather project context for LLM queries: shell history, codebase summary, sensitive data filtering.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "include_shell": {"type": "boolean", "default": True},
                "include_codebase": {"type": "boolean", "default": True},
            },
        },
    ),
    handler=_handle_llx_context,
)
