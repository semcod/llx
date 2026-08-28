"""Code editing MCP tools: aider integration."""

import hashlib
import subprocess
from pathlib import Path

from mcp.types import Tool

from llx.mcp.tools.approval import approval_response, resolve_workspace_path
from llx.mcp.tools.base import McpTool

_MAX_OUTPUT_CHARS = 50_000
_MAX_FILES = 100


def _bounded_output(value: str) -> tuple[str, bool]:
    truncated = len(value) > _MAX_OUTPUT_CHARS
    return (value[:_MAX_OUTPUT_CHARS] if truncated else value), truncated


def _aider_payload(
    path: Path,
    *,
    prompt: str,
    model: str,
    files: list[str],
    use_docker: bool,
) -> dict:
    return {
        "path": str(path),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "model": model,
        "files": files,
        "use_docker": use_docker,
    }


async def _handle_aider(args: dict) -> dict:
    """Plan an aider edit; execution requires operator and actor-bound approval."""
    try:
        path = resolve_workspace_path(".", str(args.get("path", ".")), must_exist=True)
        if not path.is_dir():
            return {"success": False, "error": f"Project path is not a directory: {path}"}
        prompt = str(args.get("prompt", ""))
        if not prompt.strip():
            return {"success": False, "error": "prompt is required"}
        if len(prompt) > 20_000:
            return {"success": False, "error": "prompt exceeds 20000 characters"}
        model = str(args.get("model", "ollama/qwen2.5-coder:7b"))
        raw_files = list(args.get("files", []))
        if len(raw_files) > _MAX_FILES:
            return {"success": False, "error": f"files exceeds maximum of {_MAX_FILES}"}
        files = [str(resolve_workspace_path(str(item), str(path))) for item in raw_files]
        use_docker = bool(args.get("use_docker", False))
    except (TypeError, ValueError) as exc:
        return {"success": False, "error": str(exc)}

    approval = approval_response(
        "aider",
        _aider_payload(path, prompt=prompt, model=model, files=files, use_docker=use_docker),
        actor=str(args.get("actor") or ""),
        supplied_hash=str(args.get("approval_hash") or ""),
    )
    if not bool(args.get("apply", False)) or approval["requires_approval"]:
        return {
            "success": False,
            "status": "approval_required",
            **approval,
            "message": (
                "Enable LLX_MCP_ALLOW_WRITE=1 and repeat with apply=true, actor, and the "
                "exact approval_hash."
            ),
        }

    if use_docker:
        # Docker-based aider execution
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{path.resolve()}:/workspace",
            "-w",
            "/workspace",
        ]
        cmd.extend(
            [
                "wronai/aider",
                "--model",
                model,
                "--message",
                prompt,
            ]
        )
        if files:
            cmd.extend(str(Path(file).relative_to(path)) for file in files)
    else:
        # Local aider execution
        cmd = ["aider", "--model", model, "--message", prompt]
        if files:
            cmd.extend(files)

    command_summary = [part if part != prompt else "<prompt:redacted>" for part in cmd]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(path) if not use_docker else None,
        )

        stdout, stdout_truncated = _bounded_output(result.stdout)
        stderr, stderr_truncated = _bounded_output(result.stderr)
        return {
            "success": result.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "command": " ".join(command_summary),
            **approval,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 300s",
            "command": " ".join(command_summary),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "command": " ".join(command_summary)}


tool_aider = McpTool(
    definition=Tool(
        name="aider",
        description=(
            "Plan an aider AI pair programming code edit. Execution requires operator capability "
            "and actor-bound approval; works with local models or Docker."
        ),
        inputSchema={
            "type": "object",
            "required": ["prompt"],
            "properties": {
                "prompt": {"type": "string", "description": "The prompt/instruction for aider"},
                "path": {"type": "string", "default": ".", "description": "Project directory path"},
                "model": {
                    "type": "string",
                    "default": "ollama/qwen2.5-coder:7b",
                    "description": "Model to use (Ollama format)",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific files to edit (optional)",
                },
                "use_docker": {
                    "type": "boolean",
                    "default": False,
                    "description": "Use Docker instead of local installation",
                },
                "apply": {
                    "type": "boolean",
                    "default": False,
                    "description": "Execute the approved edit",
                },
                "actor": {"type": "string", "description": "Approver identity"},
                "approval_hash": {"type": "string", "description": "Exact approval hash"},
            },
        },
    ),
    handler=_handle_aider,
)
