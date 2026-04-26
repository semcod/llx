"""llx CLI — Intelligent LLM model router driven by code metrics.

Commands:
    llx analyze <path>     Analyze project and recommend model
    llx select <path>      Quick model selection
    llx chat <path>        Analyze + send prompt to selected model
    llx proxy start        Start LiteLLM proxy
    llx proxy config       Generate proxy configuration
    llx proxy status       Check proxy status
    llx info               Show tools and models
    llx init               Initialize llx.toml
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Tuple, Any
import os
import time
import yaml as _yaml
import re
import logging

import typer
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from llx.analysis.collector import analyze_project
from llx.config import LlxConfig
from llx.routing.selector import ModelTier, select_model, select_with_context_check
from llx.cli.strategy_commands import strategy_app
from llx.planfile.model_selector import ModelSelector, FREE_FILTER, CHEAP_FILTER, BALANCED_FILTER, LOCAL_FILTER
from llx.routing.client import LlxClient, ChatMessage

console = Console()
app = typer.Typer(name="llx", help="Intelligent LLM model router driven by real code metrics.", no_args_is_help=True)
proxy_app = typer.Typer(help="Manage LiteLLM proxy server.")
mcp_app = typer.Typer(help="MCP server management.")
plan_app = typer.Typer(help="planfile strategy management.")
app.add_typer(proxy_app, name="proxy")
app.add_typer(mcp_app, name="mcp")
app.add_typer(plan_app, name="plan")
app.add_typer(strategy_app, name="strategy")


def _show_version_banner() -> None:
    """Show version banner if update is available."""
    try:
        from llx.cli.version_check import check_version, get_update_command
        outdated = check_version()
        if outdated:
            current, latest = outdated
            update_cmd = get_update_command()
            console.print(
                Panel(
                    f"[yellow]⚠ Update available:[/yellow] llx {current} → {latest}\n\n"
                    f"Run: [cyan]{update_cmd}[/cyan]",
                    title="Version Check",
                    border_style="yellow"
                )
            )
    except Exception:
        # Silently fail if version check fails
        pass


# Show version banner on app load
_show_version_banner()


def _run_analysis_tools(project_path: Path, config: LlxConfig) -> None:
    """Run code2llm/redup/vallm analysis tools."""
    from llx.analysis.runner import run_all_tools
    output_dir = project_path / ".llx"

    def on_progress(tool: str, status: str) -> None:
        if status == "starting":
            console.print(f"  Running {tool}...", end=" ")
        else:
            console.print(f"[{'green' if 'done' in status else 'yellow'}]{status}[/]")

    run_all_tools(project_path, output_dir, on_progress=on_progress)


@app.command()
def analyze(
    path: str = typer.Argument(".", help="Project path to analyze"),
    toon_dir: Optional[str] = typer.Option(None, "--toon-dir", "-t", help="Directory with .toon files"),
    task: Optional[str] = typer.Option(None, "--task", help="Task hint: refactor, explain, quick_fix, review"),
    local: bool = typer.Option(False, "--local", "-l", help="Force local model"),
    max_tier: Optional[str] = typer.Option(None, "--max-tier", help="Max tier: free, cheap, balanced, premium"),
    run_tools: bool = typer.Option(False, "--run", "-r", help="Run code2llm/redup/vallm first"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Analyze a project and recommend the optimal LLM model."""
    from llx.cli.formatters import output_json, output_rich
    project_path = Path(path).resolve()
    config = LlxConfig.load(project_path)
    config.verbose = config.verbose or verbose

    if run_tools:
        _run_analysis_tools(project_path, config)

    with console.status("Collecting project metrics..."):
        metrics = analyze_project(project_path, toon_dir=toon_dir)

    tier_limit = ModelTier(max_tier) if max_tier else None
    result = select_with_context_check(metrics, config, prefer_local=local, max_tier=tier_limit, task_hint=task)

    if json_output:
        output_json(metrics, result)
    else:
        output_rich(metrics, result, verbose)


@app.command()
def select(
    path: str = typer.Argument(".", help="Project path"),
    toon_dir: Optional[str] = typer.Option(None, "--toon-dir", "-t"),
    task: Optional[str] = typer.Option(None, "--task"),
    local: bool = typer.Option(False, "--local", "-l"),
) -> None:
    """Quick model selection from existing analysis files."""
    project_path = Path(path).resolve()
    config = LlxConfig.load(project_path)
    metrics = analyze_project(project_path, toon_dir=toon_dir)
    result = select_model(metrics, config, prefer_local=local, task_hint=task)
    console.print(f"[bold green]{result.model_id}[/bold green]  ({result.tier.value})")
    for reason in result.reasons[:5]:
        console.print(f"  [dim]• {reason}[/dim]")


def _resolve_chat_model(config: LlxConfig, model_override: Optional[str], result) -> str:
    """Resolve final model id from override and selection result."""
    model_id = model_override or result.model_id
    if model_override and model_override in config.models:
        return config.models[model_override].model_id
    return model_id


@app.command()
def chat(
    path: str = typer.Argument(".", help="Project path"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt to send"),
    toon_dir: Optional[str] = typer.Option(None, "--toon-dir", "-t"),
    task: Optional[str] = typer.Option(None, "--task"),
    model_override: Optional[str] = typer.Option(None, "--model", "-m"),
    local: bool = typer.Option(False, "--local", "-l"),
    free: bool = typer.Option(False, "--free", "-f", help="Force free-tier model"),
) -> None:
    """Analyze project, select model, and send a prompt."""
    project_path = Path(path).resolve()
    config = LlxConfig.load(project_path)
    metrics = analyze_project(project_path, toon_dir=toon_dir)

    if free:
        result = select_with_context_check(metrics, config, prefer_local=local, task_hint=task, force_tier=ModelTier.FREE)
    else:
        result = select_with_context_check(metrics, config, prefer_local=local, task_hint=task)

    model_id = _resolve_chat_model(config, model_override, result)
    console.print(f"[bold]Model:[/bold] {model_id}  [dim]({result.tier.value})[/dim]")

    from llx.integrations.context_builder import build_context
    context = build_context(project_path, metrics, result.tier)

    with LlxClient(config) as client:
        with console.status(f"Querying {model_id}..."):
            response = client.chat_with_context(prompt, context, model=model_id)
    console.print(Panel(response.content, title="Response", border_style="green"))
    console.print(f"[dim]Tokens: {response.prompt_tokens:,} in → {response.completion_tokens:,} out[/dim]")


@proxy_app.command("start")
def proxy_start(
    config_path: Optional[str] = typer.Option(None, "--config", "-c"),
    port: int = typer.Option(4000, "--port", "-p"),
    background: bool = typer.Option(True, "--bg/--fg"),
) -> None:
    """Start LiteLLM proxy server with llx configuration."""
    from llx.integrations.proxy import start_proxy
    config = LlxConfig.load(".")
    config.proxy.port = port
    conf = Path(config_path) if config_path else None
    console.print(f"Starting LiteLLM proxy on :{port}...")
    try:
        proc = start_proxy(config, config_path=conf, background=background)
        if proc:
            console.print(f"[green]Proxy running (PID {proc.pid})[/green]")
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@proxy_app.command("config")
def proxy_config(output: str = typer.Option("litellm_config.yaml", "--output", "-o")) -> None:
    """Generate LiteLLM proxy config."""
    from llx.integrations.proxy import generate_proxy_config
    config = LlxConfig.load(".")
    generate_proxy_config(config, Path(output))
    console.print(f"[green]Config written to {output}[/green]")


@proxy_app.command("status")
def proxy_status() -> None:
    """Check if proxy is running."""
    from llx.integrations.proxy import check_proxy
    config = LlxConfig.load(".")
    running = check_proxy(config.litellm_base_url)
    icon = "[green]✓[/green]" if running else "[red]✗[/red]"
    console.print(f"{icon} Proxy at {config.litellm_base_url}")


@mcp_app.command("start")
def mcp_start(
    mode: str = typer.Option("stdio", help="Server mode: stdio or sse"),
    port: int = typer.Option(8000, help="Port for SSE mode"),
) -> None:
    """Start the llx MCP server."""
    from llx.mcp.server import main as mcp_main

    console.print(f"Starting llx MCP server ({mode} mode)...")
    if mode == "sse":
        console.print(f"[green]SSE endpoint:[/green] http://localhost:{port}/sse")
        mcp_main(["--sse", "--port", str(port)])
        return
    mcp_main([])


@plan_app.command("generate")
def plan_generate(
    strategy: str = typer.Argument(..., help="Strategy YAML file"),
    output_dir: Path = typer.Option(Path("generated"), "--output", "-o"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Generate code from strategy."""
    _plan_code_impl(strategy, output_dir, model, profile)


@plan_app.command("review")
def plan_review(
    strategy: str = typer.Argument(..., help="Strategy YAML file"),
    project_path: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Review strategy against project."""
    from llx.planfile import load_valid_strategy
    try:
        strat = load_valid_strategy(strategy)
        console.print(f"[green]✓[/green] Strategy '{strat.name}' loaded successfully")
        console.print(f"  Sprints: {len(strat.sprints)}")
        console.print(f"  Quality gates: {len(strat.quality_gates)}")
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@plan_app.command("execute")
def plan_execute(
    strategy: str = typer.Argument(..., help="Strategy YAML file"),
    project_path: Path = typer.Option(Path("."), "--project", "-p"),
    backend: str = typer.Option("github", "--backend", "-b"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Execute strategy to create tickets."""
    from llx.planfile import run_strategy
    console.print(f"[bold]Executing strategy:[/bold] {strategy}")
    run_strategy(
        strategy_path=strategy,
        project_path=str(project_path),
        backend=backend,
        dry_run=dry_run
    )


def _print_run_params(strategy: str, project_path: Path, ticket_id: Optional[str], sprint: Optional[int], tier: Optional[str], dry_run: bool, use_aider: bool, console: Console) -> Any:
    """Print plan_run parameter summary and detect backends if needed."""
    console.print(f"[bold]Running planfile:[/bold] {strategy}")
    console.print(f"[dim]Project:[/dim] {project_path}")
    if ticket_id:
        console.print(f"[dim]Ticket:[/dim] {ticket_id}")
    if sprint:
        console.print(f"[dim]Sprint:[/dim] {sprint}")
    if tier:
        console.print(f"[dim]Tier:[/dim] {tier}")
    if dry_run:
        console.print(f"[dim]Mode:[/dim] dry-run")
    if use_aider:
        console.print(f"[dim]Code editing:[/dim] auto-detecting backend...")
        from llx.planfile.executor_simple import _detect_available_backends
        backends = _detect_available_backends()
        available = [k for k, v in backends.items() if v]
        console.print(f"[dim]Available backends:[/dim] {', '.join(available)}")
        return backends
    return None


def _ensure_proxy_running(config: LlxConfig, dry_run: bool, auto_start_proxy: bool, console: Console) -> None:
    """Auto-start proxy if not running (unless dry-run or disabled)."""
    if dry_run or not auto_start_proxy:
        return
    from llx.integrations.proxy import check_proxy, start_proxy
    proxy_url = config.litellm_base_url
    if check_proxy(proxy_url):
        return
    console.print(f"[yellow]⚠ LiteLLM proxy not running at {proxy_url}[/yellow]")
    console.print("[dim]Attempting to start proxy automatically...[/dim]")
    try:
        proc = start_proxy(config, background=True)
        if proc:
            console.print(f"[green]✓ Proxy started (PID {proc.pid})[/green]")
        else:
            console.print("[red]✗ Failed to start proxy[/red]")
            console.print(f"[dim]Run manually: llx proxy start[/dim]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Failed to start proxy: {e}[/red]")
        console.print(f"[dim]Run manually: llx proxy start[/dim]")
        raise typer.Exit(1)


def _resolve_tier_override(tier: Optional[str], config: LlxConfig, console: Console) -> Optional[str]:
    """Map tier alias to model override id."""
    if not tier:
        return None
    tier_aliases = {
        "balance": "balanced",
        "free": "free",
        "cheap": "cheap",
        "premium": "premium",
        "local": "local",
        "openrouter": "openrouter",
    }
    normalized = tier_aliases.get(tier, tier)
    tier_model = config.models.get(normalized)
    if tier_model:
        console.print(f"[dim]Model:[/dim] {tier_model.model_id}")
        return tier_model.model_id
    console.print(f"[yellow]Warning:[/yellow] Tier '{tier}' not found in config")
    return None


def _persist_failed_results(results, strategy: str) -> None:
    """Update planfile for no_changes/failed tasks so state is persisted."""
    from llx.planfile.executor.strategy import _update_task_in_planfile
    for result in results:
        if result.status in ("no_changes", "failed"):
            comment = f"Task {result.status}: {result.validation_message or result.error or 'no details'}"
            updated = False
            if result.ticket_id:
                updated = _update_task_in_planfile(
                    planfile_path=strategy,
                    task_id=result.ticket_id,
                    status=result.status,
                    comment=comment,
                )

            if not updated:
                _update_task_in_planfile(
                    planfile_path=strategy,
                    task_id=result.task_name,
                    status=result.status,
                    comment=comment,
                )


def _print_results_summary(results, use_aider: bool, backends, console: Console) -> None:
    """Print execution summary counts and validation details."""
    console.print("\n[bold]Results:[/bold]")
    if use_aider and backends:
        from llx.planfile.executor_simple import _select_best_backend
        selected = _select_best_backend(backends)
        console.print(f"[dim]Backend used:[/dim] {selected}")

    counts = {
        "success": sum(1 for r in results if r.status == "success"),
        "failed": sum(1 for r in results if r.status == "failed"),
        "invalid": sum(1 for r in results if r.status == "invalid"),
        "not_found": sum(1 for r in results if r.status == "not_found"),
        "already_fixed": sum(1 for r in results if r.status == "already_fixed"),
        "no_changes": sum(1 for r in results if r.status == "no_changes"),
        "skipped": sum(1 for r in results if r.status in ["dry_run", "skipped"]),
    }

    console.print(f"  [green]✓ Success:[/green] {counts['success']}")
    console.print(f"  [red]✗ Failed:[/red] {counts['failed']}")
    console.print(f"  [yellow]⚠ Invalid (no changes):[/yellow] {counts['invalid']}")
    console.print(f"  [dim]⊘ Not found:[/dim] {counts['not_found']}")
    console.print(f"  [dim]⊘ Already fixed:[/dim] {counts['already_fixed']}")
    console.print(f"  [cyan]⊘ No changes needed:[/cyan] {counts['no_changes']}")
    console.print(f"  [dim]⊘ Skipped:[/dim] {counts['skipped']}")

    detail_statuses = {"invalid", "not_found", "already_fixed", "no_changes"}
    detail_colors = {
        "invalid": ("yellow", "⚠"),
        "not_found": ("dim", "⊘"),
        "already_fixed": ("dim", "⊘"),
        "no_changes": ("cyan", "⊘"),
    }
    if any(counts[s] > 0 for s in detail_statuses):
        console.print("\n[dim]Validation details:[/dim]")
        for result in results:
            if result.status in detail_statuses:
                color, icon = detail_colors[result.status]
                label = result.task_name
                if result.ticket_id:
                    label = f"{result.ticket_id} ({result.task_name})" if result.ticket_id != result.task_name else result.ticket_id
                console.print(f"  [{color}]{icon} {label}:[/{color}] {result.validation_message}")

    if counts["failed"] > 0:
        console.print("\n[dim]Failed tasks:[/dim]")
        for result in results:
            if result.status == "failed":
                label = result.task_name
                if result.ticket_id:
                    label = f"{result.ticket_id} ({result.task_name})" if result.ticket_id != result.task_name else result.ticket_id
                console.print(f"    [red]✗ {label}:[/red] {result.error}")


def _build_results_payload(
    results,
    strategy: str,
    project_path: Path,
    sprint: Optional[int],
    ticket_id: Optional[str],
    tier: Optional[str],
    dry_run: bool,
) -> dict[str, Any]:
    """Build structured YAML payload for plan run output."""
    counts = {
        "success": sum(1 for r in results if r.status == "success"),
        "failed": sum(1 for r in results if r.status == "failed"),
        "invalid": sum(1 for r in results if r.status == "invalid"),
        "not_found": sum(1 for r in results if r.status == "not_found"),
        "already_fixed": sum(1 for r in results if r.status == "already_fixed"),
        "cancelled": sum(1 for r in results if r.status == "cancelled"),
        "skipped": sum(1 for r in results if r.status in ["dry_run", "skipped"]),
    }

    return {
        "strategy": strategy,
        "project": str(project_path),
        "sprint": sprint,
        "ticket_id": ticket_id,
        "tier": tier,
        "dry_run": dry_run,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {**counts, "total": len(results)},
        "results": [
            {
                "ticket_id": r.ticket_id,
                "task_name": r.task_name,
                "status": r.status,
                "model_used": r.model_used,
                "response": r.response,
                "error": r.error,
                "execution_time": r.execution_time,
                "file_changed": r.file_changed,
                "validation_message": r.validation_message,
            }
            for r in results
        ],
    }


def _sync_todo_from_planfile(strategy: str, project_path: Path, results, dry_run: bool, console: Console) -> None:
    """Sync TODO.md checkboxes using planfile reusable API when enabled in config."""
    if dry_run:
        return

    try:
        import planfile as _planfile
    except Exception:
        return

    sync_func = getattr(_planfile, "sync_todo_checkboxes_from_planfile", None)
    if not callable(sync_func):
        return

    try:
        report = sync_func(
            strategy_path=strategy,
            project_path=str(project_path),
            results=results,
        )
    except Exception as e:
        console.print(f"[dim]TODO sync skipped:[/dim] {e}")
        return

    if not isinstance(report, dict) or not report.get("enabled"):
        return

    updated = int(report.get("updated") or 0)
    todo_path = report.get("todo_path") or "TODO.md"
    if updated > 0:
        console.print(f"[dim]TODO sync:[/dim] updated {updated} checkbox(es) in {todo_path}")
    else:
        console.print(f"[dim]TODO sync:[/dim] enabled, no checkbox updates ({todo_path})")


def _save_results_yaml(payload: dict[str, Any], output_yaml: str, console: Console) -> None:
    """Save execution results payload to a YAML file."""
    with open(output_yaml, "w", encoding="utf-8") as f:
        _yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
    console.print(f"\n[dim]Results saved to:[/dim] {output_yaml}")


@plan_app.command("run")
def plan_run(
    strategy: str = typer.Argument(..., help="Strategy YAML file (or 'planfile.yaml')"),
    project_path: Path = typer.Option(Path("."), "--project", "-p"),
    sprint: Optional[int] = typer.Option(None, "--sprint", "-s", help="Run specific sprint only"),
    ticket_id: Optional[str] = typer.Option(None, "--ticket-id", "-i", help="Execute specific ticket ID from tasks section"),
    tier: Optional[str] = typer.Option(None, "--tier", "-t", help="Force model tier: free, cheap, balanced, premium"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Simulate without executing"),
    auto_start_proxy: bool = typer.Option(True, "--no-auto-start-proxy", help="Disable automatic proxy startup"),
    max_concurrent: int = typer.Option(1, "--max-concurrent", "-j", help="Maximum number of tasks to run concurrently (default: 1)"),
    max_tasks: Optional[int] = typer.Option(None, "--max-tasks", "-n", help="Maximum total number of tasks to process (default: unlimited)"),
    output_yaml: Optional[str] = typer.Option(None, "--output-yaml", "-o", help="Optional path to also save YAML results file"),
    use_aider: bool = typer.Option(False, "--use-aider", "-a", help="Use aider for code editing instead of LLM chat"),
) -> None:
    """Execute planfile tasks locally with LLM (simpler alternative to 'execute')."""
    from llx.planfile.executor_simple import execute_strategy

    run_console = Console(stderr=True)

    if strategy == ".":
        strategy = "planfile.yaml"

    backends = _print_run_params(strategy, project_path, ticket_id, sprint, tier, dry_run, use_aider, run_console)

    config = LlxConfig.load(str(project_path))
    _ensure_proxy_running(config, dry_run, auto_start_proxy, run_console)
    model_override = _resolve_tier_override(tier, config, run_console)

    def on_progress(msg: str):
        run_console.print(f"[dim]  {msg}[/dim]")

    try:
        results = execute_strategy(
            strategy_path=strategy,
            project_path=project_path,
            sprint_filter=sprint,
            ticket_id=ticket_id,
            dry_run=dry_run,
            on_progress=on_progress,
            model_override=model_override,
            max_concurrent=max_concurrent,
            max_tasks=max_tasks,
            use_aider=use_aider
        )

        _persist_failed_results(results, strategy)
        _sync_todo_from_planfile(strategy, project_path, results, dry_run, run_console)
        _print_results_summary(results, use_aider, backends, run_console)

        payload = _build_results_payload(
            results=results,
            strategy=strategy,
            project_path=project_path,
            sprint=sprint,
            ticket_id=ticket_id,
            tier=tier,
            dry_run=dry_run,
        )

        if output_yaml:
            _save_results_yaml(payload, output_yaml, run_console)

        typer.echo(_yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), nl=False)

    except Exception as e:
        run_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def models(
    tag: Optional[str] = typer.Argument(None, help="Filter models by tag (e.g., FAST, FREE, PROGRAMMING)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    tier: Optional[str] = typer.Option(None, "--tier", "-t", help="Filter by tier"),
) -> None:
    """Show available models with optional filtering by tags, provider, or tier."""
    from llx.cli.formatters import print_models_table
    config = LlxConfig.load(".")
    print_models_table(config, tag=tag, provider=provider, tier=tier)


@app.command()
def info() -> None:
    """Show available tools, models, and configuration."""
    from llx.cli.formatters import print_info_tables
    print_info_tables(LlxConfig.load("."))


@app.command()
def fix(
    workdir: str = typer.Argument(".", help="Working directory"),
    errors: str = typer.Option(None, "--errors", "-e", help="Path to errors JSON file"),
    apply: bool = typer.Option(False, "--apply", help="Apply fixes automatically"),
    model: str = typer.Option(None, "--model", "-m", help="Force specific model"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Fix code issues using LLX-driven model selection (pyqual integration)."""
    from llx.commands.fix import fix as fix_cmd
    fix_cmd(workdir, errors, apply, model, dry_run, verbose)


@app.command()
def init(path: str = typer.Argument(".", help="Project path")) -> None:
    """Initialize llx.toml configuration file."""
    config_path = Path(path).resolve() / "llx.toml"
    if config_path.exists():
        console.print(f"[yellow]llx.toml already exists at {config_path}[/yellow]")
        raise typer.Exit(0)

    config_path.write_text(_LLX_TOML_TEMPLATE, encoding="utf-8")
    console.print(f"[green]Created {config_path}[/green]")


_LLX_TOML_TEMPLATE = '''# llx — Intelligent LLM model router configuration
# Docs: https://github.com/wronai/llx

[thresholds]
files_premium = 50
files_balanced = 10
files_cheap = 3
lines_premium = 20000
lines_balanced = 5000
cc_premium = 6.0
cc_balanced = 4.0
coupling_premium = 30
coupling_balanced = 10

[models.premium]
provider = "anthropic"
model_id = "claude-opus-4-20250514"

[models.balanced]
provider = "anthropic"
model_id = "claude-sonnet-4-20250514"

[models.cheap]
provider = "anthropic"
model_id = "claude-haiku-4-5-20251001"

[models.free]
provider = "openrouter"
model_id = "openrouter/nvidia/nemotron-3-super-120b-a12b:free"

[models.local]
provider = "ollama"
model_id = "ollama/qwen2.5-coder:7b"
max_context = 32000

[models.openrouter]
provider = "openrouter"
model_id = "openrouter/deepseek/deepseek-chat-v3-0324"

[proxy]
port = 4000
# redis_url = "redis://localhost:6379"
# budget_limit = 50.0
'''



def _get_model_for_profile(profile: Optional[str], selector: ModelSelector) -> str:
    """Get model for profile (free/cheap/balanced/local)."""
    profile_map = {"free": FREE_FILTER, "cheap": CHEAP_FILTER, "balanced": BALANCED_FILTER, "local": LOCAL_FILTER}
    model_filter = profile_map.get(profile or "free", FREE_FILTER)
    selected_model = selector.select_model(model_filter)
    if not selected_model:
        console.print("[red]No model available for the selected profile.[/red]")
        raise typer.Exit(1)
    return selected_model


def _load_sprint_mapping(project_name: str, description: str) -> Dict[int, Tuple[str, str]]:
    """Load sprint mapping from config or use fallback."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'planfile_config.yaml')
    try:
        with open(config_path, 'r') as f:
            plan_config = _yaml.safe_load(f)
        return {int(k): (v['file'], v['prompt']) for k, v in plan_config['code']['sprint_files'].items()}
    except Exception as e:
        console.print(f"[dim]Note: Using fallback code generation mapping ({e})[/dim]")
        return {
            1: ("main.py", "Generate a complete FastAPI main.py for '{project_name}' ({description}). Return only Python code."),
            2: ("models.py", "Generate Pydantic models for '{project_name}' ({description}). Return only Python code."),
            3: ("test_api.py", "Generate pytest tests for '{project_name}' ({description}). Return only Python code."),
            4: ("Dockerfile", "Generate a Dockerfile for '{project_name}' FastAPI app. Return only Dockerfile."),
        }


def _generate_sprint_code(client: LlxClient, sprint: dict, sprint_files: Dict[int, Tuple[str, str]], project_name: str, description: str, out: Path, selected_model: str) -> None:
    """Generate code for a single sprint."""
    sid = sprint.get("id") or sprint.get("number", 0)
    file_info = sprint_files.get(sid)
    if not file_info:
        return
    filename, prompt_tmpl = file_info
    prompt = prompt_tmpl.format(project_name=project_name, description=description)
    with console.status(f"[cyan]{sprint.get('name', f'Sprint {sid}')} → {filename}[/cyan]"):
        resp = client.chat([ChatMessage(role="user", content=prompt)], model=selected_model)
        code = re.sub(r"```[a-z]*\n?", "", resp.content).replace("```", "").strip()
        file_path = out / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")
        console.print(f"  [green]✓[/green] {filename} ({len(code.splitlines())} lines)")


def _plan_code_impl(strategy: str, out: Path, model: Optional[str], profile: Optional[str]) -> None:
    """Generate code from strategy file."""
    profile = profile or os.getenv("LLX_DEFAULT_PROFILE", "cheap")
    out.mkdir(parents=True, exist_ok=True)
    with open(strategy, encoding="utf-8") as f:
        strat = _yaml.safe_load(f)
    project_name = strat.get("project_name") or strat.get("name", "My Project")
    description = strat.get("description") or strat.get("goal", {}).get("short", project_name)

    selector = ModelSelector(".")
    selected_model = model or _get_model_for_profile(profile, selector)

    console.print(f"[bold]Generating code for:[/bold] {project_name}\n  Strategy: {strategy}\n  Output: {out.resolve()}\n  Model: {selected_model}\n")

    config = LlxConfig.load(".")
    if config.code_tool == "aider":
        console.print(f"[bold yellow]Handing over to Aider for {project_name}...[/bold yellow]")
        return

    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    sprint_files = _load_sprint_mapping(project_name, description)
    with LlxClient(config) as client:
        for sprint in strat.get("sprints", []):
            _generate_sprint_code(client, sprint, sprint_files, project_name, description, out, selected_model)

    (out / "requirements.txt").write_text("fastapi\nuvicorn[standard]\npydantic>=2.0\n", encoding="utf-8")
    console.print(f"\n[bold green]✅ Code generated in {out.resolve()}[/bold green]")


def main() -> None:
    """CLI entry point for llx."""
    app()