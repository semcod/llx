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


def print_models_table(config, tag: str = None, provider: str = None, tier: str = None) -> None:
    """Print models table with optional filtering."""
    from rich.table import Table
    
    # Filter models
    filtered_models = {}
    for tier_name, model in config.models.items():
        # Apply filters
        if tier and tier_name != tier:
            continue
        if provider and model.provider != provider:
            continue
        if tag and tag.upper() not in [t.upper() for t in model.tags]:
            continue
        
        filtered_models[tier_name] = model
    
    if not filtered_models:
        filter_desc = []
        if tag: filter_desc.append(f"tag='{tag}'")
        if provider: filter_desc.append(f"provider='{provider}'")
        if tier: filter_desc.append(f"tier='{tier}'")
        
        console.print(f"[red]No models found for filter: {', '.join(filter_desc)}[/red]")
        return
    
    # Build title
    title_parts = ["Available Models"]
    if tag: title_parts.append(f"Tag: {tag.upper()}")
    if provider: title_parts.append(f"Provider: {provider}")
    if tier: title_parts.append(f"Tier: {tier}")
    
    model_table = Table(title=" | ".join(title_parts), show_header=True)
    model_table.add_column("Tier", style="bold", width=10)
    model_table.add_column("Model", width=20)
    model_table.add_column("Provider", width=12)
    model_table.add_column("Context", justify="right", width=8)
    model_table.add_column("Cost (1K in/out)", width=14)
    model_table.add_column("Tags", width=30)

    for tier_name, model in filtered_models.items():
        # Shorten model names for display
        display_name = model.model_id
        if len(display_name) > 18:
            # Split on first slash or dash to get shorter name
            if '/' in display_name:
                parts = display_name.split('/')
                if len(parts) > 1:
                    display_name = parts[-1]  # Take last part
            if '-' in display_name and len(display_name) > 18:
                display_name = display_name.split('-')[0]
            if len(display_name) > 18:
                display_name = display_name[:15] + "..."
        
        # Color code tags for better readability
        colored_tags = []
        for tag_item in model.tags:
            if tag_item in ["FREE", "FAST"]:
                colored_tags.append(f"[green]{tag_item}[/green]")
            elif tag_item in ["EXPENSIVE", "SLOW"]:
                colored_tags.append(f"[red]{tag_item}[/red]")
            elif tag_item in ["PROGRAMMING", "CODE_SPECIALIZED", "REFACTORING"]:
                colored_tags.append(f"[blue]{tag_item}[/blue]")
            elif tag_item in ["HIGH_QUALITY", "COMPLEX_REASONING"]:
                colored_tags.append(f"[magenta]{tag_item}[/magenta]")
            elif tag_item in ["OFFLINE", "PRIVATE"]:
                colored_tags.append(f"[cyan]{tag_item}[/cyan]")
            else:
                colored_tags.append(f"[yellow]{tag_item}[/yellow]")
        
        tags_colored = " ".join(colored_tags) if colored_tags else "—"
        
        model_table.add_row(
            tier_name, display_name, model.provider,
            f"{model.max_context:,}",
            f"${model.cost_per_1k_input:.4f} / ${model.cost_per_1k_output:.4f}",
            tags_colored,
        )
    console.print(model_table)

    # Show available tags
    all_tags = set()
    for model in config.models.values():
        all_tags.update(model.tags)
    
    if all_tags:
        console.print(f"\n[dim]Available tags for filtering: {', '.join(sorted(all_tags))}[/dim]")
        console.print("[dim]Usage: llx models <tag>  or  llx models --provider <provider>  or  llx models --tier <tier>[/dim]")


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
    model_table.add_column("Tier", style="bold", width=10)
    model_table.add_column("Model", width=20)
    model_table.add_column("Provider", width=12)
    model_table.add_column("Context", justify="right", width=8)
    model_table.add_column("Cost (1K in/out)", width=14)
    model_table.add_column("Tags", width=30)

    for tier_name, model in config.models.items():
        # Shorten model names for display
        display_name = model.model_id
        if len(display_name) > 18:
            # Split on first slash or dash to get shorter name
            if '/' in display_name:
                parts = display_name.split('/')
                if len(parts) > 1:
                    display_name = parts[-1]  # Take last part
            if '-' in display_name and len(display_name) > 18:
                display_name = display_name.split('-')[0]
            if len(display_name) > 18:
                display_name = display_name[:15] + "..."
        
        tags_str = ", ".join(model.tags) if model.tags else "—"
        # Color code tags for better readability
        colored_tags = []
        for tag in model.tags:
            if tag in ["FREE", "FAST"]:
                colored_tags.append(f"[green]{tag}[/green]")
            elif tag in ["EXPENSIVE", "SLOW"]:
                colored_tags.append(f"[red]{tag}[/red]")
            elif tag in ["PROGRAMMING", "CODE_SPECIALIZED", "REFACTORING"]:
                colored_tags.append(f"[blue]{tag}[/blue]")
            elif tag in ["HIGH_QUALITY", "COMPLEX_REASONING"]:
                colored_tags.append(f"[magenta]{tag}[/magenta]")
            elif tag in ["OFFLINE", "PRIVATE"]:
                colored_tags.append(f"[cyan]{tag}[/cyan]")
            else:
                colored_tags.append(f"[yellow]{tag}[/yellow]")
        
        tags_colored = " ".join(colored_tags) if colored_tags else "—"
        
        model_table.add_row(
            tier_name, display_name, model.provider,
            f"{model.max_context:,}",
            f"${model.cost_per_1k_input:.4f} / ${model.cost_per_1k_output:.4f}",
            tags_colored,
        )
    console.print(model_table)

    # Tags legend
    console.print("\n[bold]Tags Legend:[/bold]")
    tag_groups = [
        ("Cost & Speed", ["FREE", "FAST", "CHEAP", "EXPENSIVE", "SLOW"]),
        ("Capabilities", ["PROGRAMMING", "CODE_SPECIALIZED", "REFACTORING", "GENERATING", "ANALYSIS", "DEBUGGING"]),
        ("Quality", ["HIGH_QUALITY", "COMPLEX_REASONING", "RELIABLE"]),
        ("Environment", ["OFFLINE", "PRIVATE", "LARGE_CONTEXT"]),
        ("Use Case", ["QUICK_TASKS", "DOCUMENTATION", "CODE_COMPLETION", "ARCHITECTURE", "GENERAL_PURPOSE"]),
        ("Other", ["COST_EFFECTIVE", "BACKUP_OPTION"]),
    ]
    
    for group_name, tags in tag_groups:
        colored_tags = []
        for tag in tags:
            if tag in ["FREE", "FAST", "CHEAP"]:
                colored_tags.append(f"[green]{tag}[/green]")
            elif tag in ["EXPENSIVE", "SLOW"]:
                colored_tags.append(f"[red]{tag}[/red]")
            elif tag in ["PROGRAMMING", "CODE_SPECIALIZED", "REFACTORING", "GENERATING", "ANALYSIS", "DEBUGGING"]:
                colored_tags.append(f"[blue]{tag}[/blue]")
            elif tag in ["HIGH_QUALITY", "COMPLEX_REASONING", "RELIABLE"]:
                colored_tags.append(f"[magenta]{tag}[/magenta]")
            elif tag in ["OFFLINE", "PRIVATE", "LARGE_CONTEXT"]:
                colored_tags.append(f"[cyan]{tag}[/cyan]")
            else:
                colored_tags.append(f"[yellow]{tag}[/yellow]")
        
        console.print(f"  [dim]{group_name}:[/dim] {' '.join(colored_tags)}")

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
