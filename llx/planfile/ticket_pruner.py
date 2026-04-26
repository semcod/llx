"""Hard-delete tickets from a planfile YAML.

This complements ``llx.planfile.ticket_freshness`` (which only classifies
tickets as ``current`` / ``stale`` / ``unknown``) by physically removing
matching entries from the planfile so they no longer waste reviewer / LLM
attention.

Public entrypoint::

    report = prune_planfile_tickets(
        strategy_path="planfile.yaml",
        ticket_ids={"Q01", "Q07"},
        backup=True,
    )

The pruner walks the same locations as
``planfile.validate_planfile_tickets`` so its behaviour is consistent:

- top-level ``tasks: []`` (list) and ``tasks: {<group>: [...]}`` (dict-of-lists)
- ``backlog: []`` (list) and ``backlog.tickets: {id: {...}}`` (dict)
- ``sprints[*].task_patterns: []``
- ``sprints[*].tasks: []``
- ``sprints[*].tickets: {id: {...}}``

When ``backup=True`` (the default), a timestamped ``planfile.yaml.bak.<ts>``
copy is created before the file is rewritten. Pass ``backup=False`` to skip.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml as _yaml


def _coerce_id_set(ticket_ids: Iterable[Any] | None) -> set[str]:
    if not ticket_ids:
        return set()
    out: set[str] = set()
    for value in ticket_ids:
        text = str(value or "").strip()
        if text:
            out.add(text)
    return out


def _matches(entry: Any, ids: set[str]) -> bool:
    if not isinstance(entry, dict):
        return False
    for key in ("id", "ticket_id"):
        candidate = str(entry.get(key) or "").strip()
        if candidate and candidate in ids:
            return True
    return False


def _filter_list(items: Any, ids: set[str], removed: list[str]) -> Any:
    if not isinstance(items, list):
        return items
    kept: list[Any] = []
    for entry in items:
        if _matches(entry, ids):
            removed.append(str(entry.get("id") or entry.get("ticket_id")))
            continue
        kept.append(entry)
    return kept


def _filter_dict_of_tickets(items: Any, ids: set[str], removed: list[str]) -> Any:
    if not isinstance(items, dict):
        return items
    kept: dict[str, Any] = {}
    for key, entry in items.items():
        if str(key).strip() in ids:
            removed.append(str(key))
            continue
        if _matches(entry, ids):
            removed.append(str(entry.get("id") or entry.get("ticket_id") or key))
            continue
        kept[key] = entry
    return kept


def _prune_tasks_section(strategy: dict[str, Any], ids: set[str], removed: list[str]) -> None:
    tasks = strategy.get("tasks")
    if isinstance(tasks, list):
        strategy["tasks"] = _filter_list(tasks, ids, removed)
    elif isinstance(tasks, dict):
        strategy["tasks"] = {
            group: _filter_list(items, ids, removed) if isinstance(items, list) else items
            for group, items in tasks.items()
        }


def _prune_backlog(strategy: dict[str, Any], ids: set[str], removed: list[str]) -> None:
    backlog = strategy.get("backlog")
    if isinstance(backlog, list):
        strategy["backlog"] = _filter_list(backlog, ids, removed)
    elif isinstance(backlog, dict):
        tickets = backlog.get("tickets")
        if isinstance(tickets, dict):
            backlog["tickets"] = _filter_dict_of_tickets(tickets, ids, removed)
        elif isinstance(tickets, list):
            backlog["tickets"] = _filter_list(tickets, ids, removed)


def _prune_sprints(strategy: dict[str, Any], ids: set[str], removed: list[str]) -> None:
    sprints = strategy.get("sprints")
    if not isinstance(sprints, list):
        return
    for sprint in sprints:
        if not isinstance(sprint, dict):
            continue
        for field in ("task_patterns", "tasks"):
            if isinstance(sprint.get(field), list):
                sprint[field] = _filter_list(sprint[field], ids, removed)
        if isinstance(sprint.get("tickets"), dict):
            sprint["tickets"] = _filter_dict_of_tickets(sprint["tickets"], ids, removed)
        elif isinstance(sprint.get("tickets"), list):
            sprint["tickets"] = _filter_list(sprint["tickets"], ids, removed)


def _make_backup(path: Path) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak.{timestamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def prune_planfile_tickets(
    strategy_path: str | Path,
    ticket_ids: Iterable[str] | None,
    *,
    backup: bool = True,
) -> dict[str, Any]:
    """Physically remove the given ticket IDs from a planfile YAML file.

    Args:
        strategy_path: Path to the planfile / strategy YAML.
        ticket_ids: Ticket IDs to remove. Empty / falsy → no-op (still returns
            a structured report with ``removed: 0``).
        backup: When True (default) copy the file to ``<path>.bak.<ts>``
            before rewriting. Skipped if the planfile does not exist or no
            tickets were removed.

    Returns:
        Report dict with keys ``strategy_path``, ``ids_requested``,
        ``removed`` (count), ``removed_ids`` (sorted list), ``backup_path``
        (str or None), and ``existed`` (bool).
    """
    path = Path(strategy_path)
    requested = _coerce_id_set(ticket_ids)

    if not path.exists():
        return {
            "strategy_path": str(path),
            "existed": False,
            "ids_requested": sorted(requested),
            "removed": 0,
            "removed_ids": [],
            "backup_path": None,
        }

    if not requested:
        return {
            "strategy_path": str(path),
            "existed": True,
            "ids_requested": [],
            "removed": 0,
            "removed_ids": [],
            "backup_path": None,
        }

    raw = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return {
            "strategy_path": str(path),
            "existed": True,
            "ids_requested": sorted(requested),
            "removed": 0,
            "removed_ids": [],
            "backup_path": None,
        }

    removed_log: list[str] = []
    _prune_tasks_section(raw, requested, removed_log)
    _prune_backlog(raw, requested, removed_log)
    _prune_sprints(raw, requested, removed_log)

    backup_path: Optional[Path] = None
    if removed_log:
        if backup:
            backup_path = _make_backup(path)
        path.write_text(
            _yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    # Deduplicate while preserving sort order for stable output.
    unique_removed = sorted(set(removed_log))
    return {
        "strategy_path": str(path),
        "existed": True,
        "ids_requested": sorted(requested),
        "removed": len(unique_removed),
        "removed_ids": unique_removed,
        "backup_path": str(backup_path) if backup_path else None,
    }
