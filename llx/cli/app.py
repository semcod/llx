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
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from llx.analysis.collector import analyze_project
from llx.config import LlxConfig
from llx.routing.selector import ModelTier, select_model, select_with_context_check
from llx.cli.strategy_commands import add_strategy_commands

console = Console()
app = typer.Typer(name="llx", help="Intelligent LLM model router driven by real code metrics.", no_args_is_help=True)
proxy_app = typer.Typer(help="Manage LiteLLM proxy server.")
mcp_app = typer.Typer(help="MCP server management.")
plan_app = typer.Typer(help="planfile strategy management.")
app.add_typer(proxy_app, name="proxy")
app.add_typer(mcp_app, name="mcp")
app.add_typer(plan_app, name="plan")

# Add strategy commands
add_strategy_commands(app)


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
    
    # Resolve model alias to actual model_id from config
    if model_override and model_override in config.models:
        model_id = config.models[model_override].model_id
    
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
        tool_llx_proxy_status, tool_planfile_generate, tool_planfile_apply,
    )
    from rich.table import Table
    table = Table(title="MCP Tools", show_header=True)
    table.add_column("Tool", style="bold")
    table.add_column("Description")
    for t in [tool_llx_analyze, tool_llx_select, tool_llx_chat,
              tool_llx_preprocess, tool_llx_context,
              tool_llx_proxym_status, tool_llx_proxym_chat,
              tool_code2llm_analyze, tool_redup_scan, tool_vallm_validate,
              tool_llx_proxy_status, tool_planfile_generate, tool_planfile_apply]:
        table.add_row(t.definition.name, t.definition.description[:80])
    console.print(table)


# ─── Plan Commands ──────────────────────────────────────────────

@plan_app.command("apply")
def plan_apply(
    strategy: str = typer.Argument(..., help="Path to strategy.yaml"),
    path: str = typer.Argument(".", help="Project path"),
    sprint: Optional[str] = typer.Option(None, "--sprint", "-s"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Apply a planfile strategy to the project."""
    from llx.planfile import execute_strategy
    results = execute_strategy(strategy, path, sprint_filter=sprint, dry_run=dry_run,
                               on_progress=lambda msg: console.print(f"  {msg}"))
    for r in results:
        icon = "✓" if r.status == "success" else "○" if r.status == "dry_run" else "✗"
        console.print(f"  {icon} {r.task_name} → {r.model_used}")

@plan_app.command("models")
def plan_models(
    provider: Optional[str] = typer.Option(None, "--provider", 
        help="Filter by provider: openai, anthropic, openrouter, ollama"),
    tier: Optional[str] = typer.Option(None, "--tier", 
        help="Filter by tier: free, cheap, balanced, premium"),
    local_only: bool = typer.Option(False, "--local", help="Show local models only"),
    cloud_only: bool = typer.Option(False, "--cloud", help="Show cloud models only"),
    show_keys: bool = typer.Option(False, "--show-keys", help="Show API key status"),
) -> None:
    """List available models."""
    try:
        from llx.planfile.model_selector import ModelSelector, ModelFilter, ModelProvider, ModelTier
        
        # Build filter
        filter_params = {}
        if provider:
            filter_params["provider"] = ModelProvider(provider.lower())
        if tier:
            filter_params["tier"] = ModelTier(tier.lower())
        filter_params["local_only"] = local_only
        filter_params["cloud_only"] = cloud_only
        
        model_filter = ModelFilter(**filter_params)
        
        # Get models
        selector = ModelSelector(".")
        models = selector.list_models(model_filter)
        
        if not models:
            console.print("[yellow]No models found matching the criteria[/yellow]")
            return
        
        # Group by provider
        by_provider = {}
        for model in models:
            provider = model["provider"]
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(model)
        
        # Display
        console.print("[bold]Available Models:[/bold]")
        console.print()
        
        for provider_name, provider_models in sorted(by_provider.items()):
            console.print(f"[cyan]{provider_name.title()}:[/cyan]")
            for model in sorted(provider_models, key=lambda x: x.get("tier", "unknown")):
                status = ""
                if show_keys:
                    status = "✓" if model["has_api_key"] else "✗"
                    status = f"[{status}] "
                
                tier_color = {
                    "free": "green",
                    "cheap": "yellow",
                    "balanced": "blue",
                    "premium": "magenta"
                }.get(model["tier"], "white")
                
                console.print(f"  {status}{model['id']} [{tier_color}]{model['tier']}[/{tier_color}]")
            console.print()
        
        # Show profiles
        console.print("[bold]Predefined Profiles:[/bold]")
        console.print("  [green]free[/green] - All free models (local and cloud)")
        console.print("  [green]local[/green] - Local models only")
        console.print("  [green]cloud-free[/green] - Free cloud models only")
        console.print("  [green]openrouter-free[/green] - Free OpenRouter models only")
        console.print("  [yellow]cheap[/yellow] - Cheap cloud models")
        console.print("  [blue]balanced[/blue] - Balanced performance/price")
        
    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")


@plan_app.command("generate")
def plan_generate(
    path: str = typer.Argument(".", help="Project to analyze"),
    output: str = typer.Option("strategy.yaml", "--output", "-o"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    sprints: int = typer.Option(3, "--sprints"),
    focus: Optional[str] = typer.Option(None, "--focus"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Project description for better strategy generation"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", 
        help="Model profile: free, local, cloud-free, openrouter-free, cheap, balanced"),
    provider: Optional[str] = typer.Option(None, "--provider", 
        help="Filter by provider: openai, anthropic, openrouter, ollama"),
    tier: Optional[str] = typer.Option(None, "--tier", 
        help="Filter by tier: free, cheap, balanced, premium"),
    local_only: bool = typer.Option(False, "--local", help="Use local models only"),
    cloud_only: bool = typer.Option(False, "--cloud", help="Use cloud models only"),
) -> None:
    """Generate strategy.yaml using built-in generator."""
    try:
        # Import required modules
        from llx.planfile.generate_strategy import generate_strategy_with_fix, save_fixed_strategy
        from llx.planfile.model_selector import ModelSelector, ModelFilter, ModelProvider, ModelTier
        
        # Get model selection
        selected_model = _get_model_for_generation(model, profile, provider, tier, local_only, cloud_only)
        
        if not selected_model:
            console.print("[red]No suitable model found[/red]")
            return
        
        # Generate strategy
        console.print(f"\n[blue]Generating strategy for {path}...[/blue]")
        strategy_data = generate_strategy_with_fix(
            path, 
            model=selected_model, 
            sprints=sprints, 
            focus=focus,
            description=description
        )
        
        # Save strategy
        save_fixed_strategy(strategy_data, output)
        console.print(f"[green]✓ Strategy saved to {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error generating strategy: {e}[/red]")
        raise typer.Exit(1)


def _get_model_for_generation(model, profile, provider, tier, local_only, cloud_only):
    """Get model for strategy generation based on filters."""
    from llx.planfile.model_selector import (
        ModelSelector, ModelFilter, ModelProvider, ModelTier,
        FREE_FILTER, LOCAL_FILTER, CLOUD_FREE_FILTER,
        OPENROUTER_FREE_FILTER, CHEAP_FILTER, BALANCED_FILTER
    )
    
    if model:
        return model
    
    # Use predefined profile if specified
    if profile:
        profile_map = {
            "free": FREE_FILTER,
            "local": LOCAL_FILTER,
            "cloud-free": CLOUD_FREE_FILTER,
            "openrouter-free": OPENROUTER_FREE_FILTER,
            "cheap": CHEAP_FILTER,
            "balanced": BALANCED_FILTER
        }
        model_filter = profile_map.get(profile)
        if not model_filter:
            console.print(f"[red]Unknown profile: {profile}[/red]")
            console.print(f"Available profiles: {', '.join(profile_map.keys())}")
            raise typer.Exit(1)
    else:
        # Build custom filter
        filter_params = {}
        
        if provider:
            try:
                filter_params["provider"] = ModelProvider(provider.lower())
            except ValueError:
                console.print(f"[red]Unknown provider: {provider}[/red]")
                console.print("Available providers: openai, anthropic, openrouter, ollama")
                raise typer.Exit(1)
        
        if tier:
            try:
                filter_params["tier"] = ModelTier(tier.lower())
            except ValueError:
                console.print(f"[red]Unknown tier: {tier}[/red]")
                console.print("Available tiers: free, cheap, balanced, premium")
                raise typer.Exit(1)
        
        filter_params["local_only"] = local_only
        filter_params["cloud_only"] = cloud_only
        
        model_filter = ModelFilter(**filter_params)
    
    # Select model using "." as path for default config
    selector = ModelSelector(".")
    selected_model = selector.select_model(model_filter)
    
    if not selected_model:
        console.print("[red]No model found matching the criteria[/red]")
        
        # Show available models
        console.print("\n[yellow]Available models:[/yellow]")
        available = selector.list_models()
        for m in available[:10]:  # Show first 10
            status = "✓" if m["has_api_key"] else "✗ (no API key)"
            console.print(f"  {status} {m['id']} [{m['provider']}][{m['tier']}]")
        
        raise typer.Exit(1)
    
    return selected_model

@plan_app.command("review")
def plan_review(
    strategy: str = typer.Argument(...),
    path: str = typer.Argument("."),
) -> None:
    """Review progress against strategy quality gates."""
    try:
        from llx.planfile import load_valid_strategy
        s = load_valid_strategy(strategy)
        console.print(f"[green]Strategy loaded: {s.name}[/green]")
        console.print(f"  Sprints: {len(s.sprints)}")
        console.print(f"  Quality gates: {len(s.quality_gates)}")

        console.print("\n[bold]Quality Gates:[/bold]")
        for gate in s.quality_gates:
            console.print(f"  [cyan]•[/cyan] {gate.name}: {', '.join(gate.criteria)}")
    except Exception as e:
        console.print(f"[red]Error reviewing strategy: {e}[/red]")


@plan_app.command("code")
def plan_code(
    strategy: str = typer.Argument(..., help="Path to strategy.yaml"),
    output_dir: str = typer.Argument("./project", help="Directory to write generated files"),
    profile: Optional[str] = typer.Option("free", "--profile", "-p",
        help="Model profile: free, local, cheap, balanced"),
) -> None:
    """Generate project code from strategy using LLM (free tier by default).

    This command reads the strategy, builds a prompt per sprint task and
    calls the LLM to generate Python source files written to output_dir.
    """
    import yaml as _yaml
    import re

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with open(strategy, encoding="utf-8") as f:
        strat = _yaml.safe_load(f)

    project_name = strat.get("project_name") or strat.get("name", "My Project")
    description = strat.get("description") or strat.get("goal", {}).get("description", "") or strat.get("goal", {}).get("short", project_name)
    if isinstance(description, dict):
        description = description.get("short", project_name)
    sprints = strat.get("sprints", [])

    # Select model
    from llx.planfile.model_selector import ModelSelector, ModelFilter
    selector = ModelSelector(".")
    try:
        from llx.planfile.model_selector import FREE_FILTER, CHEAP_FILTER, BALANCED_FILTER, LOCAL_FILTER
        profile_map = {"free": FREE_FILTER, "cheap": CHEAP_FILTER,
                       "balanced": BALANCED_FILTER, "local": LOCAL_FILTER}
        model_filter = profile_map.get(profile or "free", FREE_FILTER)
        model = selector.select_model(model_filter)
    except Exception:
        model = None

    if not model:
        console.print("[red]No model available for the selected profile.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Generating code for:[/bold] {project_name}")
    console.print(f"  Strategy: {strategy}")
    console.print(f"  Output:   {out.resolve()}")
    console.print(f"  Model:    {model}")
    console.print()

    config = LlxConfig.load(".")
    from llx.routing.client import LlxClient, ChatMessage
    
    # Suppress LiteLLM Provider List messages
    import logging
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    try:
        import litellm
        litellm.suppress_debug_info = True
        litellm.set_verbose = False
    except ImportError:
        pass

    # Load sprint file mapping from config
    import os
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'planfile_config.yaml')
    try:
        with open(config_path, 'r') as f:
            plan_config = _yaml.safe_load(f)
        SPRINT_FILES = {}
        for sprint_num, file_info in plan_config['code']['sprint_files'].items():
            SPRINT_FILES[int(sprint_num)] = (file_info['file'], file_info['prompt'])
    except Exception:
        # Fallback to hardcoded mapping
        SPRINT_FILES = {
            1: ("main.py",      "Generate a complete FastAPI main.py for '{name}' ({desc}). "
                                 "Include CRUD endpoints, in-memory storage, /health endpoint. Return only Python code."),
            2: ("models.py",    "Generate Pydantic models (ItemBase, ItemCreate, Item) for '{name}' ({desc}). Return only Python code."),
            3: ("test_api.py",  "Generate pytest tests for a FastAPI '{name}' API ({desc}) using TestClient. Return only Python code."),
            4: ("Dockerfile",   "Generate a Dockerfile for '{name}' FastAPI app. Use python:3.11-slim, install fastapi uvicorn, expose 8000. Return only Dockerfile."),
        }

    generated = {}
    with LlxClient(config) as client:
        for sprint in sprints:
            sid = sprint.get("id") or sprint.get("number", 0)
            sname = sprint.get("name", f"Sprint {sid}")
            file_info = SPRINT_FILES.get(sid)
            if not file_info:
                continue
            filename, prompt_tmpl = file_info
            prompt = prompt_tmpl.format(project_name=project_name, description=description)

            with console.status(f"[cyan]{sname} → {filename}[/cyan]"):
                try:
                    resp = client.chat([ChatMessage(role="user", content=prompt)], model=model)
                    code = resp.content
                    # Strip markdown fences
                    code = re.sub(r"```[a-z]*\n?", "", code).replace("```", "").strip()
                    (out / filename).write_text(code, encoding="utf-8")
                    console.print(f"  [green]✓[/green] {filename} ({len(code.splitlines())} lines)")
                    generated[filename] = code
                except Exception as e:
                    console.print(f"  [yellow]⚠[/yellow] {filename}: {e}")

    # Always write requirements.txt and README
    (out / "requirements.txt").write_text(
        "fastapi\nuvicorn[standard]\npydantic>=2.0\nhttpx\npytest\npytest-cov\n",
        encoding="utf-8",
    )
    console.print("  [green]✓[/green] requirements.txt")

    (out / "README.md").write_text(
        f"# {project_name}\n\n{description}\n\n"
        "## Run\n```bash\npip install -r requirements.txt\nuvicorn main:app --reload\n```\n\n"
        "## Test\n```bash\npytest test_api.py -v\n```\n\n"
        "## Docker\n```bash\ndocker compose up --build\n```\n",
        encoding="utf-8",
    )
    console.print("  [green]✓[/green] README.md")
    console.print(f"\n[bold green]✅ Code generated in {out.resolve()}[/bold green]")


@plan_app.command("run")
def plan_run(
    project_dir: str = typer.Argument("./project", help="Directory with generated project"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    install: bool = typer.Option(True, "--install/--no-install", help="pip install -r requirements.txt first"),
) -> None:
    """Start the generated FastAPI application with uvicorn."""
    import subprocess

    proj = Path(project_dir).resolve()
    if not (proj / "main.py").exists():
        console.print(f"[red]main.py not found in {proj}[/red]")
        console.print("  Run `llx plan code strategy.yaml` first.")
        raise typer.Exit(1)

    if install and (proj / "requirements.txt").exists():
        console.print("[cyan]Installing dependencies...[/cyan]")
        subprocess.run(["pip", "install", "-r", "requirements.txt", "-q"], cwd=proj, check=True)

    console.print(f"[bold green]Starting API on http://localhost:{port}[/bold green]")
    console.print(f"  Docs: http://localhost:{port}/docs")
    console.print(f"  Health: http://localhost:{port}/health")
    console.print("  [dim](Ctrl+C to stop)[/dim]\n")
    subprocess.run(
        ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", str(port)],
        cwd=proj,
    )


@plan_app.command("monitor")
def plan_monitor(
    strategy: str = typer.Argument("strategy.yaml", help="Path to strategy.yaml"),
    url: str = typer.Option("http://localhost:8000", "--url", "-u", help="Base URL of the running app"),
    interval: int = typer.Option(0, "--interval", "-i", help="Repeat every N seconds (0 = once)"),
) -> None:
    """Monitor a running application: health check + quality gates summary."""
    import httpx
    import time
    import yaml as _yaml

    with open(strategy, encoding="utf-8") as f:
        strat = _yaml.safe_load(f)

    project_name = strat.get("name", "App")
    gates = strat.get("quality_gates", [])

    def _check() -> None:
        console.print(f"\n[bold]Monitor: {project_name}[/bold]  ({url})")
        console.print(f"[dim]{time.strftime('%H:%M:%S')}[/dim]\n")

        # Health check
        try:
            r = httpx.get(f"{url}/health", timeout=3)
            if r.status_code == 200:
                console.print(f"  [green]✓[/green] /health → {r.status_code}  {r.text[:60]}")
            else:
                console.print(f"  [yellow]⚠[/yellow] /health → {r.status_code}")
        except Exception as e:
            console.print(f"  [red]✗[/red] /health unreachable: {e}")

        # Docs check
        try:
            r = httpx.get(f"{url}/docs", timeout=3)
            icon = "[green]✓[/green]" if r.status_code == 200 else "[yellow]⚠[/yellow]"
            console.print(f"  {icon} /docs  → {r.status_code}")
        except Exception:
            console.print("  [red]✗[/red] /docs unreachable")

        # Quality gates summary
        if gates:
            console.print("\n  [bold]Quality Gates (from strategy):[/bold]")
            for gate in gates:
                name = gate.get("name") if isinstance(gate, dict) else str(gate)
                criteria = gate.get("criteria", []) if isinstance(gate, dict) else []
                console.print(f"    [cyan]•[/cyan] {name}")
                for c in criteria:
                    console.print(f"      [dim]- {c}[/dim]")

    if interval > 0:
        console.print(f"[dim]Monitoring every {interval}s — Ctrl+C to stop[/dim]")
        try:
            while True:
                _check()
                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[dim]Monitor stopped.[/dim]")
    else:
        _check()


def main() -> None:
    app()

