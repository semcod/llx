"""LLX fix command for pyqual integration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from llx.analysis.collector import ProjectMetrics, analyze_project
from llx.config import LlxConfig
from llx.routing.selector import SelectionResult, select_model
from llx.utils.issues import load_issue_source, build_fix_prompt

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
            errors_data = load_issue_source(errors_path)
            if isinstance(errors_data, list):
                console.print(f"[green]✓[/green] Loaded {len(errors_data)} errors from {errors}")
            else:
                console.print(f"[green]✓[/green] Loaded errors from {errors}")
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
    issues_for_prompt = errors_data if errors_data is not None else []
    prompt = build_fix_prompt(workdir_path, issues_for_prompt)

    if dry_run:
        console.print("\n[bold]Dry run - would execute:[/bold]")
        console.print(Panel(prompt, title="Fix Prompt", border_style="blue"))
        return

    if config.code_tool == "aider":
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



def _extract_issue_files(issues: dict[str, Any] | list[dict[str, Any]] | list[Any]) -> list[str]:
    """Return the unique file paths referenced by issues."""
    if isinstance(issues, dict):
        issue_items: list[Any] = [issues]
    else:
        issue_items = list(issues)

    files: list[str] = []
    seen: set[str] = set()
    for issue in issue_items:
        if not isinstance(issue, dict):
            continue
        location = issue.get("file") or issue.get("path")
        if not location:
            continue
        path = str(location)
        if path in seen:
            continue
        seen.add(path)
        files.append(path)
    return files


def _run_aider_fix(
    workdir: Path,
    prompt: str,
    model: str,
    files: list[str] | None = None,
    use_docker: bool = False,
    docker_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run aider directly, mirroring the MCP tool behaviour."""
    docker_args = docker_args or []

    if use_docker:
        docker_cmd = ["docker", "run", "--rm", "-v", f"{workdir.absolute()}:/workspace"]

        if docker_args:
            docker_cmd.extend(docker_args)

        if "--network" not in " ".join(docker_args):
            docker_cmd.extend(["--network", "host"])

        docker_cmd.extend([
            "-e",
            "OLLAMA_API_BASE=http://172.17.0.1:11434",
            "paulgauthier/aider",
            "--model",
            model.replace("ollama/", "ollama_chat/"),
            "--message",
            prompt,
        ])

        if files:
            docker_cmd.extend([f"/workspace/{f}" for f in files])

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(docker_cmd),
                "path": str(workdir),
                "method": "docker",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Aider Docker command timed out after 5 minutes",
                "command": " ".join(docker_cmd),
            }
        except FileNotFoundError:
            pass
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "command": " ".join(docker_cmd),
            }

    cmd = ["aider", "--model", model, "--message", prompt]

    if files:
        cmd.extend(files)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd),
            "path": str(workdir),
            "method": "local",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Aider command timed out after 5 minutes",
            "command": " ".join(cmd),
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Aider not found. Install with: pip install aider-chat, or use Docker with use_docker=true",
            "command": " ".join(cmd),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "command": " ".join(cmd),
        }


def _format_aider_result(result: dict[str, Any]) -> str:
    """Render aider output for the console."""
    lines = [
        f"Success: {result.get('success')}",
        f"Method: {result.get('method', 'unknown')}",
    ]

    command = result.get("command")
    if command:
        lines.append(f"Command: {command}")

    stdout = (result.get("stdout") or "").strip()
    if stdout:
        lines.extend(["", "STDOUT:", stdout])

    stderr = (result.get("stderr") or "").strip()
    if stderr:
        lines.extend(["", "STDERR:", stderr])

    error = (result.get("error") or "").strip()
    if error:
        lines.extend(["", "ERROR:", error])

    path = result.get("path")
    if path:
        lines.extend(["", f"Path: {path}"])

    return "\n".join(lines).strip()


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



if __name__ == "__main__":
    app()
