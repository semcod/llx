"""Collect project metrics from code2llm, redup, vallm, and filesystem.

Metrics drive model tier selection — no abstract scores, only concrete numbers.

Lesson from preLLM: _prepare_context() had CC=21 because it mixed file loading,
parsing, and aggregation. Here each step is a focused function (CC ≤ 5).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProjectMetrics:
    """Aggregated project metrics that drive model selection.

    Every field maps to a real, measurable property of the codebase.
    """

    # Structural (from code2llm)
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_modules: int = 0

    # Complexity (from code2llm analysis.toon)
    avg_cc: float = 0.0
    max_cc: int = 0
    critical_count: int = 0
    god_modules: int = 0

    # Coupling (from code2llm map.toon)
    max_fan_out: int = 0
    max_fan_in: int = 0
    dependency_cycles: int = 0
    hotspot_count: int = 0

    # Duplication (from redup)
    dup_groups: int = 0
    dup_saved_lines: int = 0

    # Validation (from vallm)
    vallm_pass_rate: float = 1.0
    vallm_issues: int = 0

    # Task context
    task_scope: str = "single_file"
    estimated_context_tokens: int = 0
    languages: list[str] = field(default_factory=list)

    @property
    def complexity_score(self) -> float:
        """Weighted complexity indicator (0-100)."""
        s = 0.0
        s += min(self.avg_cc * 5, 30)
        s += min(self.max_cc * 0.5, 20)
        s += min(self.critical_count * 2, 20)
        s += min(self.god_modules * 5, 15)
        s += min(self.dependency_cycles * 5, 15)
        return min(s, 100)

    @property
    def scale_score(self) -> float:
        """Project scale indicator (0-100)."""
        s = 0.0
        s += min(self.total_files * 0.3, 25)
        s += min(self.total_lines / 500, 25)
        s += min(self.total_functions / 50, 25)
        s += min(self.max_fan_out * 1.5, 25)
        return min(s, 100)

    @property
    def coupling_score(self) -> float:
        """Inter-module coupling indicator (0-100)."""
        s = 0.0
        s += min(self.max_fan_out * 2, 30)
        s += min(self.max_fan_in * 2, 30)
        s += min(self.dependency_cycles * 10, 20)
        s += min(self.hotspot_count * 3, 20)
        return min(s, 100)


def analyze_project(
    project_path: str | Path,
    *,
    use_code2llm: bool = True,
    use_redup: bool = True,
    use_vallm: bool = True,
    toon_dir: str | None = None,
) -> ProjectMetrics:
    """Collect all available metrics for a project."""
    root = Path(project_path).resolve()
    metrics = ProjectMetrics()

    _collect_filesystem_metrics(root, metrics)

    search_dir = Path(toon_dir) if toon_dir else root
    if use_code2llm:
        _collect_code2llm_metrics(search_dir, metrics)
    if use_redup:
        _collect_redup_metrics(search_dir, metrics)
    if use_vallm:
        _collect_vallm_metrics(search_dir, metrics)

    metrics.estimated_context_tokens = _estimate_context_tokens(metrics)
    metrics.task_scope = _classify_scope(metrics)
    return metrics


# ---------------------------------------------------------------------------
# Filesystem fallback
# ---------------------------------------------------------------------------

_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".lua", ".sh", ".bash",
}

_SKIP_DIRS = {"__pycache__", "node_modules", ".git", "venv", ".venv", ".tox", "dist", "build"}


def _collect_filesystem_metrics(root: Path, m: ProjectMetrics) -> None:
    """Count files and lines from the filesystem."""
    langs: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in _SKIP_DIRS]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext in _CODE_EXTENSIONS:
                fpath = Path(dirpath) / fname
                m.total_files += 1
                langs.add(ext.lstrip("."))
                try:
                    m.total_lines += sum(1 for _ in open(fpath, "rb"))
                except (OSError, PermissionError):
                    pass
    m.languages = sorted(langs)


# ---------------------------------------------------------------------------
# code2llm — analysis.toon, evolution.toon, map.toon
# ---------------------------------------------------------------------------

def _collect_code2llm_metrics(search_dir: Path, m: ProjectMetrics) -> None:
    """Load metrics from code2llm analysis files (YAML or plain-text TOON)."""
    # analysis.toon.yaml — always valid YAML
    analysis = _load_file(search_dir, [
        "analysis.toon.yaml", "analysis_toon.yaml", "analysis.yaml",
    ])
    if isinstance(analysis, dict):
        _apply_analysis_yaml(analysis, m)

    # evolution.toon.yaml — may be YAML or plain-text
    evolution = _load_file(search_dir, [
        "evolution.toon.yaml", "evolution_toon.yaml", "evolution.yaml",
    ])
    if isinstance(evolution, dict):
        _apply_evolution_yaml(evolution, m)
    elif isinstance(evolution, str):
        _apply_evolution_text(evolution, m)

    # map.toon.yaml — often plain-text TOON with YAML-breaking syntax
    map_data = _load_file(search_dir, [
        "map.toon.yaml", "map_toon.yaml", "map.yaml",
    ])
    if isinstance(map_data, dict):
        _apply_map_yaml(map_data, m)
    elif isinstance(map_data, str):
        _apply_map_text(map_data, m)


def _apply_analysis_yaml(data: dict, m: ProjectMetrics) -> None:
    """Extract metrics from analysis.toon.yaml (valid YAML format)."""
    header = data.get("header", {})
    m.total_files = max(m.total_files, header.get("files", 0))
    m.total_lines = max(m.total_lines, header.get("lines", 0))
    m.total_functions = max(m.total_functions, header.get("functions", 0))
    m.avg_cc = float(header.get("avg_cc", m.avg_cc))
    m.critical_count = header.get("critical_count", m.critical_count)
    m.dependency_cycles = header.get("cycles", m.dependency_cycles)

    # Extract max CC from health issues
    for issue in data.get("health", {}).get("issues", []):
        cc_val = _extract_cc_value(issue.get("message", ""))
        if cc_val is not None and cc_val > m.max_cc:
            m.max_cc = cc_val


def _apply_evolution_yaml(data: dict, m: ProjectMetrics) -> None:
    """Extract metrics from evolution.toon.yaml (valid YAML format).

    Handles both the code2llm format (METRICS-TARGET dict) and
    the preLLM format (metrics_target with current/target sub-dicts).
    """
    # preLLM / new format: metrics_target.god_modules.current
    mt = data.get("metrics_target", data.get("METRICS-TARGET", {}))
    if isinstance(mt, dict):
        god = mt.get("god_modules", mt.get("god-modules", {}))
        if isinstance(god, dict):
            m.god_modules = int(god.get("current", 0))
        elif isinstance(god, (int, float)):
            m.god_modules = int(god)
        elif isinstance(god, str) and "→" in god:
            try:
                m.god_modules = int(god.split("→")[0].strip())
            except ValueError:
                pass

        # Extract max CC from metrics_target
        max_cc = mt.get("max_cc", mt.get("max-cc", {}))
        if isinstance(max_cc, dict):
            val = int(max_cc.get("current", 0))
            m.max_cc = max(m.max_cc, val)

    # Stats section (preLLM format)
    stats = data.get("stats", {})
    if isinstance(stats, dict):
        m.total_functions = max(m.total_functions, stats.get("total_funcs", 0))
        m.total_files = max(m.total_files, stats.get("total_files", 0))
        if stats.get("avg_cc"):
            m.avg_cc = max(m.avg_cc, float(stats["avg_cc"]))
        if stats.get("max_cc"):
            m.max_cc = max(m.max_cc, int(stats["max_cc"]))
        m.critical_count = max(m.critical_count, stats.get("critical_count", 0))

    # Refactoring actions — count god-module splits
    for action in data.get("refactoring", {}).get("actions", []):
        if isinstance(action, dict) and action.get("action") == "SPLIT":
            m.god_modules = max(m.god_modules, 1)  # at least one god module exists

    # Fan-out from refactoring actions
    for action in data.get("refactoring", {}).get("actions", []):
        if isinstance(action, dict):
            fan = action.get("fan_out", 0)
            m.max_fan_out = max(m.max_fan_out, fan)


def _apply_evolution_text(text: str, m: ProjectMetrics) -> None:
    """Parse plain-text evolution.toon format."""
    for line in text.split("\n"):
        if "god-modules:" in line or "god_modules:" in line:
            match = re.search(r"(\d+)\s*→", line)
            if match:
                m.god_modules = int(match.group(1))
        if "max-cc:" in line or "max_cc:" in line:
            match = re.search(r"(\d+)\s*→", line)
            if match:
                m.max_cc = max(m.max_cc, int(match.group(1)))
        if "fan=" in line:
            match = re.search(r"fan=(\d+)", line)
            if match:
                m.max_fan_out = max(m.max_fan_out, int(match.group(1)))


def _apply_map_yaml(data: dict, m: ProjectMetrics) -> None:
    """Extract structural metrics from map.toon.yaml (YAML dict format)."""
    modules = data.get("M", [])
    if isinstance(modules, list):
        m.total_modules = max(m.total_modules, len(modules))

    hotspots = data.get("hotspots", [])
    if isinstance(hotspots, list):
        m.hotspot_count = max(m.hotspot_count, len(hotspots))


def _apply_map_text(text: str, m: ProjectMetrics) -> None:
    """Parse plain-text map.toon header comments for metrics.

    Header format:
    # code2llm | 108f 20922L | python:105 | 2026-03-25
    # stats: 814 func | 0 cls | 108 mod | CC̄=4.6 | critical:12 | cycles:0
    # alerts[5]: CC _extract=65; fan-out _extract=45; ...
    # hotspots[5]: _extract fan=45; ...
    """
    for line in text.split("\n")[:20]:
        line = line.strip()
        if not line.startswith("#"):
            continue

        # Parse stats line
        if "func" in line and "mod" in line:
            for part in line.split("|"):
                part = part.strip()
                match = re.search(r"(\d+)\s*func", part)
                if match:
                    m.total_functions = max(m.total_functions, int(match.group(1)))
                match = re.search(r"(\d+)\s*mod", part)
                if match:
                    m.total_modules = max(m.total_modules, int(match.group(1)))
                match = re.search(r"(\d+)\s*cls", part)
                if match:
                    m.total_classes = max(m.total_classes, int(match.group(1)))
                match = re.search(r"CC̄=([0-9.]+)", part)
                if match:
                    m.avg_cc = max(m.avg_cc, float(match.group(1)))
                match = re.search(r"critical:(\d+)", part)
                if match:
                    m.critical_count = max(m.critical_count, int(match.group(1)))
                match = re.search(r"cycles:(\d+)", part)
                if match:
                    m.dependency_cycles = max(m.dependency_cycles, int(match.group(1)))

        # Parse alerts for fan-out
        if "alerts" in line:
            for match in re.finditer(r"fan-out\s+\S+=(\d+)", line):
                m.max_fan_out = max(m.max_fan_out, int(match.group(1)))
            for match in re.finditer(r"CC\s+\S+=(\d+)", line):
                m.max_cc = max(m.max_cc, int(match.group(1)))

        # Parse hotspots
        if "hotspots" in line:
            match = re.search(r"hotspots\[(\d+)\]", line)
            if match:
                m.hotspot_count = max(m.hotspot_count, int(match.group(1)))
            for match in re.finditer(r"fan=(\d+)", line):
                m.max_fan_out = max(m.max_fan_out, int(match.group(1)))

    # Count M[] modules
    m_count = text.count("\n  ") if "M[" in text else 0
    # Better: count lines matching module pattern (indent + filename,number)
    module_lines = re.findall(r"^\s{2}\S+\.py,\d+", text, re.MULTILINE)
    if module_lines:
        m.total_modules = max(m.total_modules, len(module_lines))


# ---------------------------------------------------------------------------
# redup / vallm
# ---------------------------------------------------------------------------

def _collect_redup_metrics(search_dir: Path, m: ProjectMetrics) -> None:
    """Load from redup duplication scan."""
    data = _load_file(search_dir, ["duplication.json", "duplication.yaml"])
    if isinstance(data, dict):
        summary = data.get("summary", {})
        m.dup_groups = summary.get("total_groups", 0)
        m.dup_saved_lines = summary.get("total_saved_lines", 0)


def _collect_vallm_metrics(search_dir: Path, m: ProjectMetrics) -> None:
    """Load from vallm validation reports."""
    data = _load_file(search_dir, ["validation.json", "validation.yaml"])
    if isinstance(data, dict):
        summary = data.get("summary", {})
        total = summary.get("total_files", 0)
        passed = summary.get("passed", 0)
        if total > 0:
            m.vallm_pass_rate = passed / total
            m.vallm_issues = total - passed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_file(directory: Path, candidates: list[str]) -> dict | str | None:
    """Try to load first matching file. Returns dict (YAML/JSON) or str (plain text)."""
    for name in candidates:
        fpath = directory / name
        if not fpath.exists():
            continue
        try:
            text = fpath.read_text(encoding="utf-8")
            if name.endswith(".json"):
                return json.loads(text)
            result = yaml.safe_load(text)
            if isinstance(result, dict):
                return result
            # YAML returned a string (single-document plain text)
            return text
        except (yaml.YAMLError, json.JSONDecodeError):
            # YAML/JSON parse failed — return as raw text
            try:
                return fpath.read_text(encoding="utf-8")
            except OSError:
                pass
        except OSError:
            pass
    return None


def _extract_cc_value(msg: str) -> int | None:
    """Extract CC value from health message like 'func CC=25 (limit:15)'."""
    match = re.search(r"CC=(\d+)", msg)
    return int(match.group(1)) if match else None


def _estimate_context_tokens(m: ProjectMetrics) -> int:
    """Rough estimate: ~4 chars/token, analysis ~10% of source."""
    source_chars = m.total_lines * 40
    return int(source_chars * 1.1 / 4)


def _classify_scope(m: ProjectMetrics) -> str:
    """Classify task scope based on project structure."""
    if m.total_files <= 1:
        return "single_file"
    if m.total_files <= 5 and m.max_fan_out <= 3:
        return "multi_file"
    if m.max_fan_out > 10 or m.dependency_cycles > 0:
        return "project_wide"
    return "cross_module"
