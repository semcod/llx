"""CLI miscellaneous commands — extracted from cli.py.

This module contains process, decompose, init, serve, doctor, budget, and models commands.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer


def process(
    config: Path = typer.Argument(..., help="Path to process chain YAML"),
    guard_config: Path = typer.Option("rules.yaml", "--guard-config", "-g", help="Path to guard YAML config"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Analyze steps without calling LLM"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment override (e.g., production)"),
) -> None:
    """Execute a DevOps process chain."""
    from llx.prellm.chains.process_chain import ProcessChain

    chain = ProcessChain(config_path=config, guard_config_path=guard_config)

    extra = {}
    if env:
        extra["env"] = env

    result = asyncio.run(chain.execute(extra_context=extra, dry_run=dry_run))

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(f"\n{'='*60}")
        typer.echo(f"🔗 Process: {result.process_name}")
        typer.echo(f"   Status: {'✅ Completed' if result.completed else '⏸️  Incomplete'}")
        typer.echo(f"   Duration: {result.total_duration_seconds:.2f}s")
        typer.echo(f"{'='*60}")
        for step in result.steps:
            icon = {
                "completed": "✅",
                "failed": "❌",
                "awaiting_approval": "⏳",
                "rolled_back": "↩️",
            }.get(step.status.value, "🔄")
            typer.echo(f"   {icon} {step.step_name}: {step.status.value} ({step.duration_seconds:.2f}s)")
            if step.error:
                typer.echo(f"      Error: {step.error}")
        typer.echo(f"{'='*60}")


def decompose(
    query: str = typer.Argument(..., help="The prompt/query to decompose"),
    config: Path = typer.Option("configs/prellm_config.yaml", "--config", "-c", help="Path to preLLM v0.2 YAML config"),
    strategy: str = typer.Option("classify", "--strategy", "-s", help="Decomposition strategy: classify|structure|split|enrich|passthrough"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """[v0.2] Decompose a query using small LLM without calling the large model."""
    from llx.prellm.core import PreLLM
    from llx.prellm.models import DecompositionStrategy

    engine = PreLLM(config_path=config)
    strat = DecompositionStrategy(strategy)

    result = asyncio.run(engine.decompose_only(query, strategy=strat))

    if json_output:
        typer.echo(json.dumps(result, indent=2, default=str))
    else:
        typer.echo(f"\n{'='*60}")
        typer.echo(f"🧠 preLLM Decomposition [{strategy}]")
        typer.echo(f"{'='*60}")
        typer.echo(f"   Original: {result['original_query']}")
        if result.get('classification'):
            c = result['classification']
            typer.echo(f"   Intent: {c['intent']} (confidence: {c['confidence']:.2f})")
            typer.echo(f"   Domain: {c['domain']}")
        if result.get('structure'):
            s = result['structure']
            typer.echo(f"   Action: {s['action']}, Target: {s['target']}")
        if result.get('sub_queries'):
            typer.echo(f"   Sub-queries: {result['sub_queries']}")
        if result.get('missing_fields'):
            typer.echo(f"   ⚠️  Missing: {', '.join(result['missing_fields'])}")
        if result.get('matched_rule'):
            typer.echo(f"   Matched rule: {result['matched_rule']}")
        typer.echo(f"   Composed: {result.get('composed_prompt', '')[:200]}")
        typer.echo(f"{'='*60}")


def init(
    output: Path = typer.Option("prellm_config.yaml", "--output", "-o", help="Output path for config"),
    devops: bool = typer.Option(False, "--devops", help="Include DevOps-specific domain rules and context sources"),
) -> None:
    """Generate a starter preLLM config file."""
    import yaml

    config = {
        "small_model": {"model": "phi3:mini", "fallback": ["qwen2:1.5b"], "max_tokens": 512, "temperature": 0.0},
        "large_model": {"model": "gpt-4o-mini", "fallback": ["llama3"], "max_tokens": 2048},
        "default_strategy": "classify",
        "policy": "devops" if devops else "strict",
        "domain_rules": [
            {"name": "production_deploy", "keywords": ["deploy", "push", "release"],
             "intent": "deploy", "required_fields": ["environment_details", "version"],
             "severity": "critical", "strategy": "structure"},
            {"name": "database_operation", "keywords": ["delete", "drop", "migrate"],
             "intent": "database", "required_fields": ["target_database", "backup_confirmed"],
             "severity": "critical", "strategy": "structure"},
        ] if devops else [],
        "context_sources": [
            {"env": ["CLUSTER", "NAMESPACE", "GIT_SHA", "ENV"]},
            {"git": ["branch", "short_sha", "last_commit_msg"]},
            {"system": ["hostname", "os"]},
        ] if devops else [],
    }

    with open(output, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    typer.echo(f"✅ Config written to {output}")


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
    """Start the OpenAI-compatible API server.

    Reads config from .env file (LiteLLM-compatible). CLI args override .env values.

    Example:
        prellm serve
        prellm serve --small ollama/qwen2.5:3b --large gpt-4o-mini --port 8080
    """
    import uvicorn
    from llx.prellm.env_config import get_env_config
    from llx.prellm.server import create_app
    from llx.prellm.cli_query import _init_logging

    env = get_env_config(str(env_file) if env_file else None)
    _init_logging()

    effective_small = small or env.small_model
    effective_large = large or env.large_model
    effective_strategy = strategy or env.strategy

    create_app(
        small_model=effective_small,
        large_model=effective_large,
        strategy=effective_strategy,
        config_path=str(config) if config else env.config_path,
        dotenv_path=str(env_file) if env_file else None,
    )

    auth_status = "ON (LITELLM_MASTER_KEY)" if env.master_key else "OFF (no key set)"

    typer.echo(f"\n🧠 preLLM API Server")
    typer.echo(f"   http://{host}:{port}")
    typer.echo(f"   Small: {effective_small} | Large: {effective_large}")
    typer.echo(f"   Strategy: {effective_strategy} | Auth: {auth_status}")
    typer.echo(f"   Endpoints: /v1/chat/completions, /v1/batch, /v1/models, /health")
    typer.echo(f"{'='*60}\n")

    uvicorn.run(
        "llx.prellm.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=env.log_level,
    )


def _doctor_check_config(env) -> list[str]:
    """Format configuration summary lines."""
    lines = [
        f"   Small LLM:  {env.small_model}",
        f"   Large LLM:  {env.large_model}",
        f"   Strategy:   {env.strategy}",
        f"   Server:     {env.host}:{env.port}",
        f"   Auth:       {'ON' if env.master_key else 'OFF (no LITELLM_MASTER_KEY)'}",
    ]
    if env.config_path:
        lines.append(f"   Config:     {env.config_path}")
    if env.fallbacks:
        lines.append(f"   Fallbacks:  {', '.join(env.fallbacks)}")
    if env.monthly_budget:
        lines.append(f"   Budget:     ${env.monthly_budget:.2f}/month")
    return lines


def _doctor_check_providers(env, live: bool = False) -> list[str]:
    """Check providers and return formatted lines."""
    from llx.prellm.env_config import check_providers

    if live:
        import asyncio
        from llx.prellm.env_config import check_providers_live
        results = asyncio.run(check_providers_live(env))
    else:
        results = check_providers(env)

    lines = []
    for name, info in results.items():
        status = info["status"]
        icon = "✓" if status in ("ok", "configured") else ("✗" if status == "no_key" else "!")
        lines.append(f"   {icon} {name.upper():12s} {info['detail']}")
        if "models" in info:
            lines.append(f"     Models: {', '.join(info['models'][:5])}")
    return lines


def _doctor_check_files(env_file: Path | None) -> list[str]:
    """Check config files and return formatted lines."""
    lines = []
    env_path = Path(str(env_file)) if env_file else Path(".env")
    if env_path.is_file():
        lines.append(f"   ✓ {env_path} (loaded)")
    else:
        lines.append(f"   ✗ {env_path} (not found — run: cp .env.example .env)")

    example_path = Path(".env.example")
    if example_path.is_file():
        lines.append(f"   ✓ .env.example (available)")
    else:
        lines.append(f"   ✗ .env.example (not found)")

    config_yaml = Path("configs/prellm_config.yaml")
    if config_yaml.is_file():
        lines.append(f"   ✓ {config_yaml}")
    return lines


def doctor(
    env_file: Optional[Path] = typer.Option(None, "--env-file", help="Path to .env file"),
    live: bool = typer.Option(False, "--live", help="Test live connectivity to providers"),
) -> None:
    """Check configuration and provider connectivity.

    Validates .env config, API keys, and optionally tests live connections.

    Example:
        prellm doctor
        prellm doctor --live
    """
    from llx.prellm.env_config import get_env_config

    env = get_env_config(str(env_file) if env_file else None)

    typer.echo(f"\n🧠 preLLM Doctor")
    typer.echo(f"{'='*60}")

    typer.echo(f"\n📋 Configuration:")
    for line in _doctor_check_config(env):
        typer.echo(line)

    typer.echo(f"\n🔌 Providers:")
    for line in _doctor_check_providers(env, live=live):
        typer.echo(line)

    typer.echo(f"\n📄 Files:")
    for line in _doctor_check_files(env_file):
        typer.echo(line)

    typer.echo(f"\n{'='*60}")
    typer.echo(f"✅ Doctor complete. Use --live to test connectivity.\n")


def budget(
    reset: bool = typer.Option(False, "--reset", help="Reset current month's budget"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show LLM API spend tracking and budget status.

    Example:
        prellm budget
        prellm budget --json
        prellm budget --reset
    """
    from llx.prellm.budget import get_budget_tracker
    from llx.prellm.env_config import get_env_config

    env = get_env_config()
    tracker = get_budget_tracker(monthly_limit=env.monthly_budget)

    if reset:
        tracker.reset()
        typer.echo("✅ Budget reset for current month.")
        return

    summary = tracker.summary()

    if json_output:
        import json
        typer.echo(json.dumps(summary, indent=2, default=str))
        return

    typer.echo(f"\n💰 preLLM Budget")
    typer.echo(f"{'='*60}")
    typer.echo(f"   Month:      {summary['month']}")
    typer.echo(f"   Spent:      ${summary['total_cost']:.4f}")
    if summary['monthly_limit'] is not None:
        typer.echo(f"   Limit:      ${summary['monthly_limit']:.2f}")
        typer.echo(f"   Remaining:  ${summary['remaining']:.4f}")
        pct = (summary['total_cost'] / summary['monthly_limit'] * 100) if summary['monthly_limit'] > 0 else 0
        bar_len = 30
        filled = int(bar_len * min(pct, 100) / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        typer.echo(f"   Usage:      [{bar}] {pct:.1f}%")
    else:
        typer.echo(f"   Limit:      not set (PRELLM_MONTHLY_BUDGET)")
    typer.echo(f"   Requests:   {summary['requests']}")

    if summary['by_model']:
        typer.echo(f"\n   By model:")
        for model, cost in sorted(summary['by_model'].items(), key=lambda x: -x[1]):
            typer.echo(f"     {model}: ${cost:.4f}")

    typer.echo(f"\n{'='*60}")


def models(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider (e.g. openrouter, ollama, openai)"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search model name"),
) -> None:
    """List popular model pairs and provider examples.

    Examples:
        prellm models
        prellm models --provider openrouter
        prellm models --search kimi
    """
    from llx.prellm.model_catalog import list_model_pairs, list_openrouter_models

    pairs = list_model_pairs(provider=provider, search=search)
    or_models = list_openrouter_models(provider=provider, search=search)

    typer.echo(f"\n🤖 preLLM Model Pairs")
    typer.echo(f"{'='*60}")

    if pairs:
        typer.echo(f"\n{'Name':<25s} {'Small LLM':<30s} {'Large LLM':<45s} {'Cost':>6s}")
        typer.echo(f"{'-'*25} {'-'*30} {'-'*45} {'-'*6}")
        for m in pairs:
            typer.echo(f"{m['name']:<25s} {m['small']:<30s} {m['large']:<45s} {m['cost']:>6s}")

    if or_models:
        typer.echo(f"\n🌐 OpenRouter Models (use with --large):")
        for m in or_models:
            typer.echo(f"   {m['model_id']}")
            typer.echo(f"      {m['description']}")

    typer.echo(f"\n💡 Usage:")
    typer.echo(f'   prellm "Deploy app" --large openrouter/moonshotai/kimi-k2.5')
    typer.echo(f"   prellm config set model openrouter/moonshotai/kimi-k2.5")
    typer.echo(f"   prellm config set openrouter-key sk-or-v1-abc123")
    typer.echo(f"\n{'='*60}")
