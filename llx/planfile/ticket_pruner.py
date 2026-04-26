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

In addition to plain ticket IDs the pruner also accepts **synthetic
entry-ref strings** (``tasks[N]``, ``backlog[N]``,
``sprints[X].task_patterns[N]``, ``sprints[X].tasks[N]``,
``sprints[X].tickets[KEY]``). These are emitted by
``planfile.validate_planfile_tickets`` for entries that lack a real ``id``
field, so passing them straight through removes the targeted entry by its
structural position. Index-based removals are applied in reverse order to
keep earlier indices stable.

When ``backup=True`` (the default), a timestamped ``planfile.yaml.bak.<ts>``
copy is created before the file is rewritten. Pass ``backup=False`` to skip.
"""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml as _yaml


# Match synthetic entry refs emitted by planfile validator when an entry has
# no real id. Examples:
#   tasks[5]
#   backlog[2]
#   sprints[0].task_patterns[42]
#   sprints[1].tasks[3]
#   sprints[0].tickets[FOO]
_ENTRY_REF_RE = re.compile(
    r"^(?:sprints\[(?P<sprint>\d+)\]\.)?"
    r"(?P<section>task_patterns|tasks|tickets|backlog)"
    r"\[(?P<key>[^\]]+)\]$"
)


def _parse_entry_ref(ref: str) -> Optional[dict[str, Any]]:
    """Parse an ``entry_ref`` string into a structural locator.

    Returns ``None`` when ``ref`` is not a recognised entry-ref pattern, in
    which case the caller should fall back to id-based matching.
    """
    text = (ref or "").strip()
    match = _ENTRY_REF_RE.match(text)
    if not match:
        return None

    sprint_raw = match.group("sprint")
    section = match.group("section")
    key = match.group("key")

    # Top-level sections (no sprint prefix) only allow ``tasks`` or ``backlog``.
    if sprint_raw is None and section not in {"tasks", "backlog"}:
        return None
    # Nested sprint sections only allow the per-sprint task buckets.
    if sprint_raw is not None and section == "backlog":
        return None

    parsed: dict[str, Any] = {
        "sprint_idx": int(sprint_raw) if sprint_raw is not None else None,
        "section": section,
        "raw_key": key,
    }
    try:
        parsed["index"] = int(key)
    except ValueError:
        parsed["index"] = None
        parsed["dict_key"] = key
    return parsed


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


def _resolve_container(
    strategy: dict[str, Any], sprint_idx: Optional[int], section: str
) -> Any:
    """Return the list / dict referenced by ``(sprint_idx, section)``.

    Returns None when the path does not exist in the planfile.
    """
    if sprint_idx is None:
        if section == "tasks":
            tasks = strategy.get("tasks")
            return tasks if isinstance(tasks, list) else None
        if section == "backlog":
            backlog = strategy.get("backlog")
            if isinstance(backlog, list):
                return backlog
            if isinstance(backlog, dict):
                tickets = backlog.get("tickets")
                if isinstance(tickets, (list, dict)):
                    return tickets
        return None

    sprints = strategy.get("sprints")
    if not isinstance(sprints, list) or sprint_idx < 0 or sprint_idx >= len(sprints):
        return None
    sprint = sprints[sprint_idx]
    if not isinstance(sprint, dict):
        return None
    return sprint.get(section)


def _format_ref(sprint_idx: Optional[int], section: str, key: Any) -> str:
    if sprint_idx is None:
        return f"{section}[{key}]"
    return f"sprints[{sprint_idx}].{section}[{key}]"


def _apply_entry_ref_removals(
    strategy: dict[str, Any],
    refs: list[dict[str, Any]],
    removed_log: list[str],
) -> None:
    """Remove entries identified by parsed entry-ref locators.

    Index-based removals are batched per ``(sprint_idx, section)`` and applied
    in **descending order** so earlier indices in the same list stay valid.
    """
    grouped: dict[tuple[Optional[int], str], list[dict[str, Any]]] = {}
    for ref in refs:
        key = (ref["sprint_idx"], ref["section"])
        grouped.setdefault(key, []).append(ref)

    for (sprint_idx, section), items in grouped.items():
        container = _resolve_container(strategy, sprint_idx, section)
        if container is None:
            continue

        if isinstance(container, list):
            indices = sorted(
                {it["index"] for it in items if it.get("index") is not None},
                reverse=True,
            )
            for idx in indices:
                if 0 <= idx < len(container):
                    removed_log.append(_format_ref(sprint_idx, section, idx))
                    container.pop(idx)
            continue

        if isinstance(container, dict):
            for it in items:
                if it.get("index") is not None:
                    dkey: Any = str(it["index"])
                else:
                    dkey = it.get("dict_key") or it.get("raw_key") or ""
                if dkey in container:
                    removed_log.append(_format_ref(sprint_idx, section, dkey))
                    container.pop(dkey)


def prune_planfile_tickets(
    strategy_path: str | Path,
    ticket_ids: Iterable[str] | None,
    *,
    backup: bool = True,
) -> dict[str, Any]:
    """Physically remove the given ticket IDs from a planfile YAML file.

    Args:
        strategy_path: Path to the planfile / strategy YAML.
        ticket_ids: Ticket IDs to remove. Each item is matched in two ways:
            (1) as a plain id against ``id`` / ``ticket_id`` fields and
            (2) as a synthetic entry-ref pattern (``tasks[N]``,
            ``sprints[X].task_patterns[N]``, ``sprints[X].tickets[KEY]`` etc.)
            against the planfile's structural position. Empty / falsy → no-op.
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

    # Split requested identifiers into plain IDs vs. structural entry refs.
    plain_ids: set[str] = set()
    parsed_refs: list[dict[str, Any]] = []
    for ident in requested:
        parsed = _parse_entry_ref(ident)
        if parsed is not None:
            parsed_refs.append(parsed)
        else:
            plain_ids.add(ident)

    removed_log: list[str] = []
    # Apply ref-based deletions first so list indices map correctly to the
    # original planfile contents (id-based passes filter lists afterwards).
    _apply_entry_ref_removals(raw, parsed_refs, removed_log)
    _prune_tasks_section(raw, plain_ids, removed_log)
    _prune_backlog(raw, plain_ids, removed_log)
    _prune_sprints(raw, plain_ids, removed_log)

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
