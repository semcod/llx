"""Strategy loading, normalization, and execution."""

from pathlib import Path
from typing import Any, List, Optional
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

from llx.config import LlxConfig
from llx.analysis.collector import analyze_project
from llx.planfile.executor.base import BackendType, TaskResult
from llx.planfile.executor.backends import (
    _detect_available_backends,
    _select_best_backend,
)
from llx.planfile.executor.task import _execute_task

logger = logging.getLogger(__name__)


def _load_strategy(path: str | Path) -> dict:
    """Load YAML strategy file."""
    try:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load strategy: {e}")
        raise


def _save_strategy(path: str | Path, strategy: dict) -> None:
    """Save YAML strategy file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(strategy, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        logger.error(f"Failed to save strategy: {e}")


def _find_task_in_planfile(planfile: dict, task_id: str) -> Optional[dict]:
    """Find a task in planfile by id, title, name, or sprint pattern name."""
    tasks = planfile.get("tasks", [])
    for task in tasks:
        if task.get("id") == task_id:
            return task

    for task in tasks:
        if task.get("title") == task_id or task.get("name") == task_id:
            return task

    for sprint in planfile.get("sprints", []):
        for pattern in sprint.get("task_patterns", []):
            if pattern.get("name") == task_id:
                return pattern
    return None


def _append_task_note(target_task: dict, comment: str) -> None:
    """Append a timestamped comment to a task's notes."""
    if "notes" not in target_task:
        target_task["notes"] = []
    if not isinstance(target_task["notes"], list):
        target_task["notes"] = [target_task["notes"]]
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_task["notes"].append(f"[{timestamp}] {comment}")


def _update_task_in_planfile(
    planfile_path: str | Path,
    task_id: str,
    status: str,
    comment: str
) -> bool:
    """Update task status and add comment in planfile.

    Args:
        planfile_path: Path to planfile.yaml
        task_id: Task ID to update
        status: New status (e.g., 'cancelled', 'done', 'in_progress')
        comment: Comment explaining the status change

    Returns:
        True if task was found and updated, False otherwise
    """
    try:
        planfile = _load_strategy(planfile_path)
        target_task = _find_task_in_planfile(planfile, task_id)

        if target_task is None:
            logger.warning(f"Task {task_id} not found in planfile")
            return False

        target_task["status"] = status
        _append_task_note(target_task, comment)

        _save_strategy(planfile_path, planfile)
        logger.info(f"Updated task {task_id} in planfile: status={status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update task in planfile: {e}")
        return False


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


def _build_task_lookup(strategy: dict) -> dict[str, dict]:
    """Build a lookup dict mapping task id -> task data."""
    lookup: dict[str, dict] = {}
    for task in strategy.get("tasks", []):
        task_id = task.get("id")
        if task_id:
            lookup[task_id] = task
    return lookup


def _normalize_pattern_from_lookup(pattern: dict, task_lookup: dict) -> dict:
    """Normalize a single pattern using task lookup when available."""
    pattern_id = pattern.get("id")
    if pattern_id and pattern_id in task_lookup:
        task_data = task_lookup[pattern_id]
        return {
            "name": pattern.get("name", task_data.get("title", pattern_id)),
            "description": pattern.get("description", task_data.get("description", "")),
            "task_type": _map_action_to_task_type(task_data.get("action", "feature")),
            "model_hints": pattern.get("model_hints", {}),
            "priority": _map_priority(task_data.get("priority", 3)),
            "file": task_data.get("file", ""),
            "action": task_data.get("action", "")
        }
    return {
        "name": pattern.get("name", pattern.get("id", "Unnamed")),
        "description": pattern.get("description", ""),
        "task_type": pattern.get("task_type", "feature"),
        "model_hints": pattern.get("model_hints", {}),
        "priority": pattern.get("priority", "medium")
    }


def _normalize_v2_task(task: dict | str, strategy: dict) -> Optional[dict]:
    """Normalize a single V2 sprint task into a task_pattern dict."""
    if isinstance(task, dict):
        return {
            "name": task.get("name", "Unnamed Task"),
            "description": task.get("description", ""),
            "task_type": task.get("type", "feature"),
            "model_hints": task.get("model_hints", {}),
            "priority": task.get("priority", "medium")
        }
    if isinstance(task, str):
        patterns = strategy.get("tasks", {}).get("patterns", [])
        for pattern in patterns:
            if pattern.get("id") == task:
                return {
                    "name": pattern.get("name", "Unnamed Task"),
                    "description": pattern.get("description", ""),
                    "task_type": pattern.get("type", "feature"),
                    "model_hints": pattern.get("model_hints", {}),
                    "priority": pattern.get("priority", "medium")
                }
    return None


def _normalize_v2_sprints(strategy: dict) -> None:
    """Convert V2 sprint tasks to task_patterns format (mutates strategy in-place)."""
    for sprint in strategy.get("sprints", []):
        if "tasks" in sprint and "task_patterns" not in sprint:
            task_patterns = []
            for task in sprint["tasks"]:
                normalized = _normalize_v2_task(task, strategy)
                if normalized:
                    task_patterns.append(normalized)
            sprint["task_patterns"] = task_patterns


def _normalize_strategy(strategy: dict) -> dict:
    """Normalize strategy to handle different formats."""
    # Handle planfile.yaml format (redsl-generated)
    if "tasks" in strategy and isinstance(strategy["tasks"], list):
        task_lookup = _build_task_lookup(strategy)
        if "sprints" in strategy:
            for sprint in strategy.get("sprints", []):
                if "task_patterns" in sprint:
                    sprint["task_patterns"] = [
                        _normalize_pattern_from_lookup(pattern, task_lookup)
                        for pattern in sprint["task_patterns"]
                    ]

    # Handle V2 format with tasks in sprints
    if "sprints" in strategy:
        _normalize_v2_sprints(strategy)

    return strategy


def _run_single_task_pattern(
    task: dict,
    config: LlxConfig,
    metrics: Any,
    model_override: Optional[str],
    dry_run: bool,
    selected_backend: str,
    project_path: Path,
    on_progress: Any,
) -> Optional[TaskResult]:
    """Execute one task pattern and report progress."""
    task_name = task.get("name", "Unnamed")
    if on_progress:
        on_progress(f"  [yellow]→[/yellow] {task_name}...")
    try:
        result = _execute_task(
            task=task,
            config=config,
            metrics=metrics,
            model_override=model_override,
            dry_run=dry_run,
            backend=selected_backend,
            project_root=project_path.resolve()
        )
        if on_progress:
            if result.status == "success":
                on_progress(f"  [green]✓[/green] {task_name} ({result.model_used})")
            elif result.status == "dry_run":
                on_progress(f"  [blue]○[/blue] {task_name} (dry-run)")
            else:
                on_progress(f"  [red]✗[/red] {task_name}: {result.error or result.validation_message}")
        return result
    except Exception as e:
        logger.error(f"Task failed: {e}")
        if on_progress:
            on_progress(f"  [red]✗[/red] {task_name}: {str(e)}")
        return None


def _update_sprint_task_status(task: dict, result: TaskResult, strategy_path: str | Path, strategy: dict) -> None:
    """Update a sprint task's status and notes in-place and persist strategy."""
    task["status"] = result.status
    if "notes" not in task:
        task["notes"] = []
    if not isinstance(task["notes"], list):
        task["notes"] = [task["notes"]]
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task["notes"].append(f"[{ts}] {result.status}: {result.validation_message or result.error or 'no details'}")
    _save_strategy(strategy_path, strategy)


def _execute_ticket_block(
    strategy: dict,
    ticket_id: str,
    config: LlxConfig,
    metrics: Any,
    model_override: Optional[str],
    dry_run: bool,
    selected_backend: str,
    project_path: Path,
    on_progress: Any,
    strategy_path: str | Path,
) -> List[TaskResult]:
    """Execute a single ticket by ID and update planfile."""
    tasks = strategy.get("tasks", [])
    ticket = next((t for t in tasks if t.get("id") == ticket_id), None)

    if not ticket:
        logger.error(f"Ticket {ticket_id} not found in planfile")
        if on_progress:
            on_progress(f"[red]✗ Ticket {ticket_id} not found[/red]")
        return []

    if on_progress:
        on_progress(f"\n[bold blue]Executing ticket:[/bold blue] {ticket_id} - {ticket.get('title', 'Unnamed')}")

    task_dict = {
        "name": ticket.get("title", ticket_id),
        "description": ticket.get("description", ""),
        "task_type": _map_action_to_task_type(ticket.get("action", "feature")),
        "model_hints": {"tier": "balanced"},
        "priority": _map_priority(ticket.get("priority", 3)),
        "file": ticket.get("file", ""),
        "action": ticket.get("action", "")
    }

    try:
        result = _execute_task(
            task=task_dict,
            config=config,
            metrics=metrics,
            model_override=model_override,
            dry_run=dry_run,
            backend=selected_backend,
            project_root=project_path.resolve()
        )
        if on_progress:
            if result.status == "success":
                on_progress(f"  [green]✓[/green] {ticket_id} ({result.model_used})")
            elif result.status == "dry_run":
                on_progress(f"  [blue]○[/blue] {ticket_id} (dry-run)")
            else:
                on_progress(f"  [red]✗[/red] {ticket_id}: {result.error or result.validation_message}")

        if not dry_run:
            _update_task_in_planfile(strategy_path, ticket_id, result.status, result.validation_message or "")

        return [result]
    except Exception as e:
        logger.error(f"Ticket execution failed: {e}")
        if on_progress:
            on_progress(f"  [red]✗[/red] {ticket_id}: {str(e)}")
        return []


def _select_execution_backend(use_aider: bool) -> str:
    """Select backend based on aider availability."""
    if not use_aider:
        return BackendType.LLM_CHAT
    backends = _detect_available_backends()
    selected = _select_best_backend(backends)
    logger.info(f"Selected backend: {selected}")
    return selected


def _should_skip_sprint(sprint: dict, sprint_filter: Optional[int], on_progress: Any) -> bool:
    """Return True if sprint should be skipped due to filter."""
    sprint_num = sprint.get("sprint", 0)
    if sprint_filter is not None and sprint_num != sprint_filter:
        if on_progress:
            on_progress(f"[dim]Skipping sprint {sprint_num} (filtered)[/dim]")
        return True
    return False


def _execute_concurrent_tasks(
    task_patterns: list,
    config: LlxConfig,
    metrics: Any,
    model_override: Optional[str],
    dry_run: bool,
    selected_backend: str,
    project_path: Path,
    on_progress: Any,
    max_tasks: Optional[int],
    strategy_path: str | Path,
    strategy: dict,
) -> List[TaskResult]:
    """Execute tasks concurrently using ThreadPoolExecutor."""
    results: List[TaskResult] = []
    total_tasks_processed = 0
    with ThreadPoolExecutor(max_workers=len(task_patterns)) as executor:
        futures = [
            (task, executor.submit(
                _run_single_task_pattern,
                task, config, metrics, model_override, dry_run,
                selected_backend, project_path, on_progress
            ))
            for task in task_patterns
        ]
        for task, future in futures:
            if max_tasks is not None and total_tasks_processed >= max_tasks:
                break
            result = future.result()
            if result is not None:
                results.append(result)
                total_tasks_processed += 1
                if not dry_run:
                    _update_sprint_task_status(task, result, strategy_path, strategy)
    return results


def _execute_sequential_tasks(
    task_patterns: list,
    config: LlxConfig,
    metrics: Any,
    model_override: Optional[str],
    dry_run: bool,
    selected_backend: str,
    project_path: Path,
    on_progress: Any,
    max_tasks: Optional[int],
    strategy_path: str | Path,
    strategy: dict,
) -> List[TaskResult]:
    """Execute tasks sequentially, respecting max_tasks limit."""
    results: List[TaskResult] = []
    for task in task_patterns:
        if max_tasks is not None and len(results) >= max_tasks:
            if on_progress:
                on_progress(f"[dim]Reached max_tasks limit ({max_tasks}), stopping.[/dim]")
            break
        result = _run_single_task_pattern(
            task, config, metrics, model_override, dry_run,
            selected_backend, project_path, on_progress
        )
        if result is not None:
            results.append(result)
            if not dry_run:
                _update_sprint_task_status(task, result, strategy_path, strategy)
    return results


def execute_strategy(
    strategy_path: str | Path,
    project_path: str | Path = ".",
    *,
    sprint_filter: Optional[int] = None,
    ticket_id: Optional[str] = None,
    dry_run: bool = False,
    on_progress: Any = None,
    model_override: Optional[str] = None,
    max_concurrent: int = 1,
    max_tasks: Optional[int] = None,
    use_aider: bool = False,
) -> List[TaskResult]:
    """Execute strategy with simplified format support."""
    selected_backend = _select_execution_backend(use_aider)
    strategy = _load_strategy(strategy_path)
    strategy = _normalize_strategy(strategy)
    config = LlxConfig.load(str(project_path))
    metrics = analyze_project(str(project_path))
    resolved_path = Path(project_path).resolve()

    if ticket_id:
        return _execute_ticket_block(
            strategy, ticket_id, config, metrics, model_override,
            dry_run, selected_backend, resolved_path, on_progress, strategy_path
        )

    all_results: List[TaskResult] = []
    for sprint in strategy.get("sprints", []):
        if _should_skip_sprint(sprint, sprint_filter, on_progress):
            continue

        sprint_num = sprint.get("sprint", 0)
        if on_progress:
            on_progress(f"\n[bold blue]Sprint {sprint_num}:[/bold blue] {sprint.get('name', 'Unnamed')}")

        task_patterns = sprint.get("task_patterns", [])
        if not task_patterns:
            if on_progress:
                on_progress(f"[dim]No tasks in sprint {sprint_num}[/dim]")
            continue

        if max_concurrent > 1:
            sprint_results = _execute_concurrent_tasks(
                task_patterns, config, metrics, model_override, dry_run,
                selected_backend, resolved_path, on_progress, max_tasks,
                strategy_path, strategy,
            )
        else:
            sprint_results = _execute_sequential_tasks(
                task_patterns, config, metrics, model_override, dry_run,
                selected_backend, resolved_path, on_progress, max_tasks,
                strategy_path, strategy,
            )
        all_results.extend(sprint_results)
        if max_tasks is not None and len(all_results) >= max_tasks:
            break

    return all_results
