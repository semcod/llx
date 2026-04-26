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
    """Execute strategy with simplified format support.
    
    Args:
        strategy_path: Path to strategy/planfile YAML
        project_path: Project root directory
        sprint_filter: Optional sprint number to filter
        ticket_id: Optional specific ticket ID from tasks section to execute
        dry_run: Simulate without executing
        on_progress: Callback for progress updates
        model_override: Override model selection
        max_concurrent: Max concurrent tasks
        max_tasks: Max total tasks to process
        use_aider: Use aider for code editing
    """

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

    # If ticket_id is specified, execute that specific ticket from tasks section
    if ticket_id:
        tasks = strategy.get("tasks", [])
        ticket = None
        for task in tasks:
            if task.get("id") == ticket_id:
                ticket = task
                break
        
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found in planfile")
            if on_progress:
                on_progress(f"[red]✗ Ticket {ticket_id} not found[/red]")
            return results
        
        if on_progress:
            on_progress(f"\n[bold blue]Executing ticket:[/bold blue] {ticket_id} - {ticket.get('title', 'Unnamed')}")
        
        # Convert ticket to task format
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
                project_root=Path(project_path).resolve()
            )
            results.append(result)
            
            if on_progress:
                if result.status == "success":
                    on_progress(f"  [green]✓[/green] {ticket_id} ({result.model_used})")
                elif result.status == "dry_run":
                    on_progress(f"  [blue]○[/blue] {ticket_id} (dry-run)")
                else:
                    on_progress(f"  [red]✗[/red] {ticket_id}: {result.error or result.validation_message}")
            
            # Update ticket status in planfile if not dry_run
            if not dry_run:
                _update_task_in_planfile(strategy_path, ticket_id, result.status, result.validation_message or "")
            
        except Exception as e:
            logger.error(f"Ticket execution failed: {e}")
            if on_progress:
                on_progress(f"  [red]✗[/red] {ticket_id}: {str(e)}")
        
        return results

    # Original sprint-based execution
    for sprint in strategy.get("sprints", []):
        sprint_num = sprint.get("sprint", 0)
        
        # Apply sprint filter if specified
        if sprint_filter is not None and sprint_num != sprint_filter:
            if on_progress:
                on_progress(f"[dim]Skipping sprint {sprint_num} (filtered)[/dim]")
            continue
        
        if on_progress:
            on_progress(f"\n[bold blue]Sprint {sprint_num}:[/bold blue] {sprint.get('name', 'Unnamed')}")
        
        # Get task patterns from sprint
        task_patterns = sprint.get("task_patterns", [])
        
        if not task_patterns:
            if on_progress:
                on_progress(f"[dim]No tasks in sprint {sprint_num}[/dim]")
            continue
        
        # Execute tasks
        if max_concurrent > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = []
                for task in task_patterns:
                    future = executor.submit(
                        _execute_task,
                        task=task,
                        config=config,
                        metrics=metrics,
                        model_override=model_override,
                        dry_run=dry_run,
                        backend=selected_backend,
                        project_root=Path(project_path).resolve()
                    )
                    futures.append((task, future))
                
                for task, future in futures:
                    if max_tasks is not None and total_tasks_processed >= max_tasks:
                        break
                    
                    task_name = task.get("name", "Unnamed")
                    if on_progress:
                        on_progress(f"  [yellow]→[/yellow] {task_name}...")
                    
                    try:
                        result = future.result()
                        results.append(result)
                        total_tasks_processed += 1
                        
                        if on_progress:
                            if result.status == "success":
                                on_progress(f"  [green]✓[/green] {task_name} ({result.model_used})")
                            elif result.status == "dry_run":
                                on_progress(f"  [blue]○[/blue] {task_name} (dry-run)")
                            else:
                                on_progress(f"  [red]✗[/red] {task_name}: {result.error or result.validation_message}")
                    except Exception as e:
                        logger.error(f"Task failed: {e}")
                        if on_progress:
                            on_progress(f"  [red]✗[/red] {task_name}: {str(e)}")
        else:
            # Sequential execution
            for task in task_patterns:
                if max_tasks is not None and total_tasks_processed >= max_tasks:
                    break
                
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
                        project_root=Path(project_path).resolve()
                    )
                    results.append(result)
                    total_tasks_processed += 1
                    
                    if on_progress:
                        if result.status == "success":
                            on_progress(f"  [green]✓[/green] {task_name} ({result.model_used})")
                        elif result.status == "dry_run":
                            on_progress(f"  [blue]○[/blue] {task_name} (dry-run)")
                        else:
                            on_progress(f"  [red]✗[/red] {task_name}: {result.error or result.validation_message}")
                    
                    # Update strategy with results if it's a real execution
                    if not dry_run:
                        # Mark task status in the sprint pattern
                        task["status"] = result.status
                        if "notes" not in task:
                            task["notes"] = []
                        if not isinstance(task["notes"], list):
                            task["notes"] = [task["notes"]]
                        from datetime import datetime
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        task["notes"].append(f"[{ts}] {result.status}: {result.validation_message or result.error or 'no details'}")
                        _save_strategy(strategy_path, strategy)
                        
                except Exception as e:
                    logger.error(f"Task failed: {e}")
                    if on_progress:
                        on_progress(f"  [red]✗[/red] {task_name}: {str(e)}")
                
                # Check max_tasks limit
                if max_tasks is not None and total_tasks_processed >= max_tasks:
                    if on_progress:
                        on_progress(f"[dim]Reached max_tasks limit ({max_tasks}), stopping.[/dim]")
                    break
    
    return results
