"""Code editing MCP tools: aider integration."""

import subprocess
import json
from pathlib import Path
from mcp.types import Tool

from llx.mcp.tools.base import McpTool


async def _handle_aider(args: dict) -> dict:
    """Run aider AI pair programming tool."""
    path = Path(args.get("path", "."))
    prompt = args.get("prompt", "")
    model = args.get("model", "ollama/qwen2.5-coder:7b")
    files = args.get("files", [])
    use_docker = args.get("use_docker", False)
    docker_args = args.get("docker_args", [])

    if use_docker:
        # Docker-based aider execution
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{path.resolve()}:/workspace",
            "-w", "/workspace",
        ]
        for arg in docker_args:
            cmd.append(arg)
        cmd.extend([
            "wronai/aider",
            "--model", model,
            "--message", prompt,
        ])
        if files:
            cmd.extend(files)
    else:
        # Local aider execution
        cmd = ["aider", "--model", model, "--message", prompt]
        if files:
            cmd.extend(files)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(path) if not use_docker else None
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 300s",
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": " ".join(cmd)
        }


tool_aider = McpTool(
    definition=Tool(
        name="aider",
        description="Run aider AI pair programming tool for code editing and refactoring. Works with local Ollama models or Docker.",
        inputSchema={
            "type": "object",
            "required": ["prompt"],
            "properties": {
                "prompt": {"type": "string", "description": "The prompt/instruction for aider"},
                "path": {"type": "string", "default": ".", "description": "Project directory path"},
                "model": {"type": "string", "default": "ollama/qwen2.5-coder:7b", "description": "Model to use (Ollama format)"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Specific files to edit (optional)"},
                "use_docker": {"type": "boolean", "default": False, "description": "Use Docker instead of local installation"},
                "docker_args": {"type": "array", "items": {"type": "string"}, "description": "Additional Docker arguments (optional)"},
            },
        },
    ),
    handler=_handle_aider,
)
