"""Status-based cleanup of completed/canceled tickets.

This is a small companion to ``ticket_pruner`` aimed at the **post-run**
maintenance flow: after ``llx plan run`` finishes, tickets typically end up
with ``status: canceled`` (no longer applicable / pre-flight stale) or
``status: done`` (LLM applied the change). They stay in ``planfile.yaml``
forever unless someone removes them. This module:

1. **Collects** ticket IDs whose ``status`` matches a target set.
2. **Prunes** them from the planfile via :mod:`ticket_pruner`.
3. **Cleans** the corresponding checkbox lines from ``TODO.md``.

Public entrypoint::

    report = clean_resolved_tickets(
        strategy_path="planfile.yaml",
        project_path=".",
        statuses={"canceled"},
        backup=True,
        update_todo=True,
        dry_run=False,
    )
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml as _yaml

from llx.planfile.ticket_pruner import prune_planfile_tickets


_DEFAULT_STATUSES: frozenset[str] = frozenset({"canceled", "cancelled"})


def _normalise_statuses(statuses: Iterable[str] | None) -> set[str]:
    if statuses is None:
        return set(_DEFAULT_STATUSES)
    out: set[str] = set()
    for value in statuses:
        text = str(value or "").strip().lower()
        if text:
            out.add(text)
            # Accept British/American spelling for cancelled/canceled.
            if text == "canceled":
                out.add("cancelled")
            elif text == "cancelled":
                out.add("canceled")
    return out or set(_DEFAULT_STATUSES)


def _entry_id(entry: Any) -> str:
    if not isinstance(entry, dict):
        return ""
    for key in ("id", "ticket_id"):
        value = str(entry.get(key) or "").strip()
        if value:
            return value
    return ""


def _entry_status(entry: Any) -> str:
    if not isinstance(entry, dict):
        return ""
    return str(entry.get("status") or "").strip().lower()


def _walk_ticket_entries(strategy: dict[str, Any]) -> list[dict[str, Any]]:
    """Yield-like collection of ticket-like entries the cleaner can examine."""
    out: list[dict[str, Any]] = []

    def _collect_list(items: Any) -> None:
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    out.append(item)

    def _collect_dict(items: Any) -> None:
        if isinstance(items, dict):
            for value in items.values():
                if isinstance(value, dict):
                    out.append(value)

    tasks = strategy.get("tasks")
    if isinstance(tasks, list):
        _collect_list(tasks)
    elif isinstance(tasks, dict):
        for items in tasks.values():
            _collect_list(items)

    backlog = strategy.get("backlog")
    if isinstance(backlog, list):
        _collect_list(backlog)
    elif isinstance(backlog, dict):
        _collect_list(backlog.get("tickets"))
        _collect_dict(backlog.get("tickets"))

    sprints = strategy.get("sprints")
    if isinstance(sprints, list):
        for sprint in sprints:
            if not isinstance(sprint, dict):
                continue
            for field in ("task_patterns", "tasks"):
                _collect_list(sprint.get(field))
            _collect_list(sprint.get("tickets"))
            _collect_dict(sprint.get("tickets"))

    return out


def collect_ticket_ids_by_status(
    strategy_path: str | Path,
    *,
    statuses: Iterable[str] | None = None,
) -> list[str]:
    """Return all ticket IDs whose ``status`` matches ``statuses``.

    Defaults to ``{"canceled", "cancelled"}`` when ``statuses`` is None.
    Tickets without an explicit ``id``/``ticket_id`` are skipped (they cannot
    be safely pruned without anchoring to a stable identifier).
    """
    path = Path(strategy_path)
    if not path.exists():
        return []

    raw = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return []

    target = _normalise_statuses(statuses)
    matched: list[str] = []
    seen: set[str] = set()
    for entry in _walk_ticket_entries(raw):
        if _entry_status(entry) not in target:
            continue
        ticket_id = _entry_id(entry)
        if not ticket_id or ticket_id in seen:
            continue
        seen.add(ticket_id)
        matched.append(ticket_id)
    return matched


# ---------------------------------------------------------------------------
# TODO.md line removal
# ---------------------------------------------------------------------------


def _build_id_pattern(ticket_ids: Iterable[str]) -> Optional[re.Pattern[str]]:
    escaped = sorted({re.escape(str(t).strip()) for t in ticket_ids if str(t).strip()})
    if not escaped:
        return None
    # Match any ticket id when it appears as a standalone token.
    return re.compile(r"(?<![A-Za-z0-9_-])(?:" + "|".join(escaped) + r")(?![A-Za-z0-9_-])")


def remove_ticket_lines_from_todo(
    todo_path: str | Path,
    ticket_ids: Iterable[str],
    *,
    backup: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Strip lines from ``TODO.md`` that mention any of the given ticket IDs.

    A line is removed when it contains a ticket ID as a standalone token
    (separated by non-identifier characters), regardless of checkbox state.
    The remaining content of TODO.md is preserved verbatim.

    Returns:
        Dict report with ``existed``, ``ids_requested``, ``removed_lines`` and
        ``backup_path``. ``dry_run=True`` returns the same shape but does not
        write anything to disk.
    """
    path = Path(todo_path)
    requested = sorted({str(t).strip() for t in ticket_ids if str(t).strip()})

    if not path.exists():
        return {
            "existed": False,
            "todo_path": str(path),
            "ids_requested": requested,
            "removed_lines": 0,
            "backup_path": None,
        }

    pattern = _build_id_pattern(requested)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if pattern is None:
        return {
            "existed": True,
            "todo_path": str(path),
            "ids_requested": requested,
            "removed_lines": 0,
            "backup_path": None,
        }

    kept: list[str] = []
    removed_count = 0
    for line in lines:
        if pattern.search(line):
            removed_count += 1
            continue
        kept.append(line)

    backup_path: Optional[Path] = None
    if removed_count and not dry_run:
        if backup:
            from time import strftime
            timestamp = strftime("%Y%m%d-%H%M%S")
            backup_path = path.with_name(f"{path.name}.bak.{timestamp}")
            backup_path.write_text(text, encoding="utf-8")
        path.write_text("".join(kept), encoding="utf-8")

    return {
        "existed": True,
        "todo_path": str(path),
        "ids_requested": requested,
        "removed_lines": removed_count,
        "backup_path": str(backup_path) if backup_path else None,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Combined cleanup entrypoint
# ---------------------------------------------------------------------------


def clean_resolved_tickets(
    strategy_path: str | Path,
    project_path: str | Path = ".",
    *,
    statuses: Iterable[str] | None = None,
    backup: bool = True,
    update_todo: bool = True,
    todo_path: Optional[str | Path] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Remove resolved tickets from planfile.yaml and (optionally) TODO.md.

    Args:
        strategy_path: planfile / strategy YAML.
        project_path: project root used to locate ``TODO.md`` when
            ``todo_path`` is not given.
        statuses: ticket statuses considered "resolved". Defaults to
            ``{"canceled", "cancelled"}``. Pass e.g. ``{"canceled", "done"}``
            to also remove already-completed work.
        backup: write timestamped ``.bak.<ts>`` files before mutating.
        update_todo: when True (default), also strip lines mentioning the
            removed ticket IDs from ``TODO.md``.
        todo_path: explicit TODO.md path; defaults to ``<project>/TODO.md``.
        dry_run: only compute counts; never modify any file.

    Returns:
        Combined report with sections ``planfile`` (from ``ticket_pruner``)
        and ``todo`` (from :func:`remove_ticket_lines_from_todo`).
    """
    project_root = Path(project_path).resolve()
    target_statuses = sorted(_normalise_statuses(statuses))

    matched_ids = collect_ticket_ids_by_status(strategy_path, statuses=target_statuses)

    planfile_report: dict[str, Any]
    if dry_run:
        planfile_report = {
            "strategy_path": str(strategy_path),
            "ids_requested": matched_ids,
            "removed": 0,
            "removed_ids": list(matched_ids),
            "backup_path": None,
            "existed": True,
            "dry_run": True,
        }
    else:
        planfile_report = prune_planfile_tickets(
            strategy_path=strategy_path,
            ticket_ids=matched_ids,
            backup=backup,
        )

    todo_report: Optional[dict[str, Any]] = None
    if update_todo and matched_ids:
        resolved_todo = (
            Path(todo_path)
            if todo_path
            else (project_root / "TODO.md")
        )
        todo_report = remove_ticket_lines_from_todo(
            todo_path=resolved_todo,
            ticket_ids=matched_ids,
            backup=backup,
            dry_run=dry_run,
        )

    return {
        "strategy_path": str(strategy_path),
        "project_path": str(project_root),
        "statuses": target_statuses,
        "matched_ids": matched_ids,
        "planfile": planfile_report,
        "todo": todo_report,
        "dry_run": dry_run,
    }
