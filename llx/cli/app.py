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
import os

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
    free: bool = typer.Option(False, "--free", "-f", help="Force free-tier model"),
) -> None:
    """Analyze project, select model, and send a prompt."""
    project_path = Path(path).resolve()
    config = LlxConfig.load(project_path)
    metrics = analyze_project(project_path, toon_dir=toon_dir)
    
    # If --free flag is set, force free tier selection
    if free:
        from llx.routing.selector import ModelTier
        result = select_with_context_check(metrics, config, prefer_local=local, task_hint=task, force_tier=ModelTier.FREE)
    else:
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

@mcp_app.command("config")
def mcp_config() -> None:
    """Print Claude Desktop config snippet."""
    import sys
    snippet = {
        "mcpServers": {
            "llx": {
                "command": sys.executable,
                "args": ["-m", "llx.mcp"],
            }
        }
    }
    import json
    console.print(json.dumps(snippet, indent=2))
    console.print("\n[dim]Add to claude_desktop_config.json[/dim]")

@mcp_app.command("tools")
def mcp_tools() -> None:
    """List available MCP tools."""
    from llx.mcp.tools import MCP_TOOLS
    from rich.table import Table
    table = Table(title="MCP Tools", show_header=True)
    table.add_column("Tool", style="bold")
    table.add_column("Description")
    for t in MCP_TOOLS:
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
    import subprocess
    import sys
    
    cmd = [sys.executable, "-m", "planfile", "apply", strategy, path]
    if sprint:
        cmd.extend(["--sprint", sprint])
    if dry_run:
        cmd.append("--dry-run")
    
    subprocess.run(cmd)

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


@plan_app.command("all")
def plan_all(
    description: str = typer.Argument(..., help="Project description"),
    output_dir: str = typer.Option("./my-project", "--output", "-o", help="Directory to write generated files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p",
        help="Model profile: free, local, cheap, balanced"),
    project_type: Optional[str] = typer.Option(None, "--type", "-t", help="Project type: api, webapp, cli, data, ml"),
    framework: Optional[str] = typer.Option(None, "--framework", "-f", help="Framework to use"),
    sprints: Optional[int] = typer.Option(None, "--sprints", "-s", help="Number of sprints"),
    focus: Optional[str] = typer.Option(None, "--focus", help="Project focus"),
    run: bool = typer.Option(False, "--run", "-r", help="Run the application after generation"),
    monitor: bool = typer.Option(False, "--monitor", "-m", help="Start monitoring after running"),
) -> None:
    """Complete workflow: generate strategy, code, and optionally run."""
    import subprocess
    import sys
    
    # Internal defaults
    if profile is None:
        profile = os.getenv("LLX_DEFAULT_PROFILE", "cheap")
    if sprints is None:
        sprints = int(os.getenv("LLX_DEFAULT_SPRINTS", "8"))
    
    from llx.detection import ProjectTypeDetector
    
    strategy_file = "strategy.yaml"
    
    console.print(f"[bold blue]🚀 LLX Complete Workflow[/bold blue]")
    console.print(f"[dim]Description: {description}[/dim]\n")
    
    # Detect project type if not specified
    detector = ProjectTypeDetector()
    if not project_type:
        project_type = detector.detect(Path.cwd())
        console.print(f"[dim]Detected project type: {project_type}[/dim]")
    
    # Get project configuration
    project_config = detector.get_project_config(project_type)
    
    # Set defaults from project type or environment
    if not profile:
        profile = os.getenv("LLX_DEFAULT_PROFILE", "cheap")
    if not sprints:
        sprints = project_config.get("default_sprints", 8)
    if not focus:
        focus = project_config.get("default_focus", "api")
    if not framework:
        framework = project_config.get("default_framework")
    
    # Show configuration
    console.print(f"[dim]Configuration:[/dim]")
    console.print(f"  Type: {project_type}")
    console.print(f"  Framework: {framework or 'default'}")
    console.print(f"  Sprints: {project_config.get('default_sprints', sprints)}")
    console.print(f"  Focus: {focus}")
    console.print(f"  Profile: {profile}\n")
    
    # 1. Generate strategy
    console.print(f"[yellow]1. Generating strategy...[/yellow]")
    try:
        from llx.planfile.generate_strategy import generate_strategy_with_fix, save_fixed_strategy
        from llx.planfile.model_selector import ModelSelector, ModelFilter, ModelProvider, ModelTier
        
        # Get model selection
        selected_model = _get_model_for_generation(None, profile, None, None, False, False)
        
        if not selected_model:
            console.print("[red]No suitable model found[/red]")
            return
        
        strategy_data = generate_strategy_with_fix(
            ".", 
            model=selected_model, 
            sprints=sprints, 
            focus=focus,
            description=description,
            project_type=project_type,
            framework=framework
        )
        
        save_fixed_strategy(strategy_data, strategy_file)
        console.print(f"[green]✓ Strategy saved to {strategy_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating strategy: {e}[/red]")
        raise typer.Exit(1)
    
    # 2. Generate code
    console.print(f"\n[yellow]2. Generating code...[/yellow]")
    try:
        # Call internal implementation
        _plan_code_impl(strategy_file, Path(output_dir), None, profile)
    except Exception as e:
        console.print(f"[red]Error generating code: {e}[/red]")
        raise typer.Exit(1)
    
    # 3. Run if requested
    if run:
        console.print(f"\n[yellow]3. Running application...[/yellow]")
        console.print(f"[dim]Note: This will start the server. Use Ctrl+C to stop.[/dim]\n")
        
        if monitor:
            # Start monitoring in background
            console.print(f"[cyan]Starting monitoring in background...[/cyan]")
            monitor_cmd = [sys.executable, "-c", 
                          f"import sys; sys.path.insert(0, '{os.path.dirname(os.path.dirname(__file__))}'); "
                          f"from llx.cli.app import app; app()", 
                          "plan", "monitor", strategy_file]
            
            subprocess.Popen(monitor_cmd)
            console.print(f"[green]✓ Monitoring started[/green]")
        
        # Run the application
        try:
            plan_run(output_dir)
        except KeyboardInterrupt:
            console.print(f"\n[yellow]Application stopped.[/yellow]")
    
    console.print(f"\n[bold green]✅ Complete![/bold green]")
    if not run:
        console.print(f"\n[cyan]Next steps:[/cyan]")
        console.print(f"  llx plan run {output_dir}     # Run the app")
        console.print(f"  llx plan monitor {strategy_file}  # Monitor")


@plan_app.command("detect")
def plan_detect(
    path: str = typer.Argument(".", help="Path to analyze")
) -> None:
    """Detect project type and show configuration."""
    from llx.detection import ProjectTypeDetector
    
    detector = ProjectTypeDetector()
    project_path = Path(path).resolve()
    
    # Detect from path
    type_from_path = detector.detect_from_path(project_path)
    
    # Detect from files
    type_from_files = detector.detect_from_files(project_path)
    
    # Detect from config
    type_from_config = detector.detect_from_config(project_path)
    
    console.print(f"[bold]Project Detection Results[/bold]")
    console.print(f"  Path: {project_path}")
    console.print(f"  From directory name: {type_from_path or 'None'}")
    console.print(f"  From files: {type_from_files or 'None'}")
    console.print(f"  From config: {type_from_config or 'None'}")
    
    final_type = detector.detect(project_path)
    console.print(f"  [green]Detected type: {final_type}[/green]")
    
    # Show configuration
    config = detector.get_project_config(final_type)
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Display name: {config.get('display_name', '')}")
    console.print(f"  Default sprints: {config.get('default_sprints', 8)}")
    console.print(f"  Default focus: {config.get('default_focus', 'api')}")
    console.print(f"  Default framework: {config.get('default_framework', 'fastapi')}")
    console.print(f"  Supported frameworks: {', '.join(config.get('supported_frameworks', []))}")


@plan_app.command("types")
def plan_types() -> None:
    """List all available project types."""
    from llx.detection import ProjectTypeDetector
    
    detector = ProjectTypeDetector()
    
    console.print("[bold]Available Project Types:[/bold]\n")
    
    for project_type, config in detector.get_all_types().items():
        console.print(f"[cyan]{project_type}[/cyan] - {config.get('display_name', '')}")
        console.print(f"  Default sprints: {config.get('default_sprints')}")
        console.print(f"  Default framework: {config.get('default_framework')}")
        console.print(f"  Supported frameworks: {', '.join(config.get('supported_frameworks', []))}")
        console.print()


@plan_app.command("generate")
def plan_generate(
    path: str = typer.Argument(".", help="Project to analyze"),
    output: str = typer.Option("strategy.yaml", "--output", "-o"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    sprints: Optional[int] = typer.Option(None, "--sprints", "-s"),
    focus: Optional[str] = typer.Option(None, "--focus"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    tier: Optional[str] = typer.Option(None, "--tier"),
    local_only: bool = typer.Option(False, "--local"),
    cloud_only: bool = typer.Option(False, "--cloud"),
) -> None:
    """Generate strategy.yaml using planfile."""
    import subprocess
    import sys
    
    cmd = [sys.executable, "-m", "planfile", "generate", path, "--output", output]
    if model:
        cmd.extend(["--model", model])
    if sprints:
        cmd.extend(["--sprints", str(sprints)])
    if focus:
        cmd.extend(["--focus", focus])
    if description:
        cmd.extend(["--description", description])
    if profile:
        cmd.extend(["--profile", profile])
    if provider:
        cmd.extend(["--provider", provider])
    if tier:
        cmd.extend(["--tier", tier])
    if local_only:
        cmd.append("--local")
    if cloud_only:
        cmd.append("--cloud")
    
    subprocess.run(cmd)

def _plan_generate_impl(
    path: str, output: str, model: Optional[str], sprints: Optional[int], 
    focus: Optional[str], description: Optional[str], profile: Optional[str], 
    provider: Optional[str], tier: Optional[str], local_only: bool, cloud_only: bool
) -> None:
    """Internal implementation of plan generate."""
    if profile is None:
        profile = os.getenv("LLX_DEFAULT_PROFILE", "cheap")
    if sprints is None:
        sprints = int(os.getenv("LLX_DEFAULT_SPRINTS", "8"))
    if focus is None:
        focus = "api"

    try:
        from llx.planfile.generate_strategy import generate_strategy_with_fix, save_fixed_strategy
        
        selected_model = _get_model_for_generation(model, profile, provider, tier, local_only, cloud_only)
        if not selected_model:
            console.print("[red]No suitable model found[/red]")
            return
        
        # generate_strategy_with_fix already prints info
        strategy_data = generate_strategy_with_fix(
            path, 
            model=selected_model, 
            sprints=sprints, 
            focus=focus,
            description=description
        )
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
    import subprocess
    import sys
    
    cmd = [sys.executable, "-m", "planfile", "review", strategy, path]
    subprocess.run(cmd)


@plan_app.command("code")
def plan_code(
    strategy: str = typer.Argument("strategy.yaml", help="Path to strategy.yaml"),
    output_dir: str = typer.Argument("./project", help="Directory to write generated files"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Implement the strategy sprint-by-sprint."""
    _plan_code_impl(strategy, Path(output_dir), model, profile)

def _plan_code_impl(strategy: str, out: Path, model: Optional[str], profile: Optional[str]) -> None:
    """Internal implementation of plan code."""
    import yaml as _yaml
    import re
    
    if profile is None:
        profile = os.getenv("LLX_DEFAULT_PROFILE", "cheap")

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
    
    if model:
        selected_model = model
    else:
        try:
            from llx.planfile.model_selector import FREE_FILTER, CHEAP_FILTER, BALANCED_FILTER, LOCAL_FILTER
            profile_map = {"free": FREE_FILTER, "cheap": CHEAP_FILTER,
                           "balanced": BALANCED_FILTER, "local": LOCAL_FILTER}
            model_filter = profile_map.get(profile or "free", FREE_FILTER)
            selected_model = selector.select_model(model_filter)
        except Exception:
            selected_model = None

    if not selected_model:
        console.print("[red]No model available for the selected profile.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Generating code for:[/bold] {project_name}")
    console.print(f"  Strategy: {strategy}")
    console.print(f"  Output:   {out.resolve()}")
    console.print(f"  Model:    {selected_model}")
    console.print()

    config = LlxConfig.load(".")
    from llx.routing.client import LlxClient, ChatMessage

    if config.code_tool == "aider":
        console.print(f"[bold yellow]Handing over to Aider for {project_name}...[/bold yellow]")
        console.print(f"  Command: aider --model {selected_model} --msg 'Implement strategy from {strategy}' {out.resolve()}")
        console.print("\n[dim]Note: Aider integration is manual for now. Please run the command above.[/dim]")
        return

    if config.run_env != "local":
        console.print(f"[yellow]Note: Target environment is set to '{config.run_env}'. Ensuring compatibility...[/yellow]")
    
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
    except Exception as e:
        console.print(f"[dim]Note: Using fallback code generation mapping ({e})[/dim]")
        # Fallback to hardcoded mapping
        SPRINT_FILES = {
            1: ("main.py",      "Generate a complete FastAPI main.py for '{project_name}' ({description}). "
                                 "Include CRUD endpoints, in-memory storage, /health endpoint. Return only Python code."),
            2: ("models.py",    "Generate Pydantic models (ItemBase, ItemCreate, Item) for '{project_name}' ({description}). Return only Python code."),
            3: ("test_api.py",  "Generate pytest tests for a FastAPI '{project_name}' API ({description}) using TestClient. Return only Python code."),
            4: ("Dockerfile",   "Generate a Dockerfile for '{project_name}' FastAPI app. Use python:3.11-slim, install fastapi uvicorn, expose 8000. Return only Dockerfile."),
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
            # Use project_name and description in prompt
            prompt = prompt_tmpl.format(project_name=project_name, description=description)

            with console.status(f"[cyan]{sname} → {filename}[/cyan]"):
                try:
                    resp = client.chat([ChatMessage(role="user", content=prompt)], model=selected_model)
                    code = resp.content
                    # Strip markdown fences
                    code = re.sub(r"```[a-z]*\n?", "", code).replace("```", "").strip()
                    # Ensure directory exists
                    file_path = out / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(code, encoding="utf-8")
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
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port to listen on"),
    install: bool = typer.Option(True, "--install/--no-install", help="pip install -r requirements.txt first"),
) -> None:
    """Start the generated application (detects command from strategy or uses uvicorn)."""
    import subprocess
    import yaml as _yaml

    # Internal defaults
    if port is None:
        port = int(os.getenv("LLX_DEFAULT_PORT", "8000"))

    proj = Path(project_dir).resolve()
    
    # Try to find strategy.yaml to get run_command
    run_cmd = ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", str(port)]
    
    strategy_path = proj.parent / "strategy.yaml"
    if strategy_path.exists():
        try:
            with open(strategy_path, encoding="utf-8") as f:
                strat = _yaml.safe_load(f)
                if strat and "run_command" in strat:
                    run_cmd = strat["run_command"].split()
                    console.print(f"[cyan]Found run command in strategy: {strat['run_command']}[/cyan]")
        except Exception:
            pass

    if install and (proj / "requirements.txt").exists():
        console.print("[cyan]Installing dependencies...[/cyan]")
        subprocess.run(["pip", "install", "-r", "requirements.txt", "-q"], cwd=proj, check=True)

    console.print(f"[bold green]Starting application in {proj.name}...[/bold green]")
    console.print(f"  Command: {' '.join(run_cmd)}")
    console.print("  [dim](Ctrl+C to stop)[/dim]\n")
    
    subprocess.run(run_cmd, cwd=proj)


@plan_app.command("monitor")
def plan_monitor(
    strategy: str = typer.Argument("strategy.yaml", help="Path to strategy.yaml"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Base URL of the running app"),
    interval: int = typer.Option(0, "--interval", "-i", help="Repeat every N seconds (0 = once)"),
) -> None:
    """Monitor a running application: health check + quality gates summary."""
    import httpx
    import time
    import yaml as _yaml

    # Internal defaults
    if url is None:
        url = os.getenv("LLX_DEFAULT_URL", "http://localhost:8000")

    with open(strategy, encoding="utf-8") as f:
        strat = _yaml.safe_load(f)

    project_name = strat.get("project_name") or strat.get("name", "App")
    gates = strat.get("quality_gates", [])

    def _check() -> None:
        console.print(f"\n[bold]Monitor: {project_name}[/bold]  ({url})")
        console.print(f"[dim]{time.strftime('%H:%M:%S')}[/dim]\n")

        # Get paths from strategy or defaults
        health_path = strat.get("monitor", {}).get("health_path", "/health")
        docs_path = strat.get("monitor", {}).get("docs_path", "/docs")

        # Health check
        try:
            r = httpx.get(f"{url.rstrip('/')}{health_path}", timeout=3)
            if r.status_code == 200:
                console.print(f"  [green]✓[/green] {health_path} → {r.status_code}  {r.text[:60]}")
            else:
                console.print(f"  [yellow]⚠[/yellow] {health_path} → {r.status_code}")
        except Exception as e:
            console.print(f"  [red]✗[/red] {health_path} unreachable: {e}")

        # Docs check
        if docs_path:
            try:
                r = httpx.get(f"{url.rstrip('/')}{docs_path}", timeout=3)
                icon = "[green]✓[/green]" if r.status_code == 200 else "[yellow]⚠[/yellow]"
                console.print(f"  {icon} {docs_path}  → {r.status_code}")
            except Exception:
                console.print(f"  [red]✗[/red] {docs_path} unreachable")

        # Quality gates summary
        if gates:
            console.print("\n  [bold]Quality Gates (from strategy):[/bold]")
            for gate in gates:
                if isinstance(gate, dict):
                    name = gate.get("gate") or gate.get("name") or "Unnamed Gate"
                    condition = gate.get("condition", "")
                    criteria = gate.get("criteria", [])
                    if condition:
                        console.print(f"    [cyan]•[/cyan] {name}")
                        console.print(f"      [dim]Condition: {condition}[/dim]")
                    else:
                        console.print(f"    [cyan]•[/cyan] {name}")
                    for c in criteria:
                        console.print(f"      [dim]- {c}[/dim]")
                else:
                    console.print(f"    [cyan]•[/cyan] {str(gate)}")

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


@plan_app.command("wizard")
def plan_wizard(
    path: str = typer.Argument(".", help="Project path"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    output: str = typer.Option("strategy.yaml", "--output", "-o"),
) -> None:
    """Unified wizard: Generate strategy -> Implement code -> Run -> Monitor."""
    from rich.prompt import Prompt, Confirm
    
    # Internal defaults
    if profile is None:
        profile = os.getenv("LLX_DEFAULT_PROFILE", "cheap")
    if description is None:
        description = os.getenv("LLX_DEFAULT_DESCRIPTION", "")
    
    console.print(Panel.fit(
        "[bold blue]LLX Project Wizard[/bold blue]\n[dim]Guidance for your development lifecycle[/dim]",
        border_style="blue"
    ))
    
    # 1. Generate Strategy
    if not description:
        description = Prompt.ask("[bold cyan]Enter project description[/bold cyan]")
    
    console.print("\n[yellow]Step 1: Generating Architecture & Strategy...[/yellow]")
    _plan_generate_impl(
        path=path, output=output, description=description, profile=profile,
        model=None, sprints=None, focus=None, provider=None, tier=None, 
        local_only=False, cloud_only=False
    )
    
    # 2. Implement Code
    strategy_path = Path(path) / output
    project_dir = Path(path) / "my-api"
    
    if Confirm.ask(f"\n[bold cyan]Proceed with code generation in {project_dir}?[/bold cyan]", default=True):
        console.print("[yellow]Step 2: Implementing Code (Sprints 1-8)...[/yellow]")
        _plan_code_impl(strategy=str(strategy_path), out=Path(project_dir), model=None, profile=profile)
    else:
        console.print("[dim]Aborted code generation.[/dim]")
        return

    # 3. Run & Monitor
    if Confirm.ask("\n[bold cyan]Run and monitor the application?[/bold cyan]", default=True):
        console.print("[yellow]Step 3: Starting Application & Monitor...[/yellow]")
        
        # Start run in background
        import subprocess
        import time
        
        # We'll use a simplified version of plan_run/plan_monitor logic here
        # to avoid blocking issues or process management complexities in the wizard
        console.print(f"[bold green]Application starting...[/bold green]")
        
        # For simplicity in the wizard, we'll just hand over to the standard commands
        # or explain how to run them if backgrounding is tricky.
        console.print(f"\n[bold green]✅ Project Ready![/bold green]")
        console.print(f"  To run:    [bold]llx plan run {project_dir}[/bold]")
        console.print(f"  To monitor: [bold]llx plan monitor {strategy_path}[/bold]")
        
        # Optional: Actually try to run it if the user insisted
        # For now, keeping it clean by providing the next commands.
    else:
        console.print(f"\n[bold green]✅ Project Ready in {project_dir}[/bold green]")


def main() -> None:
    app()
