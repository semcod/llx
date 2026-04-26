"""Simplified executor for LLX planfile integration.

This module is a backward-compatible facade. All implementations have been
split into submodules in llx.planfile.executor.*
"""

from llx.planfile.executor import backends as _backends

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

# Backward compatibility for legacy patch targets such as
# llx.planfile.executor_simple.subprocess.run used in tests and integrations.
subprocess = _backends.subprocess

__all__ = [
    "BackendType",
    "TaskResult",
    "execute_strategy",
    "_detect_available_backends",
    "_discover_mcp_services",
    "_select_best_backend",
    "_run_cursor_edit",
    "_run_windsurf_edit",
    "_run_claude_code_edit",
    "_load_strategy",
    "_save_strategy",
    "_normalize_strategy",
    "_execute_task",
    "_build_task_prompt",
    "_select_model",
    "_parse_llm_response",
    "_map_action_to_task_type",
    "_map_priority",
]

# Backward compatibility: all implementations re-exported from executor submodules
