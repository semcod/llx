"""Select the optimal LLM model tier based on project metrics.

The selection algorithm uses real code metrics — not abstract quality scores.
Each metric maps to a concrete threshold that determines whether the project
needs a premium, balanced, cheap, or free/local model.

Principle: larger + more coupled + more complex → stronger model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from llx.analysis.collector import ProjectMetrics
from llx.config import LlxConfig, ModelConfig, TierThresholds


class ModelTier(str, Enum):
    """LLM model tiers ranked by capability and cost."""

    PREMIUM = "premium"      # Opus-class: large coupled projects, deep refactoring
    BALANCED = "balanced"    # Sonnet-class: medium projects, standard tasks
    CHEAP = "cheap"          # Haiku-class: small projects, simple questions
    FREE = "free"            # Gemini/free-tier: trivial tasks
    LOCAL = "local"          # Ollama/vLLM: offline, privacy-sensitive
    OPENROUTER = "openrouter"  # Fallback pool


@dataclass
class SelectionResult:
    """Result of model selection with explanation."""

    tier: ModelTier
    model: ModelConfig
    reasons: list[str]
    scores: dict[str, float]  # metric_name → score used
    alternative_tier: ModelTier | None = None  # next best option

    @property
    def model_id(self) -> str:
        return self.model.model_id

    def explain(self) -> str:
        """Human-readable explanation of why this model was selected."""
        lines = [f"Selected: {self.tier.value} → {self.model.model_id}"]
        for reason in self.reasons:
            lines.append(f"  • {reason}")
        if self.alternative_tier:
            lines.append(f"  Alternative: {self.alternative_tier.value}")
        return "\n".join(lines)


def select_model(
    metrics: ProjectMetrics,
    config: LlxConfig | None = None,
    *,
    prefer_local: bool = False,
    max_tier: ModelTier | None = None,
    force_tier: ModelTier | None = None,
    task_hint: str | None = None,
) -> SelectionResult:
    """Select the best model tier based on project metrics.

    Args:
        metrics: Project metrics from analyze_project().
        config: Configuration with model definitions and thresholds.
        prefer_local: Force local model selection (privacy/offline).
        max_tier: Upper bound on model tier (cost control).
        task_hint: Optional hint about the task type:
            "refactor" → favors stronger models
            "explain" → balanced is usually enough
            "quick_fix" → cheap is fine
            "review" → balanced+

    Returns:
        SelectionResult with chosen model, reasons, and scores.
    """
    if config is None:
        config = LlxConfig()

    thresholds = config.thresholds
    reasons: list[str] = []
    scores = {
        "complexity": metrics.complexity_score,
        "scale": metrics.scale_score,
        "coupling": metrics.coupling_score,
    }

    # Force local if requested
    if prefer_local:
        return SelectionResult(
            tier=ModelTier.LOCAL,
            model=config.models.get("local", config.models["cheap"]),
            reasons=["Local model preferred (offline/privacy mode)"],
            scores=scores,
        )

    # Force specific tier if requested
    if force_tier:
        tier = force_tier
        reasons.append(f"Forced to use {tier.value} tier")
    else:
        # Determine tier from metrics
        tier = _compute_tier(metrics, thresholds, reasons, task_hint)

    # Apply max_tier ceiling
    tier_order = [ModelTier.FREE, ModelTier.LOCAL, ModelTier.CHEAP, ModelTier.BALANCED, ModelTier.PREMIUM]
    if max_tier and tier_order.index(tier) > tier_order.index(max_tier):
        reasons.append(f"Downgraded from {tier.value} to {max_tier.value} (cost limit)")
        tier = max_tier

    # Resolve model config
    model = config.models.get(tier.value)
    if model is None:
        model = config.models.get("balanced", list(config.models.values())[0])
        reasons.append(f"Tier '{tier.value}' not configured, falling back to balanced")
        tier = ModelTier.BALANCED

    # Compute alternative
    alt = _compute_alternative(tier, tier_order)

    return SelectionResult(
        tier=tier,
        model=model,
        reasons=reasons,
        scores=scores,
        alternative_tier=alt,
    )


def _count_premium_signals(m: ProjectMetrics, t: TierThresholds, reasons: list[str]) -> int:
    """Count how many premium thresholds are exceeded."""
    premium_signals = 0

    if m.total_files >= t.files_premium:
        premium_signals += 1
        reasons.append(f"Large project: {m.total_files} files (≥{t.files_premium})")

    if m.total_lines >= t.lines_premium:
        premium_signals += 1
        reasons.append(f"Large codebase: {m.total_lines:,} lines (≥{t.lines_premium:,})")

    if m.avg_cc >= t.cc_premium:
        premium_signals += 1
        reasons.append(f"High complexity: CC̄={m.avg_cc:.1f} (≥{t.cc_premium})")

    if m.max_fan_out >= t.coupling_premium:
        premium_signals += 1
        reasons.append(f"High coupling: fan-out={m.max_fan_out} (≥{t.coupling_premium})")

    if m.max_cc >= t.max_cc_premium:
        premium_signals += 1
        reasons.append(f"Extreme function complexity: max CC={m.max_cc} (≥{t.max_cc_premium})")

    if m.dup_groups >= t.dup_groups_premium:
        premium_signals += 1
        reasons.append(f"Heavy duplication: {m.dup_groups} groups (≥{t.dup_groups_premium})")

    if m.dependency_cycles > 0:
        premium_signals += 1
        reasons.append(f"Dependency cycles detected: {m.dependency_cycles}")

    return premium_signals


def _count_balanced_signals(m: ProjectMetrics, t: TierThresholds, reasons: list[str]) -> int:
    """Count how many balanced thresholds are exceeded."""
    balanced_signals = 0

    if m.total_files >= t.files_balanced:
        balanced_signals += 1
        reasons.append(f"Medium project: {m.total_files} files (≥{t.files_balanced})")

    if m.total_lines >= t.lines_balanced:
        balanced_signals += 1
        reasons.append(f"Medium codebase: {m.total_lines:,} lines (≥{t.lines_balanced:,})")

    if m.avg_cc >= t.cc_balanced:
        balanced_signals += 1
        reasons.append(f"Moderate complexity: CC̄={m.avg_cc:.1f} (≥{t.cc_balanced})")

    if m.max_fan_out >= t.coupling_balanced:
        balanced_signals += 1
        reasons.append(f"Moderate coupling: fan-out={m.max_fan_out} (≥{t.coupling_balanced})")

    if m.dup_groups >= t.dup_groups_balanced:
        balanced_signals += 1
        reasons.append(f"Some duplication: {m.dup_groups} groups (≥{t.dup_groups_balanced})")

    return balanced_signals


def _apply_task_adjustment(signals: int, task_hint: str | None, reasons: list[str]) -> int:
    """Adjust signal count based on task hint."""
    if task_hint == "refactor":
        signals += 1
        reasons.append("Task: refactoring (favors stronger model)")
    elif task_hint == "quick_fix":
        signals = max(0, signals - 2)
        reasons.append("Task: quick fix (lighter model acceptable)")
    return signals


def _compute_tier(
    m: ProjectMetrics,
    t: TierThresholds,
    reasons: list[str],
    task_hint: str | None,
) -> ModelTier:
    """Core tier selection logic based on metric thresholds."""
    # Count premium signals and apply task adjustment
    premium = _count_premium_signals(m, t, reasons)
    premium = _apply_task_adjustment(premium, task_hint, reasons)
    
    if premium >= 3:
        return ModelTier.PREMIUM

    # Count balanced signals
    balanced = _count_balanced_signals(m, t, reasons)
    if premium >= 1 or balanced >= 2:
        return ModelTier.BALANCED

    # Cheap indicators
    if m.total_files >= t.files_cheap or m.total_lines >= t.lines_cheap:
        reasons.append(f"Small project: {m.total_files} files, {m.total_lines:,} lines")
        return ModelTier.CHEAP

    # Minimal project → free
    reasons.append(f"Minimal project: {m.total_files} files, {m.total_lines:,} lines")
    return ModelTier.FREE


def _compute_alternative(tier: ModelTier, order: list[ModelTier]) -> ModelTier | None:
    """Suggest the next cheaper tier as an alternative."""
    idx = order.index(tier)
    if idx > 0:
        return order[idx - 1]
    return None


# ---------------------------------------------------------------------------
# Context-window aware selection
# ---------------------------------------------------------------------------

def check_context_fit(metrics: ProjectMetrics, model: ModelConfig) -> bool:
    """Check if the project context fits within the model's context window."""
    return metrics.estimated_context_tokens <= model.max_context


def select_with_context_check(
    metrics: ProjectMetrics,
    config: LlxConfig | None = None,
    **kwargs,
) -> SelectionResult:
    """Select model and verify context window fit.

    If the selected model's context is too small, upgrades to the next tier.
    """
    result = select_model(metrics, config, **kwargs)

    if not check_context_fit(metrics, result.model):
        config = config or LlxConfig()
        # Try upgrading
        tier_order = [ModelTier.FREE, ModelTier.LOCAL, ModelTier.CHEAP, ModelTier.BALANCED, ModelTier.PREMIUM]
        current_idx = tier_order.index(result.tier)
        for next_idx in range(current_idx + 1, len(tier_order)):
            next_tier = tier_order[next_idx]
            next_model = config.models.get(next_tier.value)
            if next_model and check_context_fit(metrics, next_model):
                result.reasons.append(
                    f"Upgraded to {next_tier.value}: "
                    f"~{metrics.estimated_context_tokens:,} tokens exceeds "
                    f"{result.model.model_id} limit ({result.model.max_context:,})"
                )
                result.tier = next_tier
                result.model = next_model
                break

    return result
