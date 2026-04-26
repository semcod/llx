"""prefact integration: run a code-level scan and return issue records.

This adapter exposes a single high-level API used by ticket-freshness checks
in llx (and indirectly by ``planfile.validate_planfile_tickets``):

    issue_records = scan_with_prefact(project_path)

The returned records use the schema accepted by
``planfile.validate_planfile_tickets`` (``rule_id``, ``file``, ``line``).

Two execution modes are tried, in order:

1. **In-process import** of ``prefact.engine.RefactoringEngine``.
   Fastest, used when prefact is importable in the current interpreter.
2. **Subprocess fallback** invoking the ``prefact-scan`` (or ``prefact``)
   binary. Used when the in-process import fails (e.g. version mismatch).

Both paths normalise file paths to be project-relative. A ``PrefactError`` is
raised only when prefact is genuinely unavailable; callers may catch it to
degrade gracefully.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


class PrefactError(RuntimeError):
    """Raised when no working prefact backend is available."""


@dataclass
class PrefactScanReport:
    """Structured outcome of a prefact-based code scan."""

    issues: list[dict[str, Any]]
    files_scanned: int
    backend: str  # "engine" or "subprocess"
    config_path: Optional[Path] = None
    raw_total: int = 0  # total before normalisation/filtering


def _normalise_relative(file_path: Any, project_root: Path) -> Optional[str]:
    if file_path is None:
        return None

    raw = str(file_path).strip()
    if not raw:
        return None

    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        return str(candidate.relative_to(project_root.resolve()))
    except ValueError:
        return str(candidate)


def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _record_from_issue(issue: Any, project_root: Path) -> Optional[dict[str, Any]]:
    """Convert a prefact ``Issue`` (or dict) into a planfile-compatible record."""
    rule_id = getattr(issue, "rule_id", None)
    file_path = getattr(issue, "file", None)
    line = getattr(issue, "line", None)
    col = getattr(issue, "col", None)
    severity = getattr(issue, "severity", None)
    message = getattr(issue, "message", None)

    if rule_id is None and isinstance(issue, dict):
        rule_id = issue.get("rule_id") or issue.get("rule")
        file_path = file_path or issue.get("file") or issue.get("path")
        line = line if line is not None else issue.get("line")
        col = col if col is not None else issue.get("col")
        severity = severity if severity is not None else issue.get("severity")
        message = message if message is not None else issue.get("message")

    rule_str = str(rule_id or "").strip()
    if not rule_str:
        return None

    rel_path = _normalise_relative(file_path, project_root)
    if not rel_path:
        return None

    severity_str = (
        getattr(severity, "value", None)
        if hasattr(severity, "value")
        else (str(severity) if severity is not None else None)
    )

    return {
        "rule_id": rule_str,
        "file": rel_path,
        "line": _coerce_int(line),
        "col": _coerce_int(col),
        "severity": severity_str,
        "message": str(message) if message is not None else None,
    }


def _scan_with_engine(
    project_path: Path,
    prefact_yaml: Optional[Path],
) -> Optional[PrefactScanReport]:
    try:
        from prefact.config import Config  # type: ignore[import-not-found]
        from prefact.engine import RefactoringEngine  # type: ignore[import-not-found]
    except Exception:
        return None

    try:
        if prefact_yaml and prefact_yaml.exists():
            config = Config.from_yaml(prefact_yaml)
        else:
            default = project_path / "prefact.yaml"
            config = Config.from_yaml(default) if default.exists() else Config()

        config.project_root = project_path
        config.dry_run = True
        result = RefactoringEngine(config).scan_only()
    except TypeError as exc:
        # Config schema mismatch (e.g., unknown key in yaml) – fallback to subprocess
        return None
    except Exception as exc:  # pragma: no cover - defensive, prefer fallback
        raise PrefactError(f"prefact engine failed: {exc}") from exc

    issues_raw = list(getattr(result, "issues_found", []) or [])
    records: list[dict[str, Any]] = []
    for issue in issues_raw:
        record = _record_from_issue(issue, project_path)
        if record is not None:
            records.append(record)

    return PrefactScanReport(
        issues=records,
        files_scanned=len({record["file"] for record in records}),
        backend="engine",
        config_path=prefact_yaml if prefact_yaml and prefact_yaml.exists() else None,
        raw_total=len(issues_raw),
    )


def _resolve_prefact_binary(explicit: Optional[str]) -> Optional[str]:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    candidates.extend(["prefact-scan", "prefact"])
    for name in candidates:
        path = shutil.which(name)
        if path:
            return path
    return None


def _normalise_subprocess_payload(
    raw_text: str,
    project_root: Path,
) -> tuple[list[dict[str, Any]], int]:
    try:
        data = json.loads(raw_text)
    except Exception:
        return [], 0

    iterable: Iterable[Any]
    if isinstance(data, list):
        iterable = data
    elif isinstance(data, dict):
        iterable = (
            data.get("issues")
            or data.get("issues_found")
            or data.get("results")
            or []
        )
    else:
        iterable = []

    raw_items = list(iterable)
    records: list[dict[str, Any]] = []
    for item in raw_items:
        record = _record_from_issue(item, project_root)
        if record is not None:
            records.append(record)
    return records, len(raw_items)


def _scan_with_subprocess(
    project_path: Path,
    prefact_yaml: Optional[Path],
    prefact_bin: Optional[str],
) -> Optional[PrefactScanReport]:
    binary = _resolve_prefact_binary(prefact_bin)
    if not binary:
        return None

    cmd = [binary, "scan", "--format", "json", "--path", str(project_path)]
    if prefact_yaml and prefact_yaml.exists():
        cmd.extend(["--config", str(prefact_yaml)])

    try:
        proc = subprocess.run(  # noqa: S603 - controlled binary above
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(project_path),
        )
    except FileNotFoundError:
        return None

    if proc.returncode not in (0, 1):
        # Non-recoverable failure; signal to caller via empty backend.
        raise PrefactError(
            f"prefact subprocess failed (exit={proc.returncode}): "
            f"{(proc.stderr or proc.stdout).strip()[:400]}"
        )

    records, raw_total = _normalise_subprocess_payload(proc.stdout, project_path)
    return PrefactScanReport(
        issues=records,
        files_scanned=len({record["file"] for record in records}),
        backend="subprocess",
        config_path=prefact_yaml if prefact_yaml and prefact_yaml.exists() else None,
        raw_total=raw_total,
    )


def scan_with_prefact(
    project_path: str | Path = ".",
    *,
    prefact_yaml: Optional[str | Path] = None,
    prefact_bin: Optional[str] = None,
) -> PrefactScanReport:
    """Run a prefact code scan and return planfile-compatible issue records.

    Tries in-process ``RefactoringEngine`` first, then falls back to invoking
    ``prefact-scan``/``prefact`` as a subprocess. Raises ``PrefactError`` only
    when no backend is available or both backends fail outright.
    """
    project_root = Path(project_path).resolve()
    config_path = Path(prefact_yaml) if prefact_yaml else None

    try:
        engine_report = _scan_with_engine(project_root, config_path)
    except PrefactError:
        engine_report = None

    if engine_report is not None:
        return engine_report

    subprocess_report = _scan_with_subprocess(project_root, config_path, prefact_bin)
    if subprocess_report is not None:
        return subprocess_report

    raise PrefactError(
        "prefact is not available: install the 'prefact' package or provide "
        "a 'prefact-scan' executable on PATH."
    )
