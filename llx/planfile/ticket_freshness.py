"""Code-aware ticket freshness checks.

Composes the ``prefact`` source-level scanner with
``planfile.validate_planfile_tickets`` to answer the question:

    "Does the issue described by this ticket still exist in the source?"

The orchestration intentionally lives outside of ``planfile`` because it
combines an external tool (``prefact``) with the planfile validation API.
The planfile project keeps the pure ticket-validation contract; llx wires
the scanner-driven workflow.

Public entrypoint::

    report = validate_tickets_with_prefact(
        strategy_path="planfile.yaml",
        project_path=".",
    )

The returned report mirrors :func:`planfile.validate_planfile_tickets` and
adds a ``scan`` section describing the prefact run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

from llx.integrations.prefact import (
    PrefactError,
    PrefactScanReport,
    scan_with_prefact,
)


def _empty_scan_summary(reason: str) -> dict[str, Any]:
    return {
        "available": False,
        "backend": None,
        "issues": 0,
        "files_scanned": 0,
        "config_path": None,
        "reason": reason,
    }


def _scan_summary_from_report(report: PrefactScanReport) -> dict[str, Any]:
    return {
        "available": True,
        "backend": report.backend,
        "issues": len(report.issues),
        "raw_issues": report.raw_total,
        "files_scanned": report.files_scanned,
        "config_path": str(report.config_path) if report.config_path else None,
        "reason": "prefact_scan_complete",
    }


def validate_tickets_with_prefact(
    strategy_path: str | Path = "planfile.yaml",
    project_path: str | Path = ".",
    *,
    ticket_ids: Optional[Iterable[str]] = None,
    prefact_yaml: Optional[str | Path] = None,
    prefact_bin: Optional[str] = None,
    require_scan: bool = False,
) -> dict[str, Any]:
    """Validate planfile tickets against an actual prefact source-code scan.

    Args:
        strategy_path: planfile YAML path (relative to ``project_path`` or absolute).
        project_path: project root for path normalisation and the prefact scan.
        ticket_ids: optional iterable of ticket IDs to limit the report to.
        prefact_yaml: optional explicit ``prefact.yaml`` path. When omitted,
            a sibling ``prefact.yaml`` next to the planfile is used (if any).
        prefact_bin: optional explicit prefact executable name/path used by
            the subprocess fallback.
        require_scan: when True, raise :class:`~llx.integrations.prefact.PrefactError`
            if the scanner cannot run; otherwise return a report flagged as
            scan-unavailable so callers can degrade gracefully.

    Returns:
        Dict mirroring ``planfile.validate_planfile_tickets`` plus a ``scan``
        block describing the underlying prefact run.
    """
    from planfile import validate_planfile_tickets

    project_root = Path(project_path).resolve()
    strategy_file = Path(strategy_path)
    if not strategy_file.is_absolute():
        strategy_file = (project_root / strategy_file).resolve()

    issue_records: Optional[list[dict[str, Any]]] = None
    scan_summary: dict[str, Any]

    try:
        scan_report = scan_with_prefact(
            project_path=project_root,
            prefact_yaml=prefact_yaml,
            prefact_bin=prefact_bin,
        )
    except PrefactError as exc:
        if require_scan:
            raise
        scan_summary = _empty_scan_summary(str(exc))
    else:
        issue_records = scan_report.issues
        scan_summary = _scan_summary_from_report(scan_report)

    report = validate_planfile_tickets(
        strategy_path=strategy_file,
        project_path=project_root,
        issue_records=issue_records,
        ticket_ids=ticket_ids,
    )

    report["scan"] = scan_summary
    return report
