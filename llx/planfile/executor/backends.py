"""Backend detection and IDE runner functions."""

from pathlib import Path
from typing import Any
import logging
import subprocess

from llx.planfile.executor.base import BackendType

logger = logging.getLogger(__name__)


def _detect_available_backends() -> dict[str, bool]:
    """Detect which backends are available.

    Returns:
        Dict mapping backend types to availability status.
    """
    backends = {
        BackendType.LOCAL: False,
        BackendType.DOCKER: False,
        BackendType.MCP: False,
        BackendType.CURSOR: False,
        BackendType.WINDSURF: False,
        BackendType.CLAUDE_CODE: False,
        BackendType.LLM_CHAT: True,  # Always available as fallback
    }

    # Check local aider
    try:
        subprocess.run(
            ["aider", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
        backends[BackendType.LOCAL] = True
        logger.info("Local aider is available")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.info("Local aider not available")

    # Check Docker
    try:
        subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
        backends[BackendType.DOCKER] = True
        logger.info("Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.info("Docker not available")

    # Check MCP server (check if llx mcp can connect)
    try:
        # Try to check MCP status
        subprocess.run(
            ["llx", "mcp", "status"],
            capture_output=True,
            check=False,
            timeout=10
        )
        # If command exists, assume MCP is available
        backends[BackendType.MCP] = True
        logger.info("MCP is available")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.info("MCP not available")

    # Skip Cursor, Windsurf, Claude Code detection - they are IDEs, not CLI code editors
    # These tools don't have programmatic code editing CLI interfaces
    logger.info("Skipping IDE detection (Cursor, Windsurf, Claude Code are IDEs, not CLI editors)")

    return backends


def _discover_mcp_services() -> dict[str, dict]:
    """Discover available MCP services.

    Returns:
        Dict mapping service names to their metadata.
    """
    services = {}

    # Try to get MCP server list from llx
    try:
        result = subprocess.run(
            ["llx", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Parse the output to extract services
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    services[line.strip()] = {
                        "type": "mcp_service",
                        "available": True
                    }
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check for common MCP servers in the project
    mcp_config_paths = [
        Path.cwd() / ".mcp.json",
        Path.cwd() / "mcp.json",
        Path.cwd() / ".mcp" / "config.json",
    ]

    for config_path in mcp_config_paths:
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    import json
                    config = json.load(f)
                    if "mcpServers" in config:
                        for name, server_config in config["mcpServers"].items():
                            services[name] = {
                                "type": "mcp_service",
                                "config": server_config,
                                "available": True
                            }
            except Exception as e:
                logger.error(f"Failed to read MCP config from {config_path}: {e}")

    return services


def _select_best_backend(backends: dict[str, bool]) -> str:
    """Select the best available backend.

    Priority: LOCAL > DOCKER > MCP > LLM_CHAT

    Returns:
        Selected backend type.
    """
    # Priority order: Local aider first, then Docker, then MCP, then fallback
    if backends.get(BackendType.LOCAL):
        return BackendType.LOCAL
    if backends.get(BackendType.DOCKER):
        return BackendType.DOCKER
    if backends.get(BackendType.MCP):
        return BackendType.MCP
    return BackendType.LLM_CHAT


def _run_cursor_edit(
    workdir: Path,
    prompt: str,
    model: str,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Run Cursor AI for code editing."""
    cmd = ["cursor", "edit", "--message", prompt]
    if files:
        cmd.extend(files)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Cursor command timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error running Cursor: {str(e)}",
        }


def _run_windsurf_edit(
    workdir: Path,
    prompt: str,
    model: str,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Run Windsurf AI for code editing."""
    cmd = ["windsurf", "edit", "--message", prompt]
    if files:
        cmd.extend(files)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Windsurf command timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error running Windsurf: {str(e)}",
        }


def _run_claude_code_edit(
    workdir: Path,
    prompt: str,
    model: str,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Run Claude Code for code editing."""
    cmd = ["claude", "edit", "--message", prompt]
    if files:
        cmd.extend(files)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Claude Code command timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error running Claude Code: {str(e)}",
        }
