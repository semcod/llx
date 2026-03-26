"""preLLM CLI — small LLM preprocessing before large LLM execution.

v0.5 refactor: commands split into cli_query, cli_context, cli_config, cli_commands modules.

Usage:
    prellm "Deploy app to prod" --small ollama/qwen2.5:3b --large gpt-4o-mini
    prellm "Refaktoryzuj kod" --strategy structure --json
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

# Import command handlers from split modules
from llx.prellm.cli_query import (
    query as _query_cmd,
    _init_logging,
)
from llx.prellm.cli_context import context_app
from llx.prellm.cli_config import config_app
from llx.prellm.cli_commands import (
    process as _process_cmd,
    decompose as _decompose_cmd,
    init as _init_cmd,
    serve as _serve_cmd,
    doctor as _doctor_cmd,
    budget as _budget_cmd,
    models as _models_cmd,
)

app = typer.Typer(
    name="prellm",
    help="preLLM — Small LLM preprocessing before large LLM execution. Like litellm.completion() but with decomposition.",
    no_args_is_help=True,
)

# Register sub-apps
app.add_typer(config_app, name="config")
app.add_typer(context_app, name="context")

    prompt: str,
    small: Optional[str],
    large: Optional[str], 
    strategy: Optional[str],
    context: Optional[str],
    config: Optional[Path],
    memory: Optional[Path],
    codebase: Optional[Path],
    collect_env: bool,
    compress_folder: Optional[Path],
    no_sanitize: bool,
    show_schema: bool,
    show_blocked: bool,
    json_output: bool,
    trace: bool,
    trace_dir: Optional[Path],
    env_file: Optional[Path],
) -> dict:
    """Process and validate CLI query options."""
    from llx.prellm.env_config import get_env_config
    
    env = get_env_config(str(env_file) if env_file else None)
    effective_small = small or env.small_model
    effective_large = large or env.large_model
    effective_strategy = strategy or env.strategy
    
    effective_codebase = str(codebase) if codebase else (str(compress_folder) if compress_folder else None)
    do_sanitize = not no_sanitize
    do_compress = compress_folder is not None
    
    return {
        "prompt": prompt,
        "small_llm": effective_small,
        "large_llm": effective_large,
        "strategy": effective_strategy,
        "user_context": context,
        "config_path": str(config) if config else None,
        "memory_path": str(memory) if memory else None,
        "codebase_path": effective_codebase,
        "collect_env": collect_env,
        "compress_folder": do_compress,
        "sanitize": do_sanitize,
        "trace": trace,
        "trace_dir": trace_dir,
        "json_output": json_output,
        "show_schema": show_schema,
        "show_blocked": show_blocked,
        "compress_folder_path": compress_folder,
        "env": env,
    }


    """Show schema and blocked sensitive fields if requested."""
    collect_env = options["collect_env"]
    compress_folder = options["compress_folder_path"]
    show_schema = options["show_schema"]
    show_blocked = options["show_blocked"]
    do_compress = options["compress_folder"]
    
    # Show schema before execution if requested
    if show_schema and (collect_env or do_compress):
        from llx.prellm.context.shell_collector import ShellContextCollector
        from llx.prellm.context.schema_generator import ContextSchemaGenerator
        from llx.prellm.context.folder_compressor import FolderCompressor

        shell_ctx = ShellContextCollector().collect_all() if collect_env else None
        compressed = FolderCompressor().compress(compress_folder) if compress_folder else None
        schema = ContextSchemaGenerator().generate(shell_context=shell_ctx, folder_compressed=compressed)
        typer.echo(f"\n📋 Context Schema:")
        typer.echo(schema.model_dump_json(indent=2))
        typer.echo("")

    # Show blocked fields if requested
    if show_blocked and collect_env:
        from llx.prellm.context.shell_collector import ShellContextCollector
        from llx.prellm.context.sensitive_filter import SensitiveDataFilter

        collector = ShellContextCollector()
        all_vars = collector.collect_env_vars(safe_only=False)
        filt = SensitiveDataFilter()
        filt.filter_dict(all_vars)
        report = filt.get_filter_report()
        typer.echo(f"\n🔒 Sensitive Filter Report:")
        typer.echo(f"   Blocked:  {len(report.blocked_keys)} — {', '.join(report.blocked_keys[:10])}")
        typer.echo(f"   Masked:   {len(report.masked_keys)} — {', '.join(report.masked_keys[:10])}")
        typer.echo(f"   Safe:     {len(report.safe_keys)}")
        typer.echo("")


    """Initialize budget tracker and trace recorder."""
    from llx.prellm.trace import TraceRecorder
    from llx.prellm.budget import get_budget_tracker
    
    env = options["env"]
    trace = options["trace"]
    trace_dir = options["trace_dir"]
    
    # Initialize budget tracker if configured
    if env.monthly_budget:
        get_budget_tracker(monthly_limit=env.monthly_budget)

    # Start trace if requested
    recorder = None
    if trace:
        recorder = TraceRecorder(output_dir=Path(trace_dir) if trace_dir else Path(".prellm"))
        recorder.start(
            query=options["prompt"],
            small_llm=options["small_llm"],
            large_llm=options["large_llm"],
            strategy=options["strategy"],
        )
    
    return recorder


    """Execute the query and format output."""
    from llx.prellm.core import preprocess_and_execute
    
    result = asyncio.run(preprocess_and_execute(
        query=options["prompt"],
        small_llm=options["small_llm"],
        large_llm=options["large_llm"],
        strategy=options["strategy"],
        user_context=options["user_context"],
        config_path=options["config_path"],
        memory_path=options["memory_path"],
        codebase_path=options["codebase_path"],
        collect_env=options["collect_env"],
        compress_folder=options["compress_folder"],
        sanitize=options["sanitize"],
    ))

    # Stop trace and output
    if recorder:
        recorder.stop()
        # Print compact trace to stdout
        typer.echo(recorder.to_stdout())
        # Save full markdown trace
        filepath = recorder.save()
        typer.echo(f"📄 Trace saved: {filepath}")

    if options["json_output"]:
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(f"\n{'='*60}")
        typer.echo(f"\U0001f9e0 preLLM [{options['small_llm']} \u2192 {options['large_llm']}]")
        typer.echo(f"{'='*60}")
        if result.decomposition and result.decomposition.classification:
            c = result.decomposition.classification
            typer.echo(f"   Intent: {c.intent} (confidence: {c.confidence:.2f})")
        if result.decomposition and result.decomposition.matched_rule:
            typer.echo(f"   Rule: {result.decomposition.matched_rule}")
        if result.decomposition and result.decomposition.missing_fields:
            typer.echo(f"   ⚠️  Missing: {', '.join(result.decomposition.missing_fields)}")
        typer.echo(f"{'='*60}")
        typer.echo(f"\n{result.content}")
        typer.echo(f"\n{'='*60}")
        typer.echo(f"   Small: {result.small_model_used} | Large: {result.model_used} | Retries: {result.retries}")
        typer.echo(f"{'='*60}")


@app.command()
def query(
    prompt: str = typer.Argument(..., help="The prompt/query to preprocess and execute"),
    small: Optional[str] = typer.Option(None, "--small", "-s", help="Small LLM for preprocessing (default: from .env)"),
    large: Optional[str] = typer.Option(None, "--large", "-l", help="Large LLM for execution (default: from .env)"),
    strategy: Optional[str] = typer.Option(None, "--strategy", "-S", help="Strategy: classify|structure|split|enrich|passthrough (default: from .env)"),
    context: Optional[str] = typer.Option(None, "--context", "-C", help="User context tag (e.g. 'gdansk_embedded_python')"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Optional YAML config file"),
    memory: Optional[Path] = typer.Option(None, "--memory", "-m", help="Path to UserMemory database"),
    codebase: Optional[Path] = typer.Option(None, "--codebase", help="Path to codebase root for context indexing"),
    collect_env: bool = typer.Option(False, "--collect-env", help="Collect full shell environment context"),
    compress_folder: Optional[Path] = typer.Option(None, "--compress-folder", help="Compress folder for context (path)"),
    no_sanitize: bool = typer.Option(False, "--no-sanitize", help="Disable sensitive data filtering (dev only)"),
    show_schema: bool = typer.Option(False, "--show-schema", help="Show generated context schema (debug)"),
    show_blocked: bool = typer.Option(False, "--show-blocked", help="Show blocked sensitive fields"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    trace: bool = typer.Option(False, "--trace", "-t", help="Generate markdown execution trace (.prellm/)"),
    trace_dir: Optional[Path] = typer.Option(None, "--trace-dir", help="Trace output directory (default: .prellm)"),
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file (default: .env)"),
):
    """Preprocess a query with small LLM, then execute with large LLM."""
    _init_logging()
    _query_cmd(
        prompt=prompt,
        small=small,
        large=large,
        strategy=strategy,
        context=context,
        config=config,
        memory=memory,
        codebase=codebase,
        collect_env=collect_env,
        compress_folder=compress_folder,
        no_sanitize=no_sanitize,
        show_schema=show_schema,
        show_blocked=show_blocked,
        json_output=json_output,
        trace=trace,
        trace_dir=trace_dir,
        env_file=env_file,
    )


@app.command()
def context(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    schema: bool = typer.Option(False, "--schema", help="Show generated context schema"),
    blocked: bool = typer.Option(False, "--blocked", help="Show blocked sensitive data"),
    folder: Optional[Path] = typer.Option(None, "--folder", "-f", help="Folder to compress for context"),
):
    """Show collected environment context, schema, and blocked sensitive data."""
    from llx.prellm.cli_context import context as _context_cmd
    _context_cmd(json_output=json_output, schema=schema, blocked=blocked, folder=folder)


@app.command()
def process(
    config: Path = typer.Argument(..., help="Path to process chain YAML"),
    guard_config: Path = typer.Option("rules.yaml", "--guard-config", "-g", help="Path to guard YAML config"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Analyze steps without calling LLM"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment override (e.g., production)"),
):
    """Execute a DevOps process chain."""
    from llx.prellm.cli_commands import process as _process_cmd
    _process_cmd(config=config, guard_config=guard_config, dry_run=dry_run, json_output=json_output, env=env)


@app.command()
def decompose(
    query: str = typer.Argument(..., help="The prompt/query to decompose"),
    config: Path = typer.Option("configs/prellm_config.yaml", "--config", "-c", help="Path to preLLM v0.2 YAML config"),
    strategy: str = typer.Option("classify", "--strategy", "-s", help="Decomposition strategy"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """[v0.2] Decompose a query using small LLM without calling the large model."""
    from llx.prellm.cli_commands import decompose as _decompose_cmd
    _decompose_cmd(query=query, config=config, strategy=strategy, json_output=json_output)


@app.command()
def init(
    output: Path = typer.Option("prellm_config.yaml", "--output", "-o", help="Output path for config"),
    devops: bool = typer.Option(False, "--devops", help="Include DevOps-specific domain rules and context sources"),
):
    """Generate a starter preLLM config file."""
    from llx.prellm.cli_commands import init as _init_cmd
    _init_cmd(output=output, devops=devops)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-H", help="Bind host"),
    port: int = typer.Option(8080, "--port", "-p", help="Bind port"),
    small: Optional[str] = typer.Option(None, "--small", "-s", help="Override small LLM (default: from .env)"),
    large: Optional[str] = typer.Option(None, "--large", "-l", help="Override large LLM (default: from .env)"),
    strategy: Optional[str] = typer.Option(None, "--strategy", "-S", help="Override strategy (default: from .env)"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="YAML config file"),
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file (default: .env)"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on code changes (dev mode)"),
):
    """Start the OpenAI-compatible API server."""
    from llx.prellm.cli_commands import serve as _serve_cmd
    _serve_cmd(host=host, port=port, small=small, large=large, strategy=strategy, config=config, env_file=env_file, reload=reload)


@app.command()
def doctor(
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file"),
    live: bool = typer.Option(False, "--live", help="Test live connectivity to providers"),
):
    """Check configuration and provider connectivity."""
    from llx.prellm.cli_commands import doctor as _doctor_cmd
    _doctor_cmd(env_file=env_file, live=live)


# ============================================================
# Config management
# ============================================================

config_app = typer.Typer(
    name="config",
    help="Manage preLLM configuration — API keys, models, defaults.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set_cmd(
    key: str = typer.Argument(..., help="Config key (e.g. openrouter-key, model, small-model, strategy)"),
    value: str = typer.Argument(..., help="Value to set"),
    global_: bool = typer.Option(False, "--global", "-g", help="Save to ~/.prellm/.env (user-wide) instead of project .env"),
):
    """Set a config value persistently.

    Saves to .env (project) or ~/.prellm/.env (--global).

    Examples:
        prellm config set openrouter-key sk-or-v1-abc123
        prellm config set model openrouter/moonshotai/kimi-k2.5
        prellm config set small-model ollama/qwen2.5:3b
        prellm config set strategy structure
        prellm config set openrouter-key sk-or-v1-abc123 --global
    """
    from llx.prellm.env_config import config_set, mask_value, resolve_alias

    env_var, path = config_set(key, value, global_=global_)
    masked = mask_value(env_var, value)
    typer.echo(f"\u2705 {env_var}={masked}")
    typer.echo(f"   Saved to: {path}")


@config_app.command("get")
def config_get_cmd(
    key: str = typer.Argument(..., help="Config key (e.g. openrouter-key, model, small-model)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Show unmasked value"),
):
    """Get a config value.

    Examples:
        prellm config get openrouter-key
        prellm config get model
        prellm config get small-model
    """
    from llx.prellm.env_config import config_get, mask_value

    env_var, val, source = config_get(key)
    if val is None:
        typer.echo(f"\u2717 {env_var} — not set")
        typer.echo(f"   Set with: prellm config set {key} <value>")
        raise typer.Exit(1)
    displayed = val if raw else mask_value(env_var, val)
    typer.echo(f"{env_var}={displayed}")
    typer.echo(f"   Source: {source}")


def _format_config_sections(entries: dict) -> dict[str, list[str]]:
    """Group config entries into categorized sections for display."""
    sections: dict[str, list[str]] = {
        "\U0001f511 API Keys": [],
        "\U0001f916 Models": [],
        "\u2699\ufe0f  Settings": [],
        "\U0001f4cb Other": [],
    }
    for var, info in entries.items():
        alias = f" ({info['alias']})" if info["alias"] else ""
        line = f"   {var}{alias} = {info['value']}  [{info['source']}]"
        if "API_KEY" in var or "SECRET" in var or var == "LITELLM_MASTER_KEY":
            sections["\U0001f511 API Keys"].append(line)
        elif "MODEL" in var or "DEFAULT" in var:
            sections["\U0001f916 Models"].append(line)
        elif var.startswith("PRELLM_"):
            sections["\u2699\ufe0f  Settings"].append(line)
        else:
            sections["\U0001f4cb Other"].append(line)
    return sections


@config_app.command("list")
def config_list_cmd(
    raw: bool = typer.Option(False, "--raw", "-r", help="Show unmasked secret values"),
):
    """List all configured values.

    Example:
        prellm config list
        prellm config list --raw
    """
    from llx.prellm.env_config import config_list

    entries = config_list(show_secrets=raw)
    if not entries:
        typer.echo("No config values set.")
        typer.echo("   Set with: prellm config set <key> <value>")
        typer.echo("   Example:  prellm config set openrouter-key sk-or-v1-abc123")
        return

    typer.echo(f"\n\U0001f9e0 preLLM Configuration")
    typer.echo(f"{'='*60}")

    for title, lines in _format_config_sections(entries).items():
        if lines:
            typer.echo(f"\n{title}:")
            for line in lines:
                typer.echo(line)

    typer.echo(f"\n{'='*60}")


@config_app.command("show")
def config_show_cmd():
    """Show effective configuration (resolved from all sources).

    Example:
        prellm config show
    """
    from llx.prellm.env_config import get_env_config, mask_value

    env = get_env_config()
    typer.echo(f"\n\U0001f9e0 preLLM Effective Configuration")
    typer.echo(f"{'='*60}")
    typer.echo(f"   Small LLM:     {env.small_model}")
    typer.echo(f"   Large LLM:     {env.large_model}")
    typer.echo(f"   Strategy:      {env.strategy}")
    typer.echo(f"   Server:        {env.host}:{env.port}")
    typer.echo(f"   Auth:          {'ON' if env.master_key else 'OFF'}")
    typer.echo(f"   Log level:     {env.log_level}")
    typer.echo(f"   Max tokens:    {env.max_tokens}")
    typer.echo(f"   Timeout:       {env.timeout}s")
    if env.fallbacks:
        typer.echo(f"   Fallbacks:     {', '.join(env.fallbacks)}")
    if env.monthly_budget:
        typer.echo(f"   Budget:        ${env.monthly_budget:.2f}/month")
    if env.config_path:
        typer.echo(f"   Config file:   {env.config_path}")

    typer.echo(f"\n\U0001f50c Providers:")
    for name, info in env.providers.items():
        if info["has_key"] or name == "ollama":
            typer.echo(f"   \u2713 {name.upper():14s} {info.get('base_url', '')}")
        else:
            typer.echo(f"   \u2717 {name.upper():14s} ({info.get('key_var', '')} not set)")

    typer.echo(f"\n{'='*60}")


@config_app.command("init-env")
def config_init_env(
    global_: bool = typer.Option(False, "--global", "-g", help="Create ~/.prellm/.env instead of project .env"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
):
    """Generate a starter .env file with all available settings.

    Example:
        prellm config init-env
        prellm config init-env --global
    """
    from llx.prellm.env_config import _resolve_config_path

    path = _resolve_config_path(global_)
    if path.is_file() and not force:
        typer.echo(f"\u26a0\ufe0f  {path} already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    path.parent.mkdir(parents=True, exist_ok=True)
    template = """\
# preLLM Configuration
# Generated by: prellm config init-env
# Docs: https://github.com/wronai/prellm

# ── Models ──────────────────────────────────────────────
PRELLM_SMALL_DEFAULT=ollama/qwen2.5:3b
PRELLM_LARGE_DEFAULT=gpt-4o-mini
PRELLM_STRATEGY=classify

# ── API Keys (uncomment and fill in) ───────────────────
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GROQ_API_KEY=gsk_...
# MISTRAL_API_KEY=...
# OPENROUTER_API_KEY=sk-or-v1-...
# DEEPSEEK_API_KEY=...
# TOGETHERAI_API_KEY=...
# GEMINI_API_KEY=...
# MOONSHOT_API_KEY=...

# ── Azure OpenAI ───────────────────────────────────────
# AZURE_API_KEY=...
# AZURE_API_BASE=https://your-resource.openai.azure.com
# AZURE_API_VERSION=2024-02-01

# ── AWS Bedrock ────────────────────────────────────────
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION_NAME=us-east-1

# ── Ollama (local) ─────────────────────────────────────
# OLLAMA_API_BASE=http://localhost:11434

# ── OpenRouter ─────────────────────────────────────────
# OPENROUTER_API_BASE=https://openrouter.ai/api/v1

# ── Server ─────────────────────────────────────────────
# PRELLM_HOST=0.0.0.0
# PRELLM_PORT=8080
# PRELLM_LOG_LEVEL=info
# LITELLM_MASTER_KEY=sk-prellm-...

# ── Limits ─────────────────────────────────────────────
# PRELLM_MAX_TOKENS=4096
# PRELLM_TIMEOUT=30
# PRELLM_MONTHLY_BUDGET=50.00
# PRELLM_FALLBACKS=ollama/llama3:8b,gpt-4o-mini
"""
    with open(path, "w") as f:
        f.write(template)

    typer.echo(f"\u2705 Created {path}")
    typer.echo(f"   Edit the file to add your API keys.")


# ============================================================
# Budget
# ============================================================

@app.command()
def budget(
    reset: bool = typer.Option(False, "--reset", help="Reset current month's budget"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Show LLM API spend tracking and budget status."""
    from llx.prellm.cli_commands import budget as _budget_cmd
    _budget_cmd(reset=reset, json_output=json_output)


# ============================================================
# Models
# ============================================================

@app.command()
def models(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search model name"),
):
    """List popular model pairs and provider examples."""
    from llx.prellm.cli_commands import models as _models_cmd
    _models_cmd(provider=provider, search=search)


# ============================================================
# Context inspection
# ============================================================

context_app = typer.Typer(
    name="context",
    help="Inspect runtime context — env vars, process, locale, network, codebase.",
    no_args_is_help=True,
)
app.add_typer(context_app, name="context")


@context_app.command("show")
def context_show_cmd(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    blocked: bool = typer.Option(False, "--blocked", help="Show what was blocked by sensitive filter"),
    codebase: Optional[Path] = typer.Option(None, "--codebase", help="Show compressed codebase context"),
):
    """Show collected runtime context."""
    from llx.prellm.analyzers.context_engine import ContextEngine

    _init_logging()

    engine = ContextEngine()
    runtime = engine.gather_runtime()

    if json_output:
        typer.echo(runtime.model_dump_json(indent=2))
        return

    typer.echo(f"\n\U0001f9e0 preLLM Runtime Context")
    typer.echo(f"{'='*60}")
    typer.echo(f"   Collected at: {runtime.collected_at}")
    typer.echo(f"   Token estimate: {runtime.token_estimate}")
    typer.echo(f"   Sensitive blocked: {runtime.sensitive_blocked_count}")

    typer.echo(f"\n\U0001f4bb Process:")
    for k, v in runtime.process.items():
        typer.echo(f"   {k}: {v}")

    typer.echo(f"\n\U0001f30d Locale:")
    for k, v in runtime.locale.items():
        typer.echo(f"   {k}: {v}")

    typer.echo(f"\n\U0001f310 Network:")
    for k, v in runtime.network.items():
        typer.echo(f"   {k}: {v}")

    typer.echo(f"\n\u2699\ufe0f  System:")
    for k, v in runtime.system.items():
        typer.echo(f"   {k}: {v}")

    if runtime.git:
        typer.echo(f"\n\U0001f500 Git:")
        for k, v in runtime.git.items():
            typer.echo(f"   {k}: {v}")

    typer.echo(f"\n\U0001f512 Safe env vars: {len(runtime.env_safe)}")
    if blocked:
        typer.echo(f"   (showing first 20)")
        for i, (k, v) in enumerate(runtime.env_safe.items()):
            if i >= 20:
                typer.echo(f"   ... and {len(runtime.env_safe) - 20} more")
                break
            typer.echo(f"   {k}={v[:60]}{'...' if len(v) > 60 else ''}")

    if codebase:
        from llx.prellm.context.codebase_indexer import CodebaseIndexer
        indexer = CodebaseIndexer()
        compressed = indexer.get_compressed_context(str(codebase), "project overview", max_tokens=2048)
        typer.echo(f"\n\U0001f4c2 Codebase ({codebase}):")
        typer.echo(compressed)

    typer.echo(f"\n{'='*60}")


# ============================================================
# Session management
# ============================================================

session_app = typer.Typer(
    name="session",
    help="Manage persistent sessions — export, import, list, clear.",
    no_args_is_help=True,
)
app.add_typer(session_app, name="session")


@session_app.command("list")
def session_list_cmd(
    memory: Path = typer.Option(".prellm/user_memory.db", "--memory", "-m", help="Path to memory database"),
):
    """List recent interactions in the session."""
    from llx.prellm.context.user_memory import UserMemory

    _init_logging()
    mem = UserMemory(path=str(memory))
    try:
        import asyncio
        interactions = asyncio.run(mem._get_all_interactions(limit=20))
        if not interactions:
            typer.echo("No interactions found.")
            return
        typer.echo(f"\n\U0001f4ac Session ({memory}): {len(interactions)} interactions")
        typer.echo(f"{'='*60}")
        for i, item in enumerate(interactions, 1):
            q = item.get("query", "")[:80]
            r = item.get("response_summary", "")[:60]
            typer.echo(f"   {i}. Q: {q}")
            typer.echo(f"      A: {r}...")
        typer.echo(f"{'='*60}")
    finally:
        mem.close()


@session_app.command("export")
def session_export_cmd(
    output: Path = typer.Argument(..., help="Output JSON file path"),
    memory: Path = typer.Option(".prellm/user_memory.db", "--memory", "-m", help="Path to memory database"),
    session_id: Optional[str] = typer.Option(None, "--id", help="Session ID (default: auto-generated)"),
):
    """Export current session to JSON file."""
    import asyncio
    from llx.prellm.context.user_memory import UserMemory

    _init_logging()
    mem = UserMemory(path=str(memory))
    try:
        snapshot = asyncio.run(mem.export_session(session_id=session_id))
        snapshot.to_file(output)
        typer.echo(f"\u2705 Session exported to {output}")
        typer.echo(f"   ID: {snapshot.session_id}")
        typer.echo(f"   Interactions: {len(snapshot.interactions)}")
        typer.echo(f"   Preferences: {len(snapshot.preferences)}")
    finally:
        mem.close()


@session_app.command("import")
def session_import_cmd(
    input_file: Path = typer.Argument(..., help="JSON file to import"),
    memory: Path = typer.Option(".prellm/user_memory.db", "--memory", "-m", help="Path to memory database"),
):
    """Import a session from JSON file."""
    import asyncio
    from llx.prellm.context.user_memory import UserMemory
    from llx.prellm.models import SessionSnapshot

    _init_logging()
    snapshot = SessionSnapshot.from_file(input_file)
    mem = UserMemory(path=str(memory))
    try:
        asyncio.run(mem.import_session(snapshot))
        typer.echo(f"\u2705 Session imported from {input_file}")
        typer.echo(f"   ID: {snapshot.session_id}")
        typer.echo(f"   Interactions: {len(snapshot.interactions)}")
    finally:
        mem.close()


@session_app.command("clear")
def session_clear_cmd(
    memory: Path = typer.Option(".prellm/user_memory.db", "--memory", "-m", help="Path to memory database"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clear all session data."""
    import asyncio
    from llx.prellm.context.user_memory import UserMemory

    if not force:
        typer.confirm("This will delete all session data. Continue?", abort=True)

    _init_logging()
    mem = UserMemory(path=str(memory))
    try:
        asyncio.run(mem.clear())
        typer.echo(f"\u2705 Session cleared ({memory})")
    finally:
        mem.close()


if __name__ == "__main__":
    app()
