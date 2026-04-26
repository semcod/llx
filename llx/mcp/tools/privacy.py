"""Privacy MCP tools: anonymization, deanonymization, scanning."""

from pathlib import Path
from typing import Any
from mcp.types import Tool

from llx.mcp.tools.base import McpTool


async def _handle_llx_project_anonymize(args: dict) -> dict:
    """Anonymize entire project for secure LLM processing."""
    from llx.privacy.project import ProjectAnonymizer, AnonymizationContext
    from pathlib import Path

    path = Path(args.get("path", "."))
    output_dir = args.get("output_dir")
    include = args.get("include", ["*.py", "*.js", "*.ts", "*.java", "*.go"])
    exclude = args.get("exclude", [])
    max_file_size = args.get("max_file_size", 10 * 1024 * 1024)

    ctx = AnonymizationContext()
    anonymizer = ProjectAnonymizer(ctx)

    # Collect all files
    files_to_anonymize: dict[str, str] = {}
    for pattern in include:
        for file_path in path.rglob(pattern):
            if file_path.is_file() and file_path.stat().st_size <= max_file_size:
                # Check exclude patterns
                excluded = False
                for excl in exclude:
                    if file_path.match(excl):
                        excluded = True
                        break
                if excluded:
                    continue

                try:
                    relative = str(file_path.relative_to(path))
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    files_to_anonymize[relative] = content
                except Exception:
                    continue

    # Anonymize all files
    result = anonymizer.anonymize_project(
        files_to_anonymize,
        output_dir=output_dir,
    )

    # Save context for later deanonymization
    ctx.save()

    return {
        "success": True,
        "files_anonymized": len(result.files),
        "output_dir": output_dir or str(path / "anonymized"),
        "context_file": str(ctx.context_path),
        "symbols_replaced": len(ctx.mapping),
        "paths_anonymized": len(ctx.path_mapping),
    }


tool_llx_project_anonymize = McpTool(
    definition=Tool(
        name="llx_project_anonymize",
        description="Anonymize entire project: AST symbols (variables, functions, classes), file paths, and sensitive data. Creates anonymized copy with mapping file for later deanonymization.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": ".", "description": "Project path to anonymize"},
                "output_dir": {"type": "string", "description": "Output directory for anonymized files (temp if not specified)"},
                "include": {"type": "array", "items": {"type": "string"}, "description": "File patterns to include", "default": ["*.py", "*.js", "*.ts", "*.java", "*.go"]},
                "exclude": {"type": "array", "items": {"type": "string"}, "description": "File patterns to exclude"},
                "max_file_size": {"type": "integer", "description": "Max file size in bytes", "default": 10485760},
            },
        },
    ),
    handler=_handle_llx_project_anonymize,
)


async def _handle_llx_project_deanonymize(args: dict) -> dict:
    """Deanonymize project files or LLM response using saved context."""
    from llx.privacy.deanonymize import ProjectDeanonymizer
    from llx.privacy.project import AnonymizationContext
    from pathlib import Path

    context_path = args.get("context_path")
    if not context_path:
        return {"error": "context_path is required (path to .anonymization_context.json)"}

    # Load context
    try:
        ctx = AnonymizationContext.load(context_path)
    except Exception as e:
        return {"error": f"Failed to load context: {str(e)}"}

    deanonymizer = ProjectDeanonymizer(ctx)

    # Handle text input (LLM response)
    if "text" in args:
        text = args["text"]
        result = deanonymizer.deanonymize_text(text)
        return {
            "deanonymized_text": result.text,
            "restorations": len(result.restorations),
            "unknown_tokens": result.unknown_tokens[:10],
            "confidence": result.confidence,
        }

    # Handle files
    input_dir = args.get("input_dir")
    output_dir = args.get("output_dir")

    if not input_dir:
        return {"error": "Either text or input_dir must be provided"}

    input_path = Path(input_dir)

    # Collect all files
    files_to_deanonymize: dict[str, str] = {}
    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.name != ".anonymization_context.json":
            try:
                relative = str(file_path.relative_to(input_path))
                content = file_path.read_text(encoding="utf-8", errors="replace")
                files_to_deanonymize[relative] = content
            except Exception:
                continue

    # Deanonymize all files
    result = deanonymizer.deanonymize_project_files(
        files_to_deanonymize,
        output_dir=output_dir,
    )

    return {
        "success": True,
        "files_restored": len(result.files),
        "output_dir": output_dir,
        "overall_confidence": result.overall_confidence,
        "restorations_by_file": result.restorations,
        "unknown_tokens_count": sum(len(v) for v in result.unknowns.values()),
    }


tool_llx_project_deanonymize = McpTool(
    definition=Tool(
        name="llx_project_deanonymize",
        description="Deanonymize project files or LLM response using saved context from anonymization. Restores original symbol names, paths, and sensitive data.",
        inputSchema={
            "type": "object",
            "required": ["context_path"],
            "properties": {
                "context_path": {"type": "string", "description": "Path to .anonymization_context.json file"},
                "text": {"type": "string", "description": "LLM response text to deanonymize (alternative to input_dir)"},
                "input_dir": {"type": "string", "description": "Directory with anonymized files to restore"},
                "output_dir": {"type": "string", "description": "Output directory for restored files"},
            },
        },
    ),
    handler=_handle_llx_project_deanonymize,
)


async def _handle_llx_privacy_scan(args: dict) -> dict:
    """Scan text or files for sensitive data and optionally anonymize."""
    from llx.privacy import Anonymizer

    text = args.get("text", "")
    path = args.get("path")
    anonymize = args.get("anonymize", False)

    # Read from file if path provided
    if path and not text:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    if not text:
        return {"error": "No text or path provided"}

    anon = Anonymizer()

    # Scan for sensitive data
    findings = anon.scan(text)

    result: dict[str, Any] = {
        "scan": {
            "total_findings": sum(len(v) for v in findings.values()),
            "patterns_found": list(findings.keys()),
            "details": findings,
        }
    }

    # Anonymize if requested
    if anonymize:
        anon_result = anon.anonymize(text)
        result["anonymized"] = {
            "text": anon_result.text,
            "mapping_count": len(anon_result.mapping),
            "stats": anon_result.stats,
        }
        # Show sample of original values (truncated)
        sample = {}
        for token, original in list(anon_result.mapping.items())[:5]:
            sample[token] = original[:50] + "..." if len(original) > 50 else original
        if anon_result.mapping:
            result["anonymized"]["sample_mapping"] = sample

    return result


tool_llx_privacy_scan = McpTool(
    definition=Tool(
        name="llx_privacy_scan",
        description="Scan text or files for sensitive data (API keys, passwords, emails, etc.) and optionally anonymize. Returns findings and anonymized text with token mapping.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text content to scan"},
                "path": {"type": "string", "description": "File path to scan (alternative to text)"},
                "anonymize": {"type": "boolean", "description": "Also return anonymized version", "default": False},
            },
        },
    ),
    handler=_handle_llx_privacy_scan,
)
