"""LLX fix command for pyqual integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from llx.analysis.collector import ProjectMetrics, analyze_project
from llx.config import LlxConfig
from llx.routing.selector import SelectionResult, select_model

# Import preLLM if available
try:
    from llx.prellm.core import preprocess_and_execute_sync
    PRELLM_AVAILABLE = True
except ImportError:
    preprocess_and_execute_sync = None
    PRELLM_AVAILABLE = False

app = typer.Typer(help="LLX fix command for pyqual integration")
console = Console()


@app.command()
def fix(
    workdir: str = typer.Argument(".", help="Working directory"),
    errors: str = typer.Option(None, "--errors", "-e", help="Path to errors JSON file"),
    apply: bool = typer.Option(False, "--apply", help="Apply fixes automatically"),
    model: str = typer.Option(None, "--model", "-m", help="Force specific model"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Fix code issues using LLX-driven model selection."""
    workdir_path = Path(workdir).resolve()

    # Load errors if provided
    errors_data = None
    if errors:
        errors_path = Path(errors)
        if errors_path.exists():
            errors_data = _load_errors(errors_path)
            console.print(f"[green]✓[/green] Loaded {len(errors_data)} errors from {errors}")
        else:
            console.print(f"[red]✗[/red] Errors file not found: {errors}")
            raise typer.Exit(1)

    # Analyze project metrics
    if verbose:
        console.print("\n[bold]Analyzing project metrics...[/bold]")

    metrics = analyze_project(workdir_path)
    config = LlxConfig.load(workdir_path)

    # Select model based on metrics
    if model:
        selected_model_id = model
        selection: SelectionResult | None = None
    else:
        selection = select_model(metrics, config)
        selected_model_id = selection.model_id

    console.print("\n[bold]Model Selection:[/bold]")
    console.print(Panel(_format_selection(selection, selected_model_id), border_style="green"))

    console.print(Panel(_format_metrics(metrics), title="Project Metrics", border_style="blue"))

    # Prepare fix prompt
    prompt = _prepare_fix_prompt(workdir_path, errors_data, metrics)

    if dry_run:
        console.print("\n[bold]Dry run - would execute:[/bold]")
        console.print(Panel(prompt, title="Fix Prompt", border_style="blue"))
        return

    # Execute fix using preLLM if available
    if not PRELLM_AVAILABLE:
        console.print("[red]✗[/red] preLLM not available. Install with: pip install llx[prellm]")
        raise typer.Exit(1)

    if verbose:
        console.print("\n[bold]Generating fixes...[/bold]")

    try:
        # Use preLLM's two-agent pipeline
        result = preprocess_and_execute_sync(
            query=prompt,
            small_llm=_select_small_model(config),
            large_llm=selected_model_id,
            strategy="auto",
            codebase_path=str(workdir_path),
            collect_runtime=True,
            sanitize=True,
        )

        console.print("\n[bold]Generated fixes:[/bold]")
        console.print(Panel(result.content, title="LLM Response", border_style="green"))

        if apply and result.content:
            # Apply fixes (simplified - in real implementation would parse and apply)
            console.print("\n[yellow]![/yellow] Auto-apply not implemented yet. Please apply manually.")

    except Exception as e:
        console.print(f"[red]✗[/red] Error generating fixes: {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def _load_errors(errors_path: Path) -> list[dict[str, Any]]:
    """Load error entries from JSON and normalize common shapes."""
    raw = json.loads(errors_path.read_text())
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        for key in ("errors", "results", "issues"):
            value = raw.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _select_small_model(config: LlxConfig) -> str:
    """Choose a smaller model for the preLLM preprocessing step."""
    for tier_name in ("cheap", "free", config.default_tier):
        model = config.models.get(tier_name)
        if model:
            return model.model_id
    return next(iter(config.models.values())).model_id


def _format_selection(selection: SelectionResult | None, selected_model_id: str) -> str:
    """Render a short selection summary."""
    if selection is None:
        return f"Forced model: [bold]{selected_model_id}[/bold]"
    return selection.explain()


def _format_metrics(metrics: ProjectMetrics) -> str:
    """Render the most useful project metrics for the operator."""
    lines = [
        f"Files: {metrics.total_files}",
        f"Lines: {metrics.total_lines:,}",
        f"Functions: {metrics.total_functions}",
        f"Classes: {metrics.total_classes}",
        f"Modules: {metrics.total_modules}",
        f"CC̄: {metrics.avg_cc:.1f}",
        f"Max CC: {metrics.max_cc}",
        f"Critical: {metrics.critical_count}",
        f"Fan-out: {metrics.max_fan_out}",
        f"Fan-in: {metrics.max_fan_in}",
        f"Cycles: {metrics.dependency_cycles}",
        f"Dup groups: {metrics.dup_groups}",
        f"Dup saved lines: {metrics.dup_saved_lines}",
        f"Scope: {metrics.task_scope}",
        f"Est. tokens: ~{metrics.estimated_context_tokens:,}",
    ]
    return "\n".join(lines)


def _prepare_fix_prompt(workdir: Path, errors_data: list[dict] | None, metrics: ProjectMetrics) -> str:
    """Prepare fix prompt based on errors and metrics."""
    prompt_parts = [
        f"Fix code issues in project at {workdir.name}",
        f"\nProject metrics:",
        f"- Files: {metrics.total_files}",
        f"- Lines: {metrics.total_lines:,}",
        f"- Average CC: {metrics.avg_cc:.1f}",
        f"- Max CC: {metrics.max_cc}",
    ]

    if errors_data:
        prompt_parts.append(f"\nFound {len(errors_data)} errors:")
        for i, error in enumerate(errors_data[:5]):  # Show first 5 errors
            prompt_parts.append(
                f"\n{i+1}. {error.get('file', 'unknown')}:"
                f" {error.get('message', 'no message')}"
                f" (line {error.get('line', '?')})"
            )
        if len(errors_data) > 5:
            prompt_parts.append(f"\n... and {len(errors_data) - 5} more errors")
    
    prompt_parts.extend([
        "\nPlease provide specific code fixes for these issues.",
        "Focus on reducing cyclomatic complexity and fixing validation errors.",
        "Return the fixes in a clear format with file paths and line numbers."
    ])

    return "\n".join(prompt_parts)


if __name__ == "__main__":
    app()
