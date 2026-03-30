"""Issue loading and fix-prompt building utilities for llx.

Upstreamed from pyqual — provides helpers for loading issues from JSON
error files and TODO.md markdown checklists (prefact-generated), and
building concise prompts for aider-based fix/refactor workflows.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_PROMPT_LIMIT = 10

_TODO_CHECKLIST_RE = re.compile(r"^- \[(?P<state>[ xX])\]\s+(?P<body>.+)$")
_TODO_DETAIL_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+)\s+-\s+(?P<message>.+)$")


# ── Issue loading ────────────────────────────────────────────────


def load_issue_source(issues_path: Path) -> dict[str, Any] | list[dict[str, Any]] | list[Any]:
    """Load issues from a JSON error file or a markdown checklist.

    Supports:
    - JSON files with a top-level list or a dict containing an
      ``errors``, ``messages``, ``findings``, or ``results`` key.
    - Markdown files (``*.md``, ``*.markdown``, ``TODO.md``) with
      prefact-style ``- [ ] ...`` checklists.

    Returns an empty list when the file does not exist or cannot be parsed.
    """
    if not issues_path.exists():
        return []

    if issues_path.suffix.lower() in {".md", ".markdown"} or issues_path.name.lower() == "todo.md":
        return load_todo_markdown(issues_path)

    try:
        data = json.loads(issues_path.read_text())
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("errors", "messages", "findings", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return data
    return []


def load_todo_markdown(issues_path: Path) -> list[dict[str, Any]]:
    """Load unchecked TODO checklist items from prefact-generated markdown.

    Each unchecked item (``- [ ] ...``) is parsed into a dict with at
    least a ``message`` key.  If the body matches
    ``<file>:<line> - <message>`` the dict also contains ``file`` and
    ``line`` keys.
    """
    try:
        lines = issues_path.read_text().splitlines()
    except OSError:
        return []

    issues: list[dict[str, Any]] = []
    for raw_line in lines:
        match = _TODO_CHECKLIST_RE.match(raw_line.strip())
        if not match or match.group("state").lower() != " ":
            continue

        body = match.group("body").strip()
        detail = _TODO_DETAIL_RE.match(body)
        if detail:
            issues.append(
                {
                    "file": detail.group("file").strip(),
                    "line": int(detail.group("line")),
                    "message": detail.group("message").strip(),
                    "severity": "todo",
                }
            )
            continue

        issues.append({"message": body, "severity": "todo"})

    return issues


def resolve_issue_source(
    workdir: Path,
    issues_path: Path,
    fallback_name: str = "TODO.md",
) -> tuple[Path, dict[str, Any] | list[dict[str, Any]] | list[Any]]:
    """Resolve issues, falling back to a markdown file when the primary source is empty."""
    resolved = issues_path if issues_path.is_absolute() else (workdir / issues_path).resolve()
    issues = load_issue_source(resolved)

    if not issues:
        todo_path = (workdir / fallback_name).resolve()
        if todo_path.exists():
            todo_issues = load_todo_markdown(todo_path)
            if todo_issues:
                return todo_path, todo_issues

    return resolved, issues


# ── Issue formatting ─────────────────────────────────────────────


def issue_text(issue: Any) -> str:
    """Render one issue entry as a compact string."""
    if isinstance(issue, str):
        return issue
    if isinstance(issue, dict):
        parts: list[str] = []
        location = issue.get("file") or issue.get("path")
        line = issue.get("line") or issue.get("lineno")
        if location:
            loc = str(location)
            if line:
                loc = f"{loc}:{line}"
            parts.append(loc)
        severity = issue.get("severity") or issue.get("level")
        if severity:
            parts.append(str(severity))
        code = issue.get("code") or issue.get("symbol")
        if code:
            parts.append(str(code))
        message = issue.get("message") or issue.get("msg") or issue.get("description")
        if message:
            parts.append(str(message))
        if parts:
            return " - ".join(parts)
    return str(issue)


# ── Prompt building ──────────────────────────────────────────────


def task_prompt_label(task: str) -> str:
    """Map llx task hints to prompt wording."""
    labels = {
        "explain": "explaining code",
        "quick_fix": "fixing code",
        "refactor": "refactoring code",
        "review": "reviewing code",
    }
    return labels.get(task, "fixing code")


def build_fix_prompt(
    project_path: Path,
    issues: dict[str, Any] | list[dict[str, Any]] | list[Any],
    analysis: dict[str, Any] | None = None,
    prompt_limit: int = DEFAULT_PROMPT_LIMIT,
    action_label: str = "fixing code",
) -> str:
    """Build a concise prompt for llx/aider from gate failures."""
    selected_model = None
    tier = None
    if analysis:
        selection = analysis.get("selection")
        if isinstance(selection, dict):
            selected_model = selection.get("model_id")
            tier = selection.get("tier")

    issue_lines: list[str] = []
    if isinstance(issues, dict):
        issue_lines.append(issue_text(issues))
    else:
        for issue in list(issues)[:prompt_limit]:
            issue_lines.append(issue_text(issue))

    issue_block = "\n".join(f"- {line}" for line in issue_lines) if issue_lines else "- No structured issues were found."
    analysis_block = json.dumps(analysis, indent=2, ensure_ascii=False) if analysis else "{}"

    return (
        f"You are {action_label} in {project_path}.\n"
        "Use the smallest safe changes that make the quality gates pass.\n"
        "Preserve existing behavior unless a change is clearly justified.\n"
        f"Selected model: {selected_model or 'auto'}\n"
        f"Selection tier: {tier or 'unknown'}\n\n"
        f"Issue summary:\n{issue_block}\n\n"
        f"Analysis payload:\n{analysis_block}\n\n"
        "Return code edits only."
    )
