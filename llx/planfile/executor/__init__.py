"""Simplified executor for LLX planfile integration.

This module provides a facade for backward compatibility.
All implementations have been split into submodules:
    - base: Core types and dataclasses
    - backends: Backend detection and IDE runners
    - strategy: Strategy loading, normalization, and execution
    - task: Task execution and model selection
"""

from llx.planfile.executor.base import BackendType, TaskResult
from llx.planfile.executor.backends import (
    _detect_available_backends,
    _discover_mcp_services,
    _select_best_backend,
    _run_cursor_edit,
    _run_windsurf_edit,
    _run_claude_code_edit,
)
from llx.planfile.executor.strategy import (
    _load_strategy,
    _save_strategy,
    _normalize_strategy,
    execute_strategy,
)
from llx.planfile.executor.task import (
    _execute_task,
    _build_task_prompt,
    _select_model,
    _parse_llm_response,
    _map_action_to_task_type,
    _map_priority,
)

__all__ = [
    # Base types
    "BackendType",
    "TaskResult",
    # Backend functions
    "_detect_available_backends",
    "_discover_mcp_services",
    "_select_best_backend",
    "_run_cursor_edit",
    "_run_windsurf_edit",
    "_run_claude_code_edit",
    # Strategy functions
    "_load_strategy",
    "_save_strategy",
    "_normalize_strategy",
    "execute_strategy",
    # Task functions
    "_execute_task",
    "_build_task_prompt",
    "_select_model",
    "_parse_llm_response",
    "_map_action_to_task_type",
    "_map_priority",
]
