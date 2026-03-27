"""preLLM CLI — small LLM preprocessing before large LLM execution.

v0.5 refactor: commands split into cli_query, cli_context, cli_config, cli_commands modules.

Usage:
    prellm "Deploy app to prod" --small ollama/qwen2.5:3b --large gpt-4o-mini
    prellm "Refaktoryzuj kod" --strategy structure --json
"""

from typing import Optional
from pathlib import Path

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
) -> None:
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
) -> None:
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
) -> None:
    """Execute a DevOps process chain."""
    _process_cmd(config=config, guard_config=guard_config, dry_run=dry_run, json_output=json_output, env=env)


@app.command()
def decompose(
    query: str = typer.Argument(..., help="The prompt/query to decompose"),
    config: Path = typer.Option("configs/prellm_config.yaml", "--config", "-c", help="Path to preLLM v0.2 YAML config"),
    strategy: str = typer.Option("classify", "--strategy", "-s", help="Decomposition strategy"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """[v0.2] Decompose a query using small LLM without calling the large model."""
    _decompose_cmd(query=query, config=config, strategy=strategy, json_output=json_output)


@app.command()
def init(
    output: Path = typer.Option("prellm_config.yaml", "--output", "-o", help="Output path for config"),
    devops: bool = typer.Option(False, "--devops", help="Include DevOps-specific domain rules and context sources"),
) -> None:
    """Generate a starter preLLM config file."""
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
) -> None:
    """Start the OpenAI-compatible API server."""
    _serve_cmd(host=host, port=port, small=small, large=large, strategy=strategy, config=config, env_file=env_file, reload=reload)


@app.command()
def doctor(
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file"),
    live: bool = typer.Option(False, "--live", help="Test live connectivity to providers"),
) -> None:
    """Check configuration and provider connectivity."""
    _doctor_cmd(env_file=env_file, live=live)


@app.command()
def budget(
    reset: bool = typer.Option(False, "--reset", help="Reset current month's budget"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show LLM API spend tracking and budget status."""
    _budget_cmd(reset=reset, json_output=json_output)


@app.command()
def models(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search model name"),
) -> None:
    """List popular model pairs and provider examples."""
    _models_cmd(provider=provider, search=search)


# ============================================================
# Session management (kept in main cli.py as it's independent)
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
        typer.echo(f"\n💬 Session ({memory}): {len(interactions)} interactions")
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
        typer.echo(f"✅ Session exported to {output}")
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
        typer.echo(f"✅ Session imported from {input_file}")
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
        typer.echo(f"✅ Session cleared ({memory})")
    finally:
        mem.close()


if __name__ == "__main__":
    app()
