"""Formatting utilities for CLI output."""

from __future__ import annotations

from llx.analysis.collector import ProjectMetrics
from llx.routing.selector import SelectionResult


def _format_selection(selection: SelectionResult | None, selected_model_id: str) -> str:
    """Format model selection result for display.
    
    Args:
        selection: SelectionResult with tier, model, reasons, etc.
        selected_model_id: The selected model ID (used when selection is None).
    
    Returns:
        Formatted string for display in a panel.
    """
    if selection is None:
        return f"Model: {selected_model_id} (forced)\nTier: unknown"
    
    lines = [
        f"Model: {selection.model_id}",
        f"Tier: {selection.tier.value}",
        "",
        "Reasons:",
    ]
    for reason in selection.reasons:
        lines.append(f"  • {reason}")
    
    if selection.alternative_tier:
        lines.append(f"\nAlternative: {selection.alternative_tier.value}")
    
    return "\n".join(lines)


def _format_metrics(metrics: ProjectMetrics) -> str:
    """Format project metrics for display.
    
    Args:
        metrics: ProjectMetrics dataclass with all the metrics.
    
    Returns:
        Formatted string for display in a panel.
    """
    # Handle both dataclass and SimpleNamespace/other objects
    def get_attr(obj, name, default=0):
        return getattr(obj, name, default)
    
    lines = [
        "[bold]Structure:[/bold]",
        f"  Files: {get_attr(metrics, 'total_files')}",
        f"  Lines: {get_attr(metrics, 'total_lines'):,}",
        f"  Functions: {get_attr(metrics, 'total_functions')}",
        f"  Classes: {get_attr(metrics, 'total_classes')}",
        f"  Modules: {get_attr(metrics, 'total_modules')}",
        "",
        "[bold]Complexity:[/bold]",
        f"  Avg CC: {get_attr(metrics, 'avg_cc', 0.0):.2f}",
        f"  Max CC: {get_attr(metrics, 'max_cc')}",
        f"  Critical functions: {get_attr(metrics, 'critical_count')}",
        f"  God modules: {get_attr(metrics, 'god_modules')}",
        "",
        "[bold]Coupling:[/bold]",
        f"  Max fan-out: {get_attr(metrics, 'max_fan_out')}",
        f"  Max fan-in: {get_attr(metrics, 'max_fan_in')}",
        f"  Dep cycles: {get_attr(metrics, 'dependency_cycles')}",
        f"  Hotspots: {get_attr(metrics, 'hotspot_count')}",
        "",
        "[bold]Quality:[/bold]",
        f"  Duplication groups: {get_attr(metrics, 'dup_groups')}",
        f"  Duplicated lines: {get_attr(metrics, 'dup_saved_lines')}",
        f"  VallM pass rate: {get_attr(metrics, 'vallm_pass_rate', 1.0):.1%}",
        f"  VallM issues: {get_attr(metrics, 'vallm_issues')}",
        "",
        "[bold]Context:[/bold]",
        f"  Task scope: {get_attr(metrics, 'task_scope', 'unknown')}",
        f"  Est. tokens: {get_attr(metrics, 'estimated_context_tokens'):,}",
    ]
    
    languages = get_attr(metrics, 'languages', [])
    if languages:
        lines.append(f"  Languages: {', '.join(languages)}")
    
    return "\n".join(lines)
