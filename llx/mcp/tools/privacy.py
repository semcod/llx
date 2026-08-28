"""Privacy MCP tools: anonymization, deanonymization, scanning."""

from pathlib import Path
from typing import Any

from mcp.types import Tool

from llx.mcp.tools.approval import (
    MCP_SECRET_ENV,
    approval_response,
    content_manifest_sha256,
    resolve_workspace_path,
    secret_output_enabled,
)
from llx.mcp.tools.base import McpTool

_MAX_FILE_SIZE = 50 * 1024 * 1024
_MAX_TEXT_CHARS = 50_000


async def _handle_llx_project_anonymize(args: dict) -> dict:
    """Preview project anonymization; writing requires exact output approval."""
    from llx.privacy.project import ProjectAnonymizer, AnonymizationContext

    try:
        path = Path(args.get("path", ".")).expanduser().resolve()
        if not path.is_dir():
            return {"success": False, "error": f"Project path is not a directory: {path}"}
        raw_output = str(args.get("output_dir") or ".llx/anonymized")
        output_dir = resolve_workspace_path(raw_output, str(path))
        include = list(args.get("include") or ["*.py", "*.js", "*.ts", "*.java", "*.go"])
        exclude = list(args.get("exclude") or [])
        max_file_size = max(1, min(int(args.get("max_file_size", 10 * 1024 * 1024)), _MAX_FILE_SIZE))
    except (TypeError, ValueError) as exc:
        return {"success": False, "error": str(exc)}

    ctx = AnonymizationContext(project_path=path)
    result = ProjectAnonymizer(ctx).anonymize_project(
        include_patterns=include,
        exclude_patterns=exclude,
        max_file_size=max_file_size,
    )
    approval = approval_response(
        "llx_project_anonymize",
        {
            "project_path": str(path),
            "output_dir": str(output_dir),
            "output_manifest_sha256": content_manifest_sha256(result.files),
            "files": len(result.files),
        },
        actor=str(args.get("actor") or ""),
        supplied_hash=str(args.get("approval_hash") or ""),
    )
    dry_run = bool(args.get("dry_run", True))
    if not dry_run and approval["requires_approval"]:
        return {
            "success": False,
            "status": "approval_required",
            **approval,
        }

    context_file = output_dir / ".anonymization_context.json"
    if not dry_run:
        for relative, content in result.files.items():
            target = resolve_workspace_path(relative, str(output_dir))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        context_file.parent.mkdir(parents=True, exist_ok=True)
        ctx.save(context_file)

    return {
        "success": True,
        "dry_run": dry_run,
        "files_anonymized": len(result.files),
        "output_dir": str(output_dir),
        "context_file": str(context_file),
        "symbols_replaced": sum(ctx.stats.values()),
        "errors": result.errors[:100],
        **approval,
    }


tool_llx_project_anonymize = McpTool(
    definition=Tool(
        name="llx_project_anonymize",
        description=(
            "Preview project anonymization. Writing the anonymized copy and mapping requires "
            "operator capability and exact output approval."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "default": ".",
                    "description": "Project path to anonymize",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for anonymized files (temp if not specified)",
                },
                "include": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File patterns to include",
                    "default": ["*.py", "*.js", "*.ts", "*.java", "*.go"],
                },
                "exclude": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File patterns to exclude",
                },
                "max_file_size": {
                    "type": "integer",
                    "description": "Max file size in bytes",
                    "default": 10485760,
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Analyze without writing output files",
                },
                "actor": {"type": "string", "description": "Approver identity"},
                "approval_hash": {"type": "string", "description": "Exact approval hash"},
            },
        },
    ),
    handler=_handle_llx_project_anonymize,
)


async def _handle_llx_project_deanonymize(args: dict) -> dict:
    """Deanonymize project files or LLM response using saved context."""
    from llx.privacy.deanonymize import ProjectDeanonymizer
    from llx.privacy.project import AnonymizationContext

    context_path = args.get("context_path")
    if not context_path:
        return {"error": "context_path is required (path to .anonymization_context.json)"}
    if not secret_output_enabled():
        return {
            "success": False,
            "error": "Secret output is disabled for MCP deanonymization.",
            "required_env": MCP_SECRET_ENV,
        }

    # Load context
    try:
        ctx = AnonymizationContext.load(context_path)
    except Exception as e:
        return {"error": f"Failed to load context: {str(e)}"}

    deanonymizer = ProjectDeanonymizer(ctx)

    # Handle text input (LLM response)
    if "text" in args:
        text = str(args["text"])
        if len(text) > _MAX_TEXT_CHARS:
            return {"success": False, "error": f"text exceeds {_MAX_TEXT_CHARS} characters"}
        result = deanonymizer.deanonymize_text(text)
        return {
            "success": True,
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

    try:
        project_root = Path(ctx.project_path).expanduser().resolve()
        input_path = resolve_workspace_path(str(input_dir), str(project_root), must_exist=True)
        if not input_path.is_dir():
            return {"success": False, "error": f"input_dir is not a directory: {input_path}"}
        output_path = resolve_workspace_path(
            str(output_dir or ".llx/deanonymized"),
            str(project_root),
        )
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

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
        output_dir=None,
    )
    approval = approval_response(
        "llx_project_deanonymize",
        {
            "project_path": str(project_root),
            "input_dir": str(input_path),
            "output_dir": str(output_path),
            "output_manifest_sha256": content_manifest_sha256(result.files),
            "files": len(result.files),
        },
        actor=str(args.get("actor") or ""),
        supplied_hash=str(args.get("approval_hash") or ""),
    )
    dry_run = bool(args.get("dry_run", True))
    if not dry_run and approval["requires_approval"]:
        return {
            "success": False,
            "status": "approval_required",
            **approval,
        }
    if not dry_run:
        for relative, content in result.files.items():
            target = resolve_workspace_path(relative, str(output_path))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "dry_run": dry_run,
        "files_restored": len(result.files),
        "output_dir": str(output_path),
        "overall_confidence": result.overall_confidence,
        "restorations_by_file": result.restorations,
        "unknown_tokens_count": sum(len(v) for v in result.unknowns.values()),
        **approval,
    }


tool_llx_project_deanonymize = McpTool(
    definition=Tool(
        name="llx_project_deanonymize",
        description="Deanonymize project files or LLM response using saved context from anonymization. Restores original symbol names, paths, and sensitive data.",
        inputSchema={
            "type": "object",
            "required": ["context_path"],
            "properties": {
                "context_path": {
                    "type": "string",
                    "description": "Path to .anonymization_context.json file",
                },
                "text": {
                    "type": "string",
                    "description": "LLM response text to deanonymize (alternative to input_dir)",
                },
                "input_dir": {
                    "type": "string",
                    "description": "Directory with anonymized files to restore",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for restored files",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Analyze restorations without writing files",
                },
                "actor": {"type": "string", "description": "Approver identity"},
                "approval_hash": {"type": "string", "description": "Exact approval hash"},
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

    include_values = bool(args.get("include_sensitive_values", False)) and secret_output_enabled()
    result: dict[str, Any] = {
        "scan": {
            "total_findings": sum(len(v) for v in findings.values()),
            "patterns_found": list(findings.keys()),
            "details": findings if include_values else {key: len(values) for key, values in findings.items()},
            "sensitive_values_included": include_values,
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
        if include_values and anon_result.mapping:
            result["anonymized"]["sample_mapping"] = dict(
                list(anon_result.mapping.items())[:5]
            )

    return result


tool_llx_privacy_scan = McpTool(
    definition=Tool(
        name="llx_privacy_scan",
        description=(
            "Scan text or files for sensitive data and optionally anonymize. Sensitive values "
            "are redacted unless the server explicitly enables secret output."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text content to scan"},
                "path": {
                    "type": "string",
                    "description": "File path to scan (alternative to text)",
                },
                "anonymize": {
                    "type": "boolean",
                    "description": "Also return anonymized version",
                    "default": False,
                },
                "include_sensitive_values": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Return exact matches only when LLX_MCP_ALLOW_SECRET_OUTPUT=1"
                    ),
                },
            },
        },
    ),
    handler=_handle_llx_privacy_scan,
)
