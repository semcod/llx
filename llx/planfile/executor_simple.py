"""Simplified executor for LLX planfile integration."""

from pathlib import Path
from dataclasses import dataclass
from typing import Any, List, Optional
import logging
import time

import yaml

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage
from llx.analysis.collector import analyze_project

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of executing a task."""
    task_name: str
    status: str  # "success" | "failed" | "skipped" | "dry_run"
    model_used: str
    response: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


def execute_strategy(
    strategy_path: str | Path,
    project_path: str | Path = ".",
    *,
    sprint_filter: Optional[int] = None,
    dry_run: bool = False,
    on_progress: Any = None,
    model_override: Optional[str] = None,
) -> List[TaskResult]:
    """Execute strategy with simplified format support."""
    
    # Load strategy
    strategy = _load_strategy(strategy_path)
    
    # Normalize to handle both V1 and V2 formats
    strategy = _normalize_strategy(strategy)
    
    config = LlxConfig.load(str(project_path))
    metrics = analyze_project(str(project_path))
    results = []
    
    for sprint in strategy.get("sprints", []):
        if sprint_filter and sprint.get("id") != sprint_filter:
            continue
        
        if on_progress:
            on_progress(f"Sprint {sprint.get('id')}: {sprint.get('name', 'Unnamed')}")
        
        # Get tasks from sprint
        tasks = _get_sprint_tasks(sprint)
        
        for task in tasks:
            if on_progress:
                on_progress(f"  Task: {task.get('name', 'Unnamed')}")
            
            result = _execute_task(
                task, project_path, config, metrics, dry_run, model_override
            )
            results.append(result)
    
    return results


def _load_strategy(path: str | Path) -> dict:
    """Load YAML strategy file."""
    try:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load strategy: {e}")
        raise


def _normalize_strategy(strategy: dict) -> dict:
    """Normalize strategy to handle different formats."""
    
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
) -> TaskResult:
    """Execute a single task."""
    start_time = time.time()
    
    task_name = task.get("name", "Unnamed Task")
    description = task.get("description", "")
    task_type = task.get("task_type", "feature")
    model_hints = task.get("model_hints", {})
    
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
        
        # Execute
        with LlxClient(config) as client:
            response = client.chat(
                [ChatMessage(role="user", content=prompt)],
                model=model
            )
        
        return TaskResult(
            task_name=task_name,
            status="success",
            model_used=model,
            response=response.content,
            execution_time=time.time() - start_time
        )
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return TaskResult(
            task_name=task_name,
            status="failed",
            model_used=model or "unknown",
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
    
    prompt = f"""## Task: {task.get('name', 'Unnamed Task')}

Type: {task.get('task_type', 'feature')}
Priority: {task.get('priority', 'medium')}

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
    
    prompt += """
## Instructions
Execute this task considering the project metrics above. Provide:
1. Specific actions to take
2. File paths for any changes
3. Code examples if applicable
4. Verification steps

Focus on practical, actionable steps that improve the codebase.
"""
    
    return prompt
