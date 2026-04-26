"""Code analysis MCP tools: code2llm, redup, vallm."""

from pathlib import Path
from mcp.types import Tool

from llx.mcp.tools.base import McpTool


async def _handle_code2llm_analyze(args: dict) -> dict:
    """Run code2llm analysis on project."""
    from llx.analysis.runner import run_code2llm
    path = Path(args.get("path", "."))
    output_dir = Path(args.get("output_dir", str(path / ".llx" / "code2llm")))
    result = run_code2llm(path, output_dir, format=args.get("format", "json"))
    return {
        "success": result.success,
        "output_dir": str(result.output_dir),
        "files_analyzed": result.files_analyzed,
        "error": result.error,
    }


tool_code2llm_analyze = McpTool(
    definition=Tool(
        name="code2llm_analyze",
        description="Run code2llm to analyze code structure and complexity (cyclomatic complexity, maintainability, god modules, duplication).",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "output_dir": {"type": "string"},
                "format": {"type": "string", "enum": ["json", "yaml", "toon"], "default": "json"},
            },
        },
    ),
    handler=_handle_code2llm_analyze,
)


async def _handle_redup_scan(args: dict) -> dict:
    """Run redup to detect code duplication."""
    from llx.analysis.runner import run_redup
    path = Path(args.get("path", "."))
    output_dir = Path(args.get("output_dir", str(path / ".llx" / "redup")))
    result = run_redup(path, output_dir, format=args.get("format", "json"))
    return {
        "success": result.success,
        "output_dir": str(result.output_dir),
        "duplicates_found": result.duplicates_found if hasattr(result, "duplicates_found") else None,
        "error": result.error,
    }


tool_redup_scan = McpTool(
    definition=Tool(
        name="redup_scan",
        description="Run redup to detect code duplication across the project (syntax-aware clone detection).",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "output_dir": {"type": "string"},
                "format": {"type": "string", "enum": ["json", "yaml", "toon"], "default": "json"},
            },
        },
    ),
    handler=_handle_redup_scan,
)


async def _handle_vallm_validate(args: dict) -> dict:
    """Run vallm validation on code or project."""
    if "code" in args:
        # Single-file validation via Python API
        try:
            from vallm import Proposal, validate
            proposal = Proposal(code=args["code"], language=args.get("language", "python"))
            result = validate(proposal)
            return {
                "verdict": result.verdict.value,
                "score": result.weighted_score,
                "issues": [{"message": i.message, "severity": i.severity} for i in result.issues],
            }
        except ImportError:
            return {"error": "vallm package not installed. pip install llx[vallm]"}
    else:
        # Batch project validation via CLI
        from llx.analysis.runner import run_vallm
        path = Path(args.get("path", "."))
        output_dir = Path(args.get("output_dir", str(path / ".llx" / "vallm")))
        result = run_vallm(path, output_dir)
        return {"success": result.success, "output_dir": str(result.output_dir), "error": result.error}


tool_vallm_validate = McpTool(
    definition=Tool(
        name="vallm_validate",
        description="Validate code quality. Either pass 'code' for single-file validation (syntax, imports, complexity, security) or 'path' for batch project validation.",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code to validate (single-file mode)"},
                "language": {"type": "string", "default": "python"},
                "path": {"type": "string", "description": "Project path for batch validation"},
                "output_dir": {"type": "string"},
            },
        },
    ),
    handler=_handle_vallm_validate,
)
