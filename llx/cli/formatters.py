"""Output formatters for CLI.

Lesson from preLLM: to_stdout() had CC=28 because it mixed formatting,
coloring, and data extraction. Here each format is a dedicated function.
"""

from __future__ import annotations

import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llx.analysis.collector import ProjectMetrics
from llx.routing.selector import SelectionResult

console = Console()


def output_rich(metrics: ProjectMetrics, result: SelectionResult, verbose: bool) -> None:
    """Rich terminal output for analysis results."""
    metrics_text = (
        f"Files: {metrics.total_files}  Lines: {metrics.total_lines:,}  "
        f"Functions: {metrics.total_functions}\n"
        f"CC̄: {metrics.avg_cc:.1f}  Max CC: {metrics.max_cc}  "
        f"Critical: {metrics.critical_count}\n"
        f"Fan-out: {metrics.max_fan_out}  Cycles: {metrics.dependency_cycles}  "
        f"God modules: {metrics.god_modules}\n"
        f"Scope: {metrics.task_scope}  "
        f"Est. tokens: ~{metrics.estimated_context_tokens:,}"
    )
    if metrics.dup_groups > 0:
        metrics_text += f"\nDuplicate groups: {metrics.dup_groups} ({metrics.dup_saved_lines} lines)"

    console.print(Panel(metrics_text, title="Project Metrics", border_style="blue"))
    console.print(Panel(
        f"[bold green]{result.model_id}[/bold green]  (tier: {result.tier.value})",
        title="Selected Model", border_style="green",
    ))

    for reason in result.reasons:
        console.print(f"  • {reason}")

    if verbose:
        console.print(f"\n  [dim]Scores: complexity={result.scores['complexity']:.0f} "
                       f"scale={result.scores['scale']:.0f} "
                       f"coupling={result.scores['coupling']:.0f}[/dim]")
    if result.alternative_tier:
        console.print(f"\n  [dim]Alternative: {result.alternative_tier.value}[/dim]")


def output_json(metrics: ProjectMetrics, result: SelectionResult) -> None:
    """JSON output for machine consumption."""
    output = {
        "metrics": {
            "total_files": metrics.total_files,
            "total_lines": metrics.total_lines,
            "total_functions": metrics.total_functions,
            "avg_cc": metrics.avg_cc,
            "max_cc": metrics.max_cc,
            "critical_count": metrics.critical_count,
            "max_fan_out": metrics.max_fan_out,
            "dependency_cycles": metrics.dependency_cycles,
            "god_modules": metrics.god_modules,
            "dup_groups": metrics.dup_groups,
            "task_scope": metrics.task_scope,
            "estimated_tokens": metrics.estimated_context_tokens,
            "languages": metrics.languages,
        },
        "selection": {
            "tier": result.tier.value,
            "model_id": result.model_id,
            "reasons": result.reasons,
            "scores": result.scores,
        },
    }
    console.print(json.dumps(output, indent=2))


def print_info_tables(config) -> None:
    """Print tools and models info tables."""
    from llx.analysis.runner import check_tool

    tools_table = Table(title="Available Tools", show_header=True)
    tools_table.add_column("Tool", style="bold")
    tools_table.add_column("Status")
    tools_table.add_column("Purpose")

    for name, purpose in [
        ("code2llm", "Code analysis → .toon metrics"),
        ("redup", "Duplication detection"),
        ("vallm", "Code validation"),
        ("litellm", "LLM proxy / router"),
        ("ollama", "Local LLM server"),
    ]:
        status = "[green]✓ installed[/green]" if check_tool(name) else "[red]✗ not found[/red]"
        tools_table.add_row(name, status, purpose)
    console.print(tools_table)

    model_table = Table(title="Model Tiers", show_header=True)
    model_table.add_column("Tier", style="bold")
    model_table.add_column("Model")
    model_table.add_column("Provider")
    model_table.add_column("Context")
    model_table.add_column("Cost (1K in/out)")

    for tier_name, model in config.models.items():
        model_table.add_row(
            tier_name, model.model_id, model.provider,
            f"{model.max_context:,}",
            f"${model.cost_per_1k_input:.4f} / ${model.cost_per_1k_output:.4f}",
        )
    console.print(model_table)

    console.print("\n[bold]Compatible IDE/Agent Tools:[/bold]")
    for name, kind, hint in [
        ("Roo Code", "VS Code extension", "localhost:4000"),
        ("Cline", "VS Code extension", "localhost:4000"),
        ("Continue.dev", "VS Code / JetBrains", "localhost:4000"),
        ("Aider", "Terminal", "OPENAI_API_BASE=localhost:4000"),
        ("Claude Code", "Terminal", "ANTHROPIC_BASE_URL"),
        ("Cursor", "IDE", "OpenAI-compatible endpoint"),
        ("Windsurf", "IDE", "OpenAI-compatible endpoint"),
        ("avante.nvim", "Neovim", "localhost:4000"),
    ]:
        console.print(f"  • [cyan]{name}[/cyan] ({kind}) → {hint}")
