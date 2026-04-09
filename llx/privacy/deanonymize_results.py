from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DeanonymizationResult:
    """Result of deanonymization operation."""

    text: str
    restorations: list[tuple[str, str]] = field(default_factory=list)  # (token, original)
    unknown_tokens: list[str] = field(default_factory=list)
    confidence: float = 1.0  # Ratio of found tokens to total tokens


@dataclass
class ProjectDeanonymizationResult:
    """Result of project-level deanonymization."""

    files: dict[str, str] = field(default_factory=dict)
    restorations: dict[str, int] = field(default_factory=dict)
    unknowns: dict[str, list[str]] = field(default_factory=dict)
    overall_confidence: float = 0.0
