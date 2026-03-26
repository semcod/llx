"""Execute tasks from a planfile strategy.yaml.

For each task:
1. Read task definition (type, description, model_hints)
2. Select model using llx.routing.selector + task model_hints
3. Build context from code2llm analysis
4. Send to LLM for execution
5. Validate result with vallm (if available)
6. Report status back to planfile/proxym
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Any, List, Optional

import yaml

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage
from llx.analysis.collector import ProjectMetrics, analyze_project


@dataclass
class TaskResult:
    task_name: str
    status: str  # "success" | "failed" | "skipped" | "dry_run"
    model_used: str
    response: str
    validated: bool = False
    validation_score: float = 0.0
    error: Optional[str] = None


def execute_strategy(
    strategy_path: str | Path,
    project_path: str | Path = ".",
    *,
    sprint_filter: str | None = None,
    dry_run: bool = False,
    on_progress: Any = None,
) -> List[TaskResult]:
    """Execute all tasks in a strategy.yaml."""
    strategy = _load_strategy(strategy_path)
    config = LlxConfig.load(str(project_path))
    metrics = analyze_project(str(project_path))
    results = []

    for sprint in strategy.get("sprints", []):
        if sprint_filter and sprint.get("id") != sprint_filter:
            continue

        for task in sprint.get("task_patterns", []):
            if on_progress:
                on_progress(f"Executing: {task['name']}")

            result = _execute_task(task, project_path, config, metrics, dry_run)
            results.append(result)

    return results


def _execute_task(
    task: dict,
    project_path: Path,
    config: LlxConfig,
    metrics: ProjectMetrics,
    dry_run: bool,
) -> TaskResult:
    """Execute a single task from the strategy."""
    task_name = task.get("name", "unnamed")
    description = task.get("description", "")
    model_hints = task.get("model_hints", {})

    try:
        # Select model based on hints + project metrics
        model = _select_model_for_task(task, config, metrics)

        if dry_run:
            return TaskResult(
                task_name=task_name,
                status="dry_run",
                model_used=model,
                response="",
            )

        # Build prompt
        prompt = _build_task_prompt(task, metrics)

        # Execute via LLM
        with LlxClient(config) as client:
            response = client.chat(
                [ChatMessage(role="user", content=prompt)],
                model=model,
            )

        # Validate if vallm available
        validated, score = _validate_result(response.content, task)

        return TaskResult(
            task_name=task_name,
            status="success",
            model_used=model,
            response=response.content,
            validated=validated,
            validation_score=score,
        )
    except Exception as e:
        return TaskResult(
            task_name=task_name,
            status="failed",
            model_used="",
            response="",
            error=str(e),
        )


def _select_model_for_task(task: dict, config: LlxConfig, metrics: ProjectMetrics) -> str:
    """Select model using task hints + project metrics."""
    # Import here to avoid circular imports
    from llx.routing.selector import select_model

    hints = task.get("model_hints", {})
    phase = "implementation"  # default phase

    # Map hint tier to llx ModelTier
    tier_hint = hints.get(phase, "balanced")
    tier_map = {
        "premium": "premium",
        "balanced": "balanced",
        "cheap": "cheap",
        "local": "local",
    }
    preferred_tier = tier_map.get(tier_hint, "balanced")

    # Use llx selector with metrics-aware override
    result = select_model(metrics, config, task_hint=task.get("task_type"))

    # Honor hint if it requests a higher tier than metrics suggest
    if preferred_tier == "premium":
        model = config.models.get("premium")
        if model:
            return model.model_id

    return result.model_id


def _build_task_prompt(task: dict, metrics: ProjectMetrics) -> str:
    """Build execution prompt from task definition."""
    return f"""## Task: {task.get('name', '')}

**Type:** {task.get('task_type', 'refactor')}
**Description:** {task.get('description', '')}

## Project Context
- Files: {metrics.total_files}, Lines: {metrics.total_lines:,}
- CC̄: {metrics.avg_cc:.1f}, Max CC: {metrics.max_cc}
- Critical functions: {metrics.critical_count}
- God modules: {metrics.god_modules}

## Instructions
Execute this task. Provide:
1. Specific file changes (with paths)
2. Code snippets for each change
3. Verification steps
"""


def _validate_result(response: str, task: dict) -> tuple[bool, float]:
    """Validate task result with vallm if available."""
    try:
        from vallm import Proposal, validate
        # Extract code from response
        code_blocks = []
        if "```python" in response:
            for block in response.split("```python")[1:]:
                code_blocks.append(block.split("```")[0])
        if not code_blocks:
            return False, 0.0
        proposal = Proposal(code=code_blocks[0], language="python")
        result = validate(proposal)
        return result.verdict.value == "pass", result.weighted_score
    except ImportError:
        return False, 0.0
    except Exception:
        return False, 0.0


def _load_strategy(path: str | Path) -> dict:
    """Load strategy.yaml file."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
