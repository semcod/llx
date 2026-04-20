# Imports used in this function:
import os
import re
from pathlib import Path
import typer
from rich.panel import Panel
from llx.analysis.collector import ProjectMetrics, analyze_project
from llx.config import LlxConfig
from llx.routing.selector import SelectionResult, select_model
from llx.utils.issues import load_issue_source, build_fix_prompt

# Assuming these are imported elsewhere in the file
from rich.console import Console
console = Console()
from llx.utils.aider import _run_aider_fix, _format_aider_result, _extract_issue_files
from llx.utils.formatting import _format_selection, _format_metrics
try:
    from llx.prellm import preprocess_and_execute_sync
    PRELLM_AVAILABLE = True
except ImportError:
    PRELLM_AVAILABLE = False
    preprocess_and_execute_sync = None
from llx.utils.models import _select_small_model

# Neighboring function:
def apply_code_changes(workdir: Path, content: str) -> tuple[int, list[str]]:
    """Parse LLM response and apply changes to files.

    Supports four response formats (tried in order):
    1. JSON array of ``{"file": "...", "patch": "..."}`` objects
       (patches are unified diffs or full-file replacements)
    2. OpenAI ``*** Begin Patch`` / ``*** End Patch`` format
    3. Markdown code blocks with file paths in the header
    4. Code blocks with ``# File:`` / ``// File:`` comments

    Returns:
        Tuple of (number of changes applied, list of modified files)
    """
    changes_applied, modified_files = _apply_json_patch_strategy(workdir, content)
    if changes_applied > 0:
        return changes_applied, modified_files

    oa_changes, oa_files = _apply_openai_patch_strategy(workdir, content)
    if oa_changes > 0:
        return oa_changes, oa_files

    return _apply_markdown_code_block_strategy(workdir, content)


def load_errors_data(errors: str | None, console: Console) -> list | dict | None:
    """Load errors data from file if provided."""
    errors_data = None
    if errors:
        errors_path = Path(errors)
        if errors_path.exists():
            errors_data = load_issue_source(errors_path)
            if isinstance(errors_data, list):
                console.print(f"[green]✓[/green] Loaded {len(errors_data)} errors from {errors}")
            else:
                console.print(f"[green]✓[/green] Loaded errors from {errors}")
        else:
            console.print(f"[red]✗[/red] Errors file not found: {errors}")
            raise typer.Exit(1)
    return errors_data


def select_model_for_fix(model: str | None, metrics: ProjectMetrics, config: LlxConfig, console: Console) -> tuple[str, SelectionResult | None]:
    """Select the model for fixing based on flags, env, or metrics."""
    env_model = os.environ.get("LLM_MODEL")
    if model:
        selected_model_id = model
        selection: SelectionResult | None = None
    elif env_model:
        selected_model_id = env_model
        selection = None
    else:
        selection = select_model(metrics, config)
        selected_model_id = selection.model_id
    return selected_model_id, selection


def display_model_selection_and_metrics(selection: SelectionResult | None, selected_model_id: str, metrics: ProjectMetrics, console: Console) -> None:
    """Display model selection and project metrics."""
    console.print("\n[bold]Model Selection:[/bold]")
    console.print(Panel(_format_selection(selection, selected_model_id), border_style="green"))
    console.print(Panel(_format_metrics(metrics), title="Project Metrics", border_style="blue"))


def prepare_fix_prompt(workdir_path: Path, errors_data: list | dict | None, selected_model_id: str, selection: SelectionResult | None) -> str:
    """Prepare the fix prompt with issues and analysis."""
    issues_for_prompt = errors_data if errors_data is not None else []
    analysis = {
        "selection": {
            "model_id": selected_model_id,
            "tier": selection.tier.value if selection else "forced",
        }
    } if selected_model_id else None
    prompt = build_fix_prompt(workdir_path, issues_for_prompt, analysis=analysis)
    return prompt


def handle_dry_run(prompt: str, console: Console) -> None:
    """Handle dry run by printing the prompt."""
    console.print("\n[bold]Dry run - would execute:[/bold]")
    console.print(Panel(prompt, title="Fix Prompt", border_style="blue"))


def execute_aider_fix(workdir_path: Path, prompt: str, selected_model_id: str, issues_for_prompt: list | dict | None, config: LlxConfig, apply: bool, verbose: bool, console: Console) -> None:
    """Execute fix using Aider."""
    if verbose:
        console.print("\n[bold]Generating fixes with Aider...[/bold]")

    aider_files = _extract_issue_files(issues_for_prompt)
    if verbose and aider_files:
        console.print(f"[dim]Target files:[/dim] {', '.join(aider_files)}")

    aider_result = _run_aider_fix(
        workdir=workdir_path,
        prompt=prompt,
        model=selected_model_id,
        files=aider_files,
        use_docker=config.run_env == "docker",
    )

    console.print("\n[bold]Aider result:[/bold]")
    console.print(
        Panel(
            _format_aider_result(aider_result),
            title="Aider Output",
            border_style="green" if aider_result.get("success") else "red",
        )
    )

    if not aider_result.get("success"):
        raise typer.Exit(1)

    if apply:
        console.print("\n[green]✓[/green] Aider applied changes directly.")


def execute_prellm_fix(workdir_path: Path, prompt: str, selected_model_id: str, config: LlxConfig, apply: bool, verbose: bool, console: Console) -> None:
    """Execute fix using preLLM."""
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
            changes, files = apply_code_changes(workdir_path, result.content)
            if changes > 0:
                console.print(f"\n[green]✓[/green] Applied {changes} changes to {len(files)} files: {', '.join(files)}")
            else:
                console.print("\n[yellow]![/yellow] No code changes could be auto-applied. Manual review needed.")

    except Exception as e:
        console.print(f"[red]✗[/red] Error generating fixes: {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


# Function to refactor:
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

    errors_data = load_errors_data(errors, console)

    # Analyze project metrics
    if verbose:
        console.print("\n[bold]Analyzing project metrics...[/bold]")

    metrics = analyze_project(workdir_path)
    config = LlxConfig.load(workdir_path)

    selected_model_id, selection = select_model_for_fix(model, metrics, config, console)

    display_model_selection_and_metrics(selection, selected_model_id, metrics, console)

    prompt = prepare_fix_prompt(workdir_path, errors_data, selected_model_id, selection)

    if dry_run:
        handle_dry_run(prompt, console)
        return

    if config.code_tool == "aider":
        execute_aider_fix(workdir_path, prompt, selected_model_id, errors_data, config, apply, verbose, console)
        return

    execute_prellm_fix(workdir_path, prompt, selected_model_id, config, apply, verbose, console)


# [context truncated for length]