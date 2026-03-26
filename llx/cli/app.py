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

Architecture note (vs preLLM):
- preLLM cli.py: 999 lines, CC=30 (main), CC=27 (query)
- llx cli/app.py: ~250 lines, max CC ≤ 8
- Output formatting delegated to cli/formatters.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from llx.analysis.collector import analyze_project
from llx.config import LlxConfig
from llx.routing.selector import ModelTier, select_model, select_with_context_check

console = Console()
app = typer.Typer(name="llx", help="Intelligent LLM model router driven by real code metrics.", no_args_is_help=True)
proxy_app = typer.Typer(help="Manage LiteLLM proxy server.")
mcp_app = typer.Typer(help="MCP server management.")
app.add_typer(proxy_app, name="proxy")
app.add_typer(mcp_app, name="mcp")


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
    project_path = Path(path).resolve()
    config = LlxConfig.load(project_path)
    config.verbose = config.verbose or verbose

    if run_tools:
        _run_analysis_tools(project_path, config)

    with console.status("Collecting project metrics..."):
        metrics = analyze_project(project_path, toon_dir=toon_dir)

    tier_limit = ModelTier(max_tier) if max_tier else None
    result = select_with_context_check(metrics, config, prefer_local=local, max_tier=tier_limit, task_hint=task)

    from llx.cli.formatters import output_json, output_rich
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


@app.command()
def chat(
    path: str = typer.Argument(".", help="Project path"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt to send"),
    toon_dir: Optional[str] = typer.Option(None, "--toon-dir", "-t"),
    task: Optional[str] = typer.Option(None, "--task"),
    model_override: Optional[str] = typer.Option(None, "--model", "-m"),
    local: bool = typer.Option(False, "--local", "-l"),
) -> None:
    """Analyze project, select model, and send a prompt."""
    project_path = Path(path).resolve()
    config = LlxConfig.load(project_path)
    metrics = analyze_project(project_path, toon_dir=toon_dir)
    result = select_with_context_check(metrics, config, prefer_local=local, task_hint=task)

    model_id = model_override or result.model_id
    console.print(f"[bold]Model:[/bold] {model_id}  [dim]({result.tier.value})[/dim]")

    from llx.integrations.context_builder import build_context
    context = build_context(project_path, metrics, result.tier)

    from llx.routing.client import ChatMessage, LlxClient
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
provider = "google"
model_id = "gemini/gemini-2.5-pro"

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


def _run_analysis_tools(project_path: Path, config: LlxConfig) -> None:
    from llx.analysis.runner import run_all_tools
    output_dir = project_path / ".llx"

    def on_progress(tool: str, status: str) -> None:
        if status == "starting":
            console.print(f"  Running {tool}...", end=" ")
        else:
            console.print(f"[{'green' if 'done' in status else 'yellow'}]{status}[/]")

    run_all_tools(project_path, output_dir, on_progress=on_progress)


# ─── MCP Commands ─────────────────────────────────────────────

@mcp_app.command("start")
def mcp_start(
    mode: str = typer.Option("stdio", help="Server mode: stdio or sse"),
    port: int = typer.Option(3000, help="Port for SSE mode"),
) -> None:
    """Start the llx MCP server."""
    import asyncio
    from llx.mcp.server import main as mcp_main
    console.print(f"Starting llx MCP server ({mode} mode)...")
    if mode == "sse":
        console.print(f"[yellow]SSE mode not yet implemented, using stdio[/yellow]")
    asyncio.run(mcp_main())

@mcp_app.command("config")
def mcp_config() -> None:
    """Print Claude Desktop config snippet."""
    import sys
    snippet = {
        "mcpServers": {
            "llx": {
                "command": sys.executable,
                "args": ["-m", "llx.mcp.server"],
            }
        }
    }
    import json
    console.print(json.dumps(snippet, indent=2))
    console.print("\n[dim]Add to claude_desktop_config.json[/dim]")

@mcp_app.command("tools")
def mcp_tools() -> None:
    """List available MCP tools."""
    from llx.mcp.tools import (
        tool_llx_analyze, tool_llx_select, tool_llx_chat,
        tool_llx_preprocess, tool_llx_context,
        tool_llx_proxym_status, tool_llx_proxym_chat,
        tool_code2llm_analyze, tool_redup_scan, tool_vallm_validate,
        tool_llx_proxy_status,
    )
    from rich.table import Table
    table = Table(title="MCP Tools", show_header=True)
    table.add_column("Tool", style="bold")
    table.add_column("Description")
    for t in [tool_llx_analyze, tool_llx_select, tool_llx_chat,
              tool_llx_preprocess, tool_llx_context,
              tool_llx_proxym_status, tool_llx_proxym_chat,
              tool_code2llm_analyze, tool_redup_scan, tool_vallm_validate,
              tool_llx_proxy_status]:
        table.add_row(t.definition.name, t.definition.description[:80])
    console.print(table)


def main() -> None:
    app()
