"""Base types and dataclasses for planfile executor."""

from dataclasses import dataclass
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def map_to_ticket_status(result_status: str, file_changed: bool = False) -> str:
    """Map TaskResult execution status to planfile TicketStatus.

    Workflow mapping:
    - success + file_changed -> done (completed with modifications)
    - success + !file_changed -> done (verified no changes needed)
    - no_changes -> canceled (ticket obsolete, issue not found)
    - failed -> blocked (technical error, retry possible)
    - invalid -> open (unclear response, needs re-execution)
    - not_found -> canceled (issue doesn't exist)
    - already_fixed -> done (previously resolved)
    - dry_run -> open (not yet executed)
    - skipped -> open (not yet executed)
    """
    status_map = {
        "success": "done",
        "no_changes": "canceled",
        "failed": "blocked",
        "invalid": "open",
        "not_found": "canceled",
        "already_fixed": "done",
        "dry_run": "open",
        "skipped": "open",
    }
    return status_map.get(result_status, "open")


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
    status: str  # "success" | "failed" | "skipped" | "dry_run" | "invalid" | "not_found" | "already_fixed" | "no_changes"
    model_used: str
    response: str
    error: Optional[str] = None
    execution_time: Optional[float] = None
    file_changed: bool = False
    validation_message: Optional[str] = None
