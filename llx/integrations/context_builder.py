"""Build compact LLM context from code2llm analysis outputs.

Reads .toon files and produces a context string optimized for the
selected model's context window. Larger models get more detail;
smaller models get a compressed summary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llx.analysis.collector import ProjectMetrics
from llx.routing.selector import ModelTier


def build_context(
    project_path: Path,
    metrics: ProjectMetrics,
    tier: ModelTier,
    *,
    toon_dir: Path | None = None,
    max_tokens: int | None = None,
) -> str:
    """Build a context string from analysis files, sized to the model tier.

    Args:
        project_path: Project root.
        metrics: Pre-computed project metrics.
        tier: Selected model tier (determines verbosity).
        toon_dir: Directory with .toon/.yaml files.
        max_tokens: Hard token limit for context.

    Returns:
        Formatted context string for LLM consumption.
    """
    search_dir = toon_dir or project_path
    sections: list[str] = []

    # Always include: project summary
    sections.append(_build_summary(metrics))

    # Include health/complexity for balanced+
    if tier in (ModelTier.BALANCED, ModelTier.PREMIUM):
        analysis = _load_toon(search_dir, "analysis.toon.yaml")
        if analysis:
            sections.append(_format_health(analysis))

    # Include evolution queue for premium
    if tier == ModelTier.PREMIUM:
        evolution = _load_toon(search_dir, "evolution.toon.yaml")
        if evolution:
            sections.append(_format_evolution(evolution))

        map_data = _load_toon(search_dir, "map.toon.yaml")
        if map_data:
            sections.append(_format_map_details(map_data))

    # Include duplication for balanced+
    if tier in (ModelTier.BALANCED, ModelTier.PREMIUM) and metrics.dup_groups > 0:
        sections.append(_format_duplication(metrics))

    context = "\n\n---\n\n".join(sections)

    # Trim if exceeding token budget
    if max_tokens:
        estimated = len(context) // 4
        if estimated > max_tokens:
            # Aggressive truncation: keep only summary + health
            context = "\n\n---\n\n".join(sections[:2])
            context += f"\n\n[Context trimmed to ~{max_tokens} tokens]"

    return context


def _build_summary(m: ProjectMetrics) -> str:
    """Build the always-included project summary."""
    lines = [
        "# Project Analysis Summary",
        "",
        f"- **Files**: {m.total_files} ({', '.join(m.languages)})",
        f"- **Lines**: {m.total_lines:,}",
        f"- **Functions**: {m.total_functions} | **Classes**: {m.total_classes}",
        f"- **Avg CC**: {m.avg_cc:.1f} | **Max CC**: {m.max_cc}",
        f"- **Critical functions** (CC≥15): {m.critical_count}",
        f"- **God modules**: {m.god_modules}",
        f"- **Max fan-out**: {m.max_fan_out} | **Cycles**: {m.dependency_cycles}",
        f"- **Scope**: {m.task_scope}",
        f"- **Estimated context**: ~{m.estimated_context_tokens:,} tokens",
    ]
    if m.dup_groups > 0:
        lines.append(f"- **Duplicate groups**: {m.dup_groups} ({m.dup_saved_lines} lines recoverable)")
    if m.vallm_issues > 0:
        lines.append(f"- **Validation issues**: {m.vallm_issues} ({m.vallm_pass_rate:.0%} pass rate)")
    return "\n".join(lines)


def _format_health(analysis: dict) -> str:
    """Format health issues from analysis.toon.yaml."""
    health = analysis.get("health", {})
    issues = health.get("issues", [])
    if not issues:
        return "## Health: ✅ No issues"

    lines = [f"## Health Issues ({len(issues)})"]
    for issue in issues[:20]:  # cap at 20
        sev = issue.get("severity", "yellow")
        icon = "🔴" if sev == "red" else "🟡"
        msg = issue.get("message", "")
        lines.append(f"- {icon} {msg}")
    return "\n".join(lines)


def _format_evolution(data: Any) -> str:
    """Format evolution queue from evolution.toon.yaml."""
    if isinstance(data, str):
        # Raw TOON text — include as-is (trimmed)
        return f"## Evolution Queue\n\n```\n{data[:3000]}\n```"

    if isinstance(data, dict):
        lines = ["## Evolution Queue (Top Refactoring Actions)"]
        next_items = data.get("NEXT", data.get("next", []))
        if isinstance(next_items, list):
            for item in next_items[:10]:
                if isinstance(item, dict):
                    action = item.get("action", item.get("WHY", ""))
                    lines.append(f"- {action}")
                elif isinstance(item, str):
                    lines.append(f"- {item}")
        return "\n".join(lines)

    return ""


def _format_map_details(data: Any) -> str:
    """Format key structural details from map.toon.yaml."""
    lines = ["## Module Map (key modules)"]

    if isinstance(data, dict):
        details = data.get("D", {})
        if isinstance(details, dict):
            for module_name, info in list(details.items())[:15]:
                if isinstance(info, dict):
                    exports = info.get("e", "")
                    lines.append(f"- **{module_name}**: {exports}")
                elif isinstance(info, str):
                    lines.append(f"- **{module_name}**: {info[:100]}")

    return "\n".join(lines)


def _format_duplication(m: ProjectMetrics) -> str:
    """Format duplication summary."""
    return (
        f"## Duplication\n\n"
        f"- **Groups**: {m.dup_groups}\n"
        f"- **Recoverable lines**: {m.dup_saved_lines}"
    )


def _load_toon(directory: Path, filename: str) -> Any | None:
    """Load a .toon.yaml file."""
    path = directory / filename
    if not path.exists():
        # Try without .yaml extension
        alt = directory / filename.replace(".yaml", "")
        if alt.exists():
            return alt.read_text(encoding="utf-8")
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
