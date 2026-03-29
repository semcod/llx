"""LLX fix command for pyqual integration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llx.analysis.collector import analyze_project, ProjectMetrics
from llx.routing.selector import select_model, SelectionResult
from llx.cli.formatters import format_selection

# Import preLLM if available
try:
    from llx.prellm.core import preprocess_and_execute
    PRELLM_AVAILABLE = True
except ImportError:
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
            errors_data = json.loads(errors_path.read_text())
            console.print(f"[green]✓[/green] Loaded {len(errors_data)} errors from {errors}")
        else:
            console.print(f"[red]✗[/red] Errors file not found: {errors}")
            raise typer.Exit(1)
    
    # Analyze project metrics
    if verbose:
        console.print("\n[bold]Analyzing project metrics...[/bold]")
    
    metrics = analyze_project(str(workdir_path))
    
    # Select model based on metrics
    if model:
        # Force specific model
        selection = SelectionResult(
            model_id=model,
            tier="forced",
            reason=f"User forced model: {model}",
            confidence=1.0,
            metrics=metrics
        )
    else:
        selection = select_model(metrics)
    
    console.print("\n[bold]Model Selection:[/bold]")
    console.print(format_selection(selection))
    
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
        result = preprocess_and_execute(
            query=prompt,
            small_llm=None,  # Let preLLM select based on config
            large_llm=selection.model_id,
            workdir=str(workdir_path),
        )
        
        console.print("\n[bold]Generated fixes:[/bold]")
        console.print(Panel(result.response, title="LLM Response", border_style="green"))
        
        if apply and result.response:
            # Apply fixes (simplified - in real implementation would parse and apply)
            console.print("\n[yellow]![/yellow] Auto-apply not implemented yet. Please apply manually.")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error generating fixes: {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def _prepare_fix_prompt(workdir: Path, errors_data: list[dict] | None, metrics: ProjectMetrics) -> str:
    """Prepare fix prompt based on errors and metrics."""
    
    prompt_parts = [
        f"Fix code issues in project at {workdir.name}",
        f"\nProject metrics:",
        f"- Files: {metrics.files}",
        f"- Lines: {metrics.lines:,}",
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
