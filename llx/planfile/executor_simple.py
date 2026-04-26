"""Simplified executor for LLX planfile integration."""

from pathlib import Path
from dataclasses import dataclass
from typing import Any, List, Optional
import logging
import time
import hashlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage
from llx.analysis.collector import analyze_project
from llx.utils.aider import _run_aider_fix

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

    # Check Cursor AI
    try:
        subprocess.run(
            ["cursor", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
        backends[BackendType.CURSOR] = True
        logger.info("Cursor is available")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.info("Cursor not available")

    # Check Windsurf AI
    try:
        subprocess.run(
            ["windsurf", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
        backends[BackendType.WINDSURF] = True
        logger.info("Windsurf is available")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.info("Windsurf not available")

    # Check Claude Code
    try:
        subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
        backends[BackendType.CLAUDE_CODE] = True
        logger.info("Claude Code is available")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.info("Claude Code not available")

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

    Priority: LOCAL > CURSOR > WINDSURF > CLAUDE_CODE > DOCKER > MCP > LLM_CHAT

    Returns:
        Selected backend type.
    """
    # Priority order: Local tools first, then Docker, then MCP, then fallback
    if backends.get(BackendType.LOCAL):
        return BackendType.LOCAL
    if backends.get(BackendType.CURSOR):
        return BackendType.CURSOR
    if backends.get(BackendType.WINDSURF):
        return BackendType.WINDSURF
    if backends.get(BackendType.CLAUDE_CODE):
        return BackendType.CLAUDE_CODE
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
    """Run Cursor AI for code editing.

    Args:
        workdir: Working directory path
        prompt: The prompt/instruction for Cursor
        model: Model to use
        files: Specific files to edit (optional)

    Returns:
        Dict with success status, stdout, stderr.
    """
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
    """Run Windsurf AI for code editing.

    Args:
        workdir: Working directory path
        prompt: The prompt/instruction for Windsurf
        model: Model to use
        files: Specific files to edit (optional)

    Returns:
        Dict with success status, stdout, stderr.
    """
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
    """Run Claude Code for code editing.

    Args:
        workdir: Working directory path
        prompt: The prompt/instruction for Claude Code
        model: Model to use
        files: Specific files to edit (optional)

    Returns:
        Dict with success status, stdout, stderr.
    """
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


def _apply_code_changes(response: str, project_path: Path, target_file: Optional[Path]) -> bool:
    """Parse LLM response for code blocks and apply changes to files.

    Returns True if any changes were applied.
    """
    import re

    changes_applied = False

    # Pattern for code blocks with file paths: ```python:path/to/file.py
    code_block_pattern = r'```(?:python|yaml|json|toml|text)?(?:[:\s]*([^\s\n]+))?\n([\s\S]*?)```'

    # First, try to find code blocks with explicit file paths
    for match in re.finditer(code_block_pattern, response):
        file_path = match.group(1)
        code_content = match.group(2)

        if file_path:
            # Explicit file path in code block
            full_path = project_path / file_path
            if not full_path.is_absolute():
                full_path = project_path / file_path

            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(code_content.strip() + "\n")
                logger.info(f"Applied changes to {file_path}")
                changes_applied = True
            except Exception as e:
                logger.error(f"Failed to write to {file_path}: {e}")
        elif target_file:
            # No explicit path, use target file from task
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(code_content.strip() + "\n")
                logger.info(f"Applied changes to {target_file}")
                changes_applied = True
            except Exception as e:
                logger.error(f"Failed to write to {target_file}: {e}")

    # If no code blocks with paths found, try to apply to target file if specified
    if not changes_applied and target_file:
        # Look for any code block without path
        simple_code_pattern = r'```\n([\s\S]*?)```'
        for match in re.finditer(simple_code_pattern, response):
            code_content = match.group(1)
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(code_content.strip() + "\n")
                logger.info(f"Applied changes to {target_file}")
                changes_applied = True
                break  # Only apply first code block
            except Exception as e:
                logger.error(f"Failed to write to {target_file}: {e}")

    return changes_applied


def _get_file_hash(file_path: Path) -> Optional[str]:
    """Get SHA256 hash of a file."""
    try:
        if not file_path.exists():
            return None
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        return None


def _analyze_llm_response(response: str) -> dict:
    """Analyze LLM response to determine if changes were made.

    Returns dict with keys:
    - changes_made: bool - whether LLM claims to have made changes
    - problem_fixed: bool - whether LLM claims the problem was fixed
    - issue_not_found: bool - whether LLM says the issue doesn't exist
    - message: str - summary of LLM's assessment
    """
    response_lower = response.lower()

    # Check if LLM claims issue not found
    not_found_indicators = [
        "issue not found",
        "problem not found",
        "no such issue",
        "cannot find",
        "doesn't exist",
        "already fixed",
        "already resolved",
        "no action needed",
    ]
    issue_not_found = any(indicator in response_lower for indicator in not_found_indicators)

    # Check if LLM claims changes were made
    changes_indicators = [
        "i have modified",
        "i have changed",
        "i've updated",
        "here is the modified",
        "changes made",
        "file updated",
        "code changed",
    ]
    changes_made = any(indicator in response_lower for indicator in changes_indicators)

    # Check if LLM claims problem was fixed
    fixed_indicators = [
        "issue fixed",
        "problem fixed",
        "resolved",
        "corrected",
        "fixed the",
        "has been fixed",
    ]
    problem_fixed = any(indicator in response_lower for indicator in fixed_indicators)

    # Build summary message
    if issue_not_found:
        message = "LLM reports issue not found or already fixed"
    elif changes_made and problem_fixed:
        message = "LLM reports changes made and issue fixed"
    elif changes_made:
        message = "LLM reports changes made"
    elif problem_fixed:
        message = "LLM reports issue fixed"
    else:
        message = "LLM response unclear about changes"

    return {
        "changes_made": changes_made,
        "problem_fixed": problem_fixed,
        "issue_not_found": issue_not_found,
        "message": message
    }


@dataclass
class TaskResult:
    """Result of executing a task."""
    task_name: str
    status: str  # "success" | "failed" | "skipped" | "dry_run" | "invalid" | "not_found" | "already_fixed"
    model_used: str
    response: str
    error: Optional[str] = None
    execution_time: Optional[float] = None
    file_changed: bool = False
    validation_message: Optional[str] = None


def execute_strategy(
    strategy_path: str | Path,
    project_path: str | Path = ".",
    *,
    sprint_filter: Optional[int] = None,
    dry_run: bool = False,
    on_progress: Any = None,
    model_override: Optional[str] = None,
    max_concurrent: int = 1,
    max_tasks: Optional[int] = None,
    use_aider: bool = False,
) -> List[TaskResult]:
    """Execute strategy with simplified format support."""

    # Auto-detect and select best backend for code editing
    selected_backend = BackendType.LLM_CHAT
    if use_aider:
        backends = _detect_available_backends()
        selected_backend = _select_best_backend(backends)
        logger.info(f"Selected backend: {selected_backend}")

    # Load strategy
    strategy = _load_strategy(strategy_path)
    
    # Normalize to handle both V1 and V2 formats
    strategy = _normalize_strategy(strategy)
    
    config = LlxConfig.load(str(project_path))
    metrics = analyze_project(str(project_path))
    results = []
    total_tasks_processed = 0

    for sprint in strategy.get("sprints", []):
        if sprint_filter and sprint.get("id") != sprint_filter:
            continue

        if on_progress:
            on_progress(f"Sprint {sprint.get('id')}: {sprint.get('name', 'Unnamed')}")

        # Get tasks from sprint
        tasks = _get_sprint_tasks(sprint)

        # Filter out already successful tasks
        pending_tasks = []
        for task in tasks:
            if task.get("status") == "success":
                task_name = task.get("name", "Unnamed Task")
                if on_progress:
                    on_progress(f"  Task: {task_name} [dim](already completed, skipping)[/dim]")
                results.append(TaskResult(
                    task_name=task_name,
                    status="skipped",
                    model_used="none",
                    response="Already completed"
                ))
            else:
                pending_tasks.append(task)

        # Apply max_tasks limit
        if max_tasks is not None:
            remaining = max_tasks - total_tasks_processed
            if remaining <= 0:
                if on_progress:
                    on_progress(f"[dim]Reached max_tasks limit ({max_tasks}), stopping.[/dim]")
                break
            pending_tasks = pending_tasks[:remaining]

        # Execute tasks (concurrent or sequential)
        if max_concurrent > 1 and not dry_run:
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_task = {}
                for task in pending_tasks:
                    future = executor.submit(
                        _execute_task, task, project_path, config, metrics, dry_run, model_override, selected_backend
                    )
                    future_to_task[future] = task

                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    task_name = task.get("name", "Unnamed Task")
                    if on_progress:
                        on_progress(f"  Task: {task_name}")

                    try:
                        result = future.result()
                        results.append(result)
                        total_tasks_processed += 1

                        # Update status in memory and SAVE to file after each task
                        # Only mark as success if validation passed
                        if result.status == "success":
                            task["status"] = "success"
                            _save_strategy(strategy_path, strategy)
                        elif result.status in ["invalid", "not_found", "already_fixed"]:
                            # Mark these with descriptive status for review
                            task["status"] = result.status
                            task["validation_message"] = result.validation_message or ""
                            _save_strategy(strategy_path, strategy)

                        # Check max_tasks limit
                        if max_tasks is not None and total_tasks_processed >= max_tasks:
                            if on_progress:
                                on_progress(f"[dim]Reached max_tasks limit ({max_tasks}), stopping.[/dim]")
                            # Cancel remaining futures
                            for f in future_to_task:
                                f.cancel()
                            break
                    except Exception as e:
                        logger.error(f"Task execution failed: {e}")
                        results.append(TaskResult(
                            task_name=task_name,
                            status="failed",
                            model_used="unknown",
                            response="",
                            error=str(e)
                        ))
                        total_tasks_processed += 1
        else:
            # Sequential execution
            for task in pending_tasks:
                task_name = task.get("name", "Unnamed Task")
                if on_progress:
                    on_progress(f"  Task: {task_name}")

                result = _execute_task(
                    task, project_path, config, metrics, dry_run, model_override, selected_backend
                )
                results.append(result)
                total_tasks_processed += 1

                # Update status in memory and SAVE to file after each task
                if not dry_run:
                    if result.status == "success":
                        task["status"] = "success"
                        _save_strategy(strategy_path, strategy)
                    elif result.status in ["invalid", "not_found", "already_fixed"]:
                        # Mark these with descriptive status for review
                        task["status"] = result.status
                        task["validation_message"] = result.validation_message or ""
                        _save_strategy(strategy_path, strategy)

                # Check max_tasks limit
                if max_tasks is not None and total_tasks_processed >= max_tasks:
                    if on_progress:
                        on_progress(f"[dim]Reached max_tasks limit ({max_tasks}), stopping.[/dim]")
                    break
    
    return results


def _save_strategy(path: str | Path, strategy: dict) -> None:
    """Save YAML strategy file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(strategy, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        logger.error(f"Failed to save strategy: {e}")


def _load_strategy(path: str | Path) -> dict:
    """Load YAML strategy file."""
    try:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load strategy: {e}")
        raise


def _normalize_strategy(strategy: dict) -> dict:
    """Normalize strategy to handle different formats."""
    
    # Handle planfile.yaml format (redsl-generated)
    if "tasks" in strategy and isinstance(strategy["tasks"], list):
        # Build task lookup from flat tasks list
        task_lookup = {}
        for task in strategy["tasks"]:
            task_id = task.get("id")
            if task_id:
                task_lookup[task_id] = task
        
        # Convert sprint task_patterns to use task data from lookup
        if "sprints" in strategy:
            for sprint in strategy.get("sprints", []):
                if "task_patterns" in sprint:
                    normalized_patterns = []
                    for pattern in sprint["task_patterns"]:
                        pattern_id = pattern.get("id")
                        if pattern_id and pattern_id in task_lookup:
                            # Use full task data from lookup
                            task_data = task_lookup[pattern_id]
                            normalized_patterns.append({
                                "name": pattern.get("name", task_data.get("title", pattern_id)),
                                "description": pattern.get("description", task_data.get("description", "")),
                                "task_type": _map_action_to_task_type(task_data.get("action", "feature")),
                                "model_hints": pattern.get("model_hints", {}),
                                "priority": _map_priority(task_data.get("priority", 3)),
                                "file": task_data.get("file", ""),
                                "action": task_data.get("action", "")
                            })
                        else:
                            # Keep pattern as-is if no matching task
                            normalized_patterns.append({
                                "name": pattern.get("name", pattern.get("id", "Unnamed")),
                                "description": pattern.get("description", ""),
                                "task_type": pattern.get("task_type", "feature"),
                                "model_hints": pattern.get("model_hints", {}),
                                "priority": pattern.get("priority", "medium")
                            })
                    sprint["task_patterns"] = normalized_patterns
    
    # Handle V2 format with tasks in sprints
    if "sprints" in strategy:
        for sprint in strategy.get("sprints", []):
            # Convert tasks to task_patterns format for executor
            if "tasks" in sprint and "task_patterns" not in sprint:
                task_patterns = []
                for task in sprint["tasks"]:
                    if isinstance(task, dict):
                        # Task is already an object (V2 embedded)
                        task_patterns.append({
                            "name": task.get("name", "Unnamed Task"),
                            "description": task.get("description", ""),
                            "task_type": task.get("type", "feature"),
                            "model_hints": task.get("model_hints", {}),
                            "priority": task.get("priority", "medium")
                        })
                    elif isinstance(task, str):
                        # Task is a reference (V2 with separate definitions)
                        # Try to find it in tasks.patterns if exists
                        if "tasks" in strategy and "patterns" in strategy["tasks"]:
                            for pattern in strategy["tasks"]["patterns"]:
                                if pattern.get("id") == task:
                                    task_patterns.append({
                                        "name": pattern.get("name", task),
                                        "description": pattern.get("description", ""),
                                        "task_type": pattern.get("type", "feature"),
                                        "model_hints": pattern.get("model_hints", {}),
                                        "priority": pattern.get("priority", "medium")
                                    })
                                    break
                        else:
                            # Create a placeholder task
                            task_patterns.append({
                                "name": task,
                                "description": f"Task: {task}",
                                "task_type": "feature",
                                "model_hints": {},
                                "priority": "medium"
                            })
                sprint["task_patterns"] = task_patterns
    
    return strategy


def _map_action_to_task_type(action: str) -> str:
    """Map redsl action to task_type."""
    action_map = {
        "reduce_complexity": "refactor",
        "extract_function": "refactor",
        "extract_class": "refactor",
        "split_module": "refactor",
        "fix": "bugfix",
        "feature": "feature",
        "tech_debt": "tech_debt"
    }
    return action_map.get(action, "feature")


def _map_priority(priority: int) -> str:
    """Map numeric priority to string."""
    if priority <= 1:
        return "high"
    elif priority <= 2:
        return "high"
    elif priority == 3:
        return "medium"
    else:
        return "low"


def _get_sprint_tasks(sprint: dict) -> List[dict]:
    """Get tasks from sprint, handling both formats."""
    # Prefer task_patterns (executor format)
    if "task_patterns" in sprint:
        return sprint["task_patterns"]
    
    # Fallback to tasks (V2 format)
    elif "tasks" in sprint:
        return sprint["tasks"]
    
    return []


def _execute_task(
    task: dict,
    project_path: str | Path,
    config: LlxConfig,
    metrics: Any,
    dry_run: bool,
    model_override: Optional[str] = None,
    backend: str = BackendType.LLM_CHAT,
) -> TaskResult:
    """Execute a single task with validation."""
    start_time = time.time()

    task_name = task.get("name", "Unnamed Task")
    description = task.get("description", "")
    task_type = task.get("task_type", "feature")
    model_hints = task.get("model_hints", {})
    file_path = task.get("file", "")

    # Get file hash before execution if file is specified
    project_root = Path(project_path).resolve()
    target_file = None
    file_hash_before = None

    if file_path:
        target_file = project_root / file_path
        if not target_file.is_absolute():
            target_file = project_root / file_path
        file_hash_before = _get_file_hash(target_file)

        if file_hash_before is None:
            # File doesn't exist
            return TaskResult(
                task_name=task_name,
                status="not_found",
                model_used="none",
                response="",
                validation_message=f"File not found: {file_path}",
                execution_time=time.time() - start_time
            )

    try:
        # Select model
        model = model_override or _select_model(task, config, metrics)

        if dry_run:
            return TaskResult(
                task_name=task_name,
                status="dry_run",
                model_used=model,
                response="",
                execution_time=time.time() - start_time
            )

        # Build prompt
        prompt = _build_task_prompt(task, metrics)

        # Execute using selected backend
        if backend == BackendType.MCP and target_file:
            # Use MCP for code editing
            try:
                from llx.mcp.client import MCPClient
                mcp_client = MCPClient()
                
                # Build MCP tool call
                tool_result = mcp_client.call_tool(
                    "aider_edit_file",
                    {
                        "file_path": str(target_file),
                        "prompt": prompt,
                        "model": model
                    }
                )
                
                response_content = str(tool_result)
                code_changes_applied = True  # Assume MCP handles changes
                
                if not code_changes_applied:
                    logger.error("MCP editing failed")
            except Exception as e:
                logger.error(f"MCP editing failed: {e}")
                # Fallback to LLM chat
                backend = BackendType.LLM_CHAT
                
        elif backend == BackendType.CURSOR and target_file:
            # Use Cursor for code editing
            cursor_result = _run_cursor_edit(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)]
            )
            
            response_content = cursor_result.get("stdout", "") + "\n" + cursor_result.get("stderr", "")
            code_changes_applied = cursor_result.get("success", False)
            
            if not code_changes_applied:
                logger.error(f"Cursor failed: {cursor_result.get('stderr', 'Unknown error')}")
                
        elif backend == BackendType.WINDSURF and target_file:
            # Use Windsurf for code editing
            windsurf_result = _run_windsurf_edit(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)]
            )
            
            response_content = windsurf_result.get("stdout", "") + "\n" + windsurf_result.get("stderr", "")
            code_changes_applied = windsurf_result.get("success", False)
            
            if not code_changes_applied:
                logger.error(f"Windsurf failed: {windsurf_result.get('stderr', 'Unknown error')}")
                
        elif backend == BackendType.CLAUDE_CODE and target_file:
            # Use Claude Code for code editing
            claude_result = _run_claude_code_edit(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)]
            )
            
            response_content = claude_result.get("stdout", "") + "\n" + claude_result.get("stderr", "")
            code_changes_applied = claude_result.get("success", False)
            
            if not code_changes_applied:
                logger.error(f"Claude Code failed: {claude_result.get('stderr', 'Unknown error')}")
                
        elif backend in [BackendType.LOCAL, BackendType.DOCKER] and target_file:
            # Use aider for code editing
            use_docker = (backend == BackendType.DOCKER)
            aider_result = _run_aider_fix(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)] if target_file else None,
                use_docker=use_docker
            )

            response_content = aider_result.get("stdout", "") + "\n" + aider_result.get("stderr", "")
            code_changes_applied = aider_result.get("success", False)

            if not code_changes_applied:
                logger.error(f"Aider failed: {aider_result.get('stderr', 'Unknown error')}")
        else:
            # Use LLM chat (fallback or when no file specified)
            with LlxClient(config) as client:
                response = client.chat(
                    [ChatMessage(role="user", content=prompt)],
                    model=model
                )
            response_content = response.content

            # Try to apply code changes from LLM response
            code_changes_applied = False
            if target_file:
                code_changes_applied = _apply_code_changes(response_content, project_root, target_file)

        # Validate after execution
        file_hash_after = None
        file_changed = False
        validation_status = "success"
        validation_message = ""

        if target_file:
            file_hash_after = _get_file_hash(target_file)
            file_changed = (file_hash_before != file_hash_after)

        # Analyze LLM response
        llm_analysis = _analyze_llm_response(response_content)

        # Determine final status based on file changes, code application, and LLM response
        if llm_analysis["issue_not_found"]:
            validation_status = "already_fixed"
            validation_message = llm_analysis["message"]
        elif file_changed or code_changes_applied:
            validation_status = "success"
            validation_message = llm_analysis["message"] if code_changes_applied else "File changed"
        elif not file_changed and not code_changes_applied and not llm_analysis["changes_made"]:
            # File didn't change, no code applied, LLM didn't claim to make changes
            validation_status = "invalid"
            validation_message = "No changes made to code"
        elif llm_analysis["changes_made"]:
            validation_status = "success"
            validation_message = llm_analysis["message"]
        else:
            validation_status = "invalid"
            validation_message = llm_analysis["message"]

        return TaskResult(
            task_name=task_name,
            status=validation_status,
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
            model_used=model or "unknown",
            response="",
            error=str(e),
            execution_time=time.time() - start_time
        )


def _select_model(task: dict, config: LlxConfig, metrics: Any) -> str:
    """Select model based on task and project metrics."""
    
    # Get model hints
    hints = task.get("model_hints", {})
    if isinstance(hints, str):
        hints = {"implementation": hints}
    elif not isinstance(hints, dict):
        hints = {}
    
    # Determine preferred tier
    preferred_tier = hints.get("implementation") or hints.get("design", "balanced")
    
    # Normalize tier names
    if preferred_tier == "free":
        preferred_tier = "cheap"
    
    # Check project complexity
    if hasattr(metrics, 'avg_cc') and hasattr(metrics, 'max_cc'):
        if metrics.avg_cc > 15 or metrics.max_cc > 30:
            # Complex project - might need better model
            if preferred_tier == "cheap" and task.get("task_type") in ["feature", "tech_debt"]:
                preferred_tier = "balanced"
    
    # Select model based on tier
    model_map = {
        "local": config.models.get("local"),
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
