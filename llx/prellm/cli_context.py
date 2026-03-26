"""CLI context inspection commands — extracted from cli.py.

This module contains the `context` command and context_app subcommands
for inspecting runtime environment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer


context_app = typer.Typer(
    name="context",
    help="Inspect runtime context — env vars, process, locale, network, codebase.",
    no_args_is_help=True,
)


def context(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    schema: bool = typer.Option(False, "--schema", help="Show generated context schema"),
    blocked: bool = typer.Option(False, "--blocked", help="Show blocked sensitive data"),
    folder: Optional[Path] = typer.Option(None, "--folder", "-f", help="Folder to compress for context"),
) -> None:
    """Show collected environment context, schema, and blocked sensitive data."""
    from llx.prellm.context.shell_collector import ShellContextCollector
    from llx.prellm.context.schema_generator import ContextSchemaGenerator
    from llx.prellm.context.sensitive_filter import SensitiveDataFilter

    collector = ShellContextCollector()
    shell_ctx = collector.collect_all()

    if json_output and not schema and not blocked:
        typer.echo(shell_ctx.model_dump_json(indent=2))
        return

    if schema:
        compressed = None
        if folder:
            from llx.prellm.context.folder_compressor import FolderCompressor
            compressed = FolderCompressor().compress(folder)
        gen = ContextSchemaGenerator()
        ctx_schema = gen.generate(shell_context=shell_ctx, folder_compressed=compressed)
        if json_output:
            typer.echo(ctx_schema.model_dump_json(indent=2))
        else:
            typer.echo(f"\n📋 Context Schema:")
            typer.echo(gen.to_prompt_section(ctx_schema))
            typer.echo(f"\n   Token cost: ~{ctx_schema.schema_token_cost}")
        return

    if blocked:
        all_vars = collector.collect_env_vars(safe_only=False)
        filt = SensitiveDataFilter()
        filt.filter_dict(all_vars)
        report = filt.get_filter_report()
        if json_output:
            typer.echo(report.model_dump_json(indent=2))
        else:
            typer.echo(f"\n🔒 Sensitive Filter Report:")
            typer.echo(f"   Blocked ({len(report.blocked_keys)}): {', '.join(report.blocked_keys[:15])}")
            typer.echo(f"   Masked  ({len(report.masked_keys)}): {', '.join(report.masked_keys[:15])}")
            typer.echo(f"   Safe    ({len(report.safe_keys)}): {len(report.safe_keys)} keys")
        return

    # Default: show shell context summary
    typer.echo(f"\n🧠 preLLM Environment Context")
    typer.echo(f"{'='*60}")
    typer.echo(f"   PID:      {shell_ctx.process.pid}")
    typer.echo(f"   CWD:      {shell_ctx.process.cwd}")
    typer.echo(f"   User:     {shell_ctx.process.user}")
    typer.echo(f"   Shell:    {shell_ctx.shell.shell}")
    typer.echo(f"   Term:     {shell_ctx.shell.term}")
    typer.echo(f"   Locale:   {shell_ctx.locale.lang}")
    typer.echo(f"   Timezone: {shell_ctx.locale.timezone}")
    typer.echo(f"   Hostname: {shell_ctx.network.hostname}")
    typer.echo(f"   Local IP: {shell_ctx.network.local_ip}")
    typer.echo(f"   Env vars: {len(shell_ctx.env_vars)} (safe only)")
    typer.echo(f"   Collected in: {shell_ctx.collection_duration_ms:.1f}ms")
    typer.echo(f"{'='*60}")


@context_app.command("show")
def context_show_cmd(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    schema: bool = typer.Option(False, "--schema", help="Show generated context schema"),
    blocked: bool = typer.Option(False, "--blocked", help="Show blocked sensitive data"),
    folder: Optional[Path] = typer.Option(None, "--folder", "-f", help="Folder to compress for context"),
):
    """Show collected runtime context.

    Example:
        prellm context show
        prellm context show --schema --folder ./src
        prellm context show --blocked
    """
    # Delegate to the main context function
    context(json_output=json_output, schema=schema, blocked=blocked, folder=folder)
