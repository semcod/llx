"""Base types and dataclasses for planfile executor."""

from dataclasses import dataclass
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class BackendType:
    """Available backend types for code editing."""
    LOCAL = "local"          # Local aider package
    DOCKER = "docker"        # Docker container
    MCP = "mcp"              # MCP server
    CURSOR = "cursor"        # Cursor AI
    WINDSURF = "windsurf"    # Windsurf AI
    CLAUDE_CODE = "claude_code"  # Claude Code
    LLM_CHAT = "llm_chat"    # LLM chat (fallback)


@dataclass
class TaskResult:
    """Result of executing a task."""
    ticket_id: Optional[str]
    task_name: str
    status: str  # "success" | "failed" | "skipped" | "dry_run" | "invalid" | "not_found" | "already_fixed" | "cancelled"
    model_used: str
    response: str
    error: Optional[str] = None
    execution_time: Optional[float] = None
    file_changed: bool = False
    validation_message: Optional[str] = None
