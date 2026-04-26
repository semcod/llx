"""Task execution, model selection, and prompt building."""

from pathlib import Path
from typing import Any, Optional
import logging
import time


def _map_action_to_task_type(action: str) -> str:
    """Map action string to task type."""
    action_map = {
        "fix": "fix",
        "refactor": "refactor",
        "feature": "feature",
        "test": "test",
        "docs": "docs",
        "chore": "chore",
    }
    return action_map.get(action, "feature")


def _map_priority(priority: int | str) -> str:
    """Map priority to standardized format."""
    if isinstance(priority, int):
        if priority <= 1:
            return "critical"
        elif priority <= 2:
            return "high"
        elif priority <= 3:
            return "medium"
        else:
            return "low"
    return priority if priority in ["critical", "high", "medium", "low"] else "medium"

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage
from llx.planfile.executor.base import BackendType, TaskResult
from llx.planfile.executor.backends import (
    _run_cursor_edit,
    _run_windsurf_edit,
    _run_claude_code_edit,
)
from llx.utils.aider import _run_aider_fix

logger = logging.getLogger(__name__)


def _check_indicators(text: str, indicators: list[str]) -> bool:
    """Return True if any indicator is present in text (case-insensitive)."""
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in indicators)


_NOT_FOUND_INDICATORS = [
    "issue not found",
    "problem not found",
    "no such issue",
    "cannot find",
    "could not find",
    "doesn't exist",
    "does not exist",
    "already fixed",
    "already resolved",
    "no action needed",
    "no changes needed",
    "nothing to fix",
    "not applicable",
    "already up to date",
]

_CHANGES_INDICATORS = [
    "i have modified",
    "i have changed",
    "i've updated",
    "i updated",
    "here is the modified",
    "here is the updated",
    "here is the fixed",
    "changes made",
    "file updated",
    "code changed",
    "i made the following changes",
    "here are the changes",
    "modified the",
    "refactored",
    "rewrote",
]

_FIXED_INDICATORS = [
    "issue fixed",
    "problem fixed",
    "resolved",
    "corrected",
    "fixed the",
    "has been fixed",
    "successfully fixed",
    "addressed",
    "eliminated",
]


def _extract_explanation(lines: list[str], indicators: list[str]) -> str:
    """Extract explanation context from lines where an indicator appears."""
    for i, line in enumerate(lines):
        if any(ind in line.lower() for ind in indicators):
            context_lines = [line]
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].strip() and not lines[j].startswith('```'):
                    context_lines.append(lines[j])
            return ' '.join(context_lines)
    return ""


def _build_message(issue_not_found: bool, changes_made: bool, problem_fixed: bool, explanation: str) -> str:
    """Build human-readable summary message from parsed flags."""
    if issue_not_found:
        return f"Task cancelled: {explanation}"
    if changes_made and problem_fixed:
        return "LLM reports changes made and issue fixed"
    if changes_made:
        return "LLM reports changes made"
    if problem_fixed:
        return "LLM reports issue fixed"
    return "LLM response unclear about changes"


def _parse_llm_response(response: str) -> dict:
    """Parse LLM response to extract structured information."""
    response_lower = response.lower()
    has_code_block = "```python" in response_lower

    issue_not_found = _check_indicators(response, _NOT_FOUND_INDICATORS)
    changes_made = has_code_block or _check_indicators(response, _CHANGES_INDICATORS)
    problem_fixed = _check_indicators(response, _FIXED_INDICATORS)

    detailed_explanation = ""
    if issue_not_found:
        detailed_explanation = _extract_explanation(response.split('\n'), _NOT_FOUND_INDICATORS)
        if not detailed_explanation:
            detailed_explanation = "The issue described in the ticket was not found in the codebase."

    message = _build_message(issue_not_found, changes_made, problem_fixed, detailed_explanation)

    return {
        "changes_made": changes_made,
        "problem_fixed": problem_fixed,
        "issue_not_found": issue_not_found,
        "message": message,
        "detailed_explanation": detailed_explanation
    }


def _select_model(task: dict, config: LlxConfig, metrics: Any) -> str:
    """Select appropriate model based on task and metrics."""
    # Get model hints from task
    model_hints = task.get("model_hints", {})
    preferred_tier = model_hints.get("tier", "balanced")
    
    # Map tier to model
    model_map = {
        "fast": config.models.get("fast"),
        "cheap": config.models.get("cheap"),
        "balanced": config.models.get("balanced"),
        "premium": config.models.get("premium")
    }
    
    model = model_map.get(preferred_tier, model_map.get("balanced"))
    
    if model:
        return model.model_id
    
    # Fallback to default
    default = config.models.get(config.default_tier)
    return default.model_id if default else "openai/gpt-5.4-mini"


def _build_task_prompt(task: dict, metrics: Any) -> str:
    """Build execution prompt with project context."""

    file_path = task.get("file", "")

    prompt = f"""## Task: {task.get('name', 'Unnamed Task')}

Type: {task.get('task_type', 'feature')}
Priority: {task.get('priority', 'medium')}
Target File: {file_path if file_path else 'N/A'}

Description:
{task.get('description', '')}

## Project Context
"""

    # Add metrics if available
    if hasattr(metrics, 'total_files'):
        prompt += f"- Files: {metrics.total_files}\n"
        prompt += f"- Lines of code: {metrics.total_lines:,}\n"
        prompt += f"- Average cyclomatic complexity: {metrics.avg_cc:.1f}\n"
        prompt += f"- Max complexity: {metrics.max_cc}\n"
        prompt += f"- Critical functions (CC > 10): {metrics.critical_count}\n"
    else:
        prompt += "- Metrics not available\n"

    # Add file content if file is specified
    if file_path:
        try:
            from pathlib import Path
            file_full_path = Path(file_path)
            if not file_full_path.is_absolute():
                # Assume relative to current directory
                file_full_path = Path.cwd() / file_path

            if file_full_path.exists():
                with open(file_full_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                prompt += f"""
## Current File Content

```python
{file_content}
```
"""
            else:
                prompt += f"\n## Current File Content\nFile not found: {file_path}\n"
        except Exception as e:
            prompt += f"\n## Current File Content\nError reading file: {e}\n"

    prompt += f"""
## Instructions

CRITICAL: You MUST output the complete modified file content in a code block.

For each file you modify, use this format:
```python:{file_path if file_path else 'path/to/file.py'}
# Complete file content here
```

If modifying multiple files, use separate code blocks with file paths.

Requirements:
1. Read and understand the current file content
2. Apply the necessary changes to fix the issue
3. Output the COMPLETE modified file content (not just snippets)
4. Ensure the code is syntactically correct and complete
5. Do not truncate or omit any parts of the file

If the issue does not exist or cannot be found, explicitly state: "Issue not found" or "No action needed".

Focus on practical, actionable changes that improve the codebase.
"""

    return prompt


def _run_mcp_backend(target_file: str, prompt: str, model: str) -> tuple[str, bool, str]:
    """Run MCP backend. Returns (response, changes_applied, effective_backend)."""
    try:
        from llx.mcp.client import MCPClient
        mcp_client = MCPClient()
        tool_result = mcp_client.call_tool(
            "aider_edit_file",
            {"file_path": target_file, "prompt": prompt, "model": model}
        )
        return str(tool_result), True, BackendType.MCP
    except Exception as e:
        logger.error(f"MCP editing failed: {e}")
        return "", False, BackendType.LLM_CHAT


def _run_cursor_backend(project_root: Path, prompt: str, model: str, target_file: str) -> tuple[str, bool]:
    """Run Cursor backend. Returns (response, changes_applied)."""
    result = _run_cursor_edit(workdir=project_root, prompt=prompt, model=model, files=[target_file])
    response = result.get("stdout", "") + "\n" + result.get("stderr", "")
    success = result.get("success", False)
    if not success:
        logger.error(f"Cursor failed: {result.get('stderr', 'Unknown error')}")
    return response, success


def _run_windsurf_backend(project_root: Path, prompt: str, model: str, target_file: str) -> tuple[str, bool]:
    """Run Windsurf backend. Returns (response, changes_applied)."""
    result = _run_windsurf_edit(workdir=project_root, prompt=prompt, model=model, files=[target_file])
    response = result.get("stdout", "") + "\n" + result.get("stderr", "")
    success = result.get("success", False)
    if not success:
        logger.error(f"Windsurf failed: {result.get('stderr', 'Unknown error')}")
    return response, success


def _run_claude_code_backend(project_root: Path, prompt: str, model: str, target_file: str) -> tuple[str, bool]:
    """Run Claude Code backend. Returns (response, changes_applied)."""
    result = _run_claude_code_edit(workdir=project_root, prompt=prompt, model=model, files=[target_file])
    response = result.get("stdout", "") + "\n" + result.get("stderr", "")
    success = result.get("success", False)
    if not success:
        logger.error(f"Claude Code failed: {result.get('stderr', 'Unknown error')}")
    return response, success


def _run_aider_backend(project_root: Path, prompt: str, model: str, target_file: str, use_docker: bool) -> tuple[str, bool]:
    """Run aider backend. Returns (response, changes_applied)."""
    result = _run_aider_fix(
        workdir=project_root,
        prompt=prompt,
        model=model,
        files=[target_file] if target_file else None,
        use_docker=use_docker
    )
    response = result.get("stdout", "") + "\n" + result.get("stderr", "")
    success = result.get("success", False)
    if not success:
        logger.warning(f"Aider editing failed: {result.get('stderr', 'Unknown error')}")
    return response, success


def _run_llm_chat_with_retry(prompt: str, model: str) -> str:
    """Run LLM chat with optional retry on unclear responses. Returns response content or raises Exception."""
    client = LlxClient()
    messages = [
        ChatMessage(role="system", content="You are a helpful coding assistant."),
        ChatMessage(role="user", content=prompt)
    ]
    response = client.chat(messages=messages, model=model, temperature=0.7)
    response_content = response.content

    validation = _parse_llm_response(response_content)
    unclear = not validation["issue_not_found"] and not validation["changes_made"] and not validation["problem_fixed"]
    if unclear:
        logger.warning("LLM response unclear; retrying with stricter instructions")
        strict_messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a precise coding assistant. "
                    "When you modify code you MUST wrap the full file in a ```python block. "
                    "If you make no changes, say exactly: 'No action needed'."
                )
            ),
            ChatMessage(role="user", content=prompt)
        ]
        try:
            retry_response = client.chat(messages=strict_messages, model=model, temperature=0.1)
            return retry_response.content
        except Exception as e:
            logger.error(f"LLM retry failed: {e}")
    return response_content


def _determine_task_status(validation: dict, code_changes_applied: bool) -> tuple[str, bool, str]:
    """Determine final task status from validation and backend results.

    Returns (status, file_changed, validation_message).
    """
    if validation["issue_not_found"]:
        return "cancelled", False, validation["message"]
    if validation["changes_made"] or validation["problem_fixed"] or code_changes_applied:
        return "success", code_changes_applied or validation["changes_made"], validation["message"]
    return "failed", False, validation["message"]


def _execute_task(
    task: dict,
    config: LlxConfig,
    metrics: Any,
    model_override: Optional[str] = None,
    dry_run: bool = False,
    backend: str = BackendType.LLM_CHAT,
    project_root: Path = Path("."),
) -> TaskResult:
    """Execute a single task."""
    start_time = time.time()
    task_name = task.get("name", "Unnamed Task")
    target_file = task.get("file")

    try:
        model = model_override or _select_model(task, config, metrics)

        if dry_run:
            return TaskResult(
                task_name=task_name,
                status="dry_run",
                model_used=model,
                response="",
                execution_time=time.time() - start_time
            )

        prompt = _build_task_prompt(task, metrics)
        code_changes_applied = False
        response_content = ""

        if backend == BackendType.MCP and target_file:
            response_content, code_changes_applied, backend = _run_mcp_backend(str(target_file), prompt, model)
        elif backend == BackendType.CURSOR and target_file:
            response_content, code_changes_applied = _run_cursor_backend(project_root, prompt, model, str(target_file))
        elif backend == BackendType.WINDSURF and target_file:
            response_content, code_changes_applied = _run_windsurf_backend(project_root, prompt, model, str(target_file))
        elif backend == BackendType.CLAUDE_CODE and target_file:
            response_content, code_changes_applied = _run_claude_code_backend(project_root, prompt, model, str(target_file))
        elif backend in [BackendType.LOCAL, BackendType.DOCKER] and target_file:
            use_docker = backend == BackendType.DOCKER
            response_content, code_changes_applied = _run_aider_backend(project_root, prompt, model, str(target_file), use_docker)

        if not code_changes_applied and backend == BackendType.LLM_CHAT:
            try:
                response_content = _run_llm_chat_with_retry(prompt, model)
            except Exception as e:
                logger.error(f"LLM chat failed: {e}")
                return TaskResult(
                    task_name=task_name,
                    status="failed",
                    model_used=model,
                    response="",
                    error=str(e),
                    execution_time=time.time() - start_time
                )

        validation = _parse_llm_response(response_content)
        status, file_changed, validation_message = _determine_task_status(validation, code_changes_applied)

        return TaskResult(
            task_name=task_name,
            status=status,
            model_used=model,
            response=response_content,
            execution_time=time.time() - start_time,
            file_changed=file_changed,
            validation_message=validation_message
        )

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return TaskResult(
            task_name=task_name,
            status="failed",
            model_used=model_override or "unknown",
            response="",
            error=str(e),
            execution_time=time.time() - start_time
        )
