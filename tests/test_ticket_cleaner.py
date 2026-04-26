"""Tests for the planfile ticket cleaner (status-based cleanup + TODO sync)."""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from llx.cli.app import app as llx_app
from llx.planfile.ticket_cleaner import (
    clean_resolved_tickets,
    collect_ticket_ids_by_status,
    remove_ticket_lines_from_todo,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# collect_ticket_ids_by_status
# ---------------------------------------------------------------------------


def test_collect_ids_default_canceled_only(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q1", "status": "canceled"},
                {"id": "Q2", "status": "open"},
                {"id": "Q3", "status": "done"},
                {"id": "Q4", "status": "cancelled"},  # British spelling alias
            ]
        },
    )

    ids = collect_ticket_ids_by_status(strategy)
    assert sorted(ids) == ["Q1", "Q4"]


def test_collect_ids_include_done_explicit(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q1", "status": "canceled"},
                {"id": "Q2", "status": "done"},
                {"id": "Q3", "status": "open"},
            ]
        },
    )

    ids = collect_ticket_ids_by_status(strategy, statuses=["canceled", "done"])
    assert sorted(ids) == ["Q1", "Q2"]


def test_collect_ids_walks_sprints_and_backlog(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [{"id": "T1", "status": "canceled"}],
            "backlog": [{"id": "B1", "status": "canceled"}],
            "sprints": [
                {
                    "id": 1,
                    "task_patterns": [{"id": "S1", "status": "canceled"}],
                    "tickets": {"X1": {"id": "X1", "status": "canceled"}},
                }
            ],
        },
    )

    ids = collect_ticket_ids_by_status(strategy)
    assert sorted(ids) == ["B1", "S1", "T1", "X1"]


def test_collect_ids_skips_entries_without_id(tmp_path: Path) -> None:
    """Cleaner is id-anchored — entries lacking id cannot be safely cleaned."""
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"status": "canceled", "name": "no-id"},
                {"id": "Q1", "status": "canceled"},
            ]
        },
    )

    ids = collect_ticket_ids_by_status(strategy)
    assert ids == ["Q1"]


# ---------------------------------------------------------------------------
# remove_ticket_lines_from_todo
# ---------------------------------------------------------------------------


def test_remove_todo_lines_strips_matching_only(tmp_path: Path) -> None:
    todo = tmp_path / "TODO.md"
    todo.write_text(
        "# TODO\n"
        "- [x] Q01 Done item\n"
        "- [ ] Q02 Keep me\n"
        "- [x] Q03 Drop me\n"
        "Free text mentioning Q02 should NOT be removed when bound to a checkbox?\n",
        encoding="utf-8",
    )

    report = remove_ticket_lines_from_todo(todo, ["Q01", "Q03"], backup=False)

    assert report["removed_lines"] == 2
    after = todo.read_text(encoding="utf-8")
    assert "Q01" not in after
    assert "Q03" not in after
    assert "Q02 Keep me" in after


def test_remove_todo_lines_id_must_be_standalone_token(tmp_path: Path) -> None:
    """Substring matches must NOT trigger removal."""
    todo = tmp_path / "TODO.md"
    todo.write_text(
        "- [ ] Q1 short\n"
        "- [ ] Q11 longer must be kept\n"
        "- [ ] Q1Z foreign suffix must be kept\n",
        encoding="utf-8",
    )

    report = remove_ticket_lines_from_todo(todo, ["Q1"], backup=False)

    assert report["removed_lines"] == 1
    after = todo.read_text(encoding="utf-8")
    assert "Q1 short" not in after
    assert "Q11 longer" in after
    assert "Q1Z foreign" in after


def test_remove_todo_lines_dry_run_does_not_write(tmp_path: Path) -> None:
    todo = tmp_path / "TODO.md"
    original = "- [x] Q01 Done\n- [ ] Q02 Keep\n"
    todo.write_text(original, encoding="utf-8")

    report = remove_ticket_lines_from_todo(todo, ["Q01"], backup=False, dry_run=True)

    assert report["removed_lines"] == 1
    assert report["dry_run"] is True
    assert todo.read_text(encoding="utf-8") == original


def test_remove_todo_lines_creates_backup(tmp_path: Path) -> None:
    todo = tmp_path / "TODO.md"
    todo.write_text("- [x] Q01 Done\n- [ ] Q02 Keep\n", encoding="utf-8")

    report = remove_ticket_lines_from_todo(todo, ["Q01"], backup=True)

    assert report["removed_lines"] == 1
    assert report["backup_path"] is not None
    assert Path(report["backup_path"]).exists()


def test_remove_todo_lines_handles_missing_file(tmp_path: Path) -> None:
    report = remove_ticket_lines_from_todo(tmp_path / "nope.md", ["Q01"])
    assert report["existed"] is False
    assert report["removed_lines"] == 0


# ---------------------------------------------------------------------------
# clean_resolved_tickets — combined flow
# ---------------------------------------------------------------------------


def test_clean_resolved_removes_from_planfile_and_todo(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q1", "status": "canceled"},
                {"id": "Q2", "status": "open"},
                {"id": "Q3", "status": "canceled"},
            ]
        },
    )
    todo = tmp_path / "TODO.md"
    todo.write_text(
        "- [x] Q1 cancelled item\n- [ ] Q2 still active\n- [x] Q3 dropped\n",
        encoding="utf-8",
    )

    report = clean_resolved_tickets(
        strategy_path=strategy,
        project_path=tmp_path,
        backup=False,
    )

    assert sorted(report["matched_ids"]) == ["Q1", "Q3"]
    assert report["planfile"]["removed"] == 2
    assert report["todo"]["removed_lines"] == 2

    after_strategy = _read(strategy)
    assert [t["id"] for t in after_strategy["tasks"]] == ["Q2"]
    assert "Q1" not in todo.read_text(encoding="utf-8")
    assert "Q2 still active" in todo.read_text(encoding="utf-8")
    assert "Q3" not in todo.read_text(encoding="utf-8")


def test_clean_resolved_dry_run_writes_nothing(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, {"tasks": [{"id": "Q1", "status": "canceled"}]})
    todo = tmp_path / "TODO.md"
    todo.write_text("- [x] Q1 done\n", encoding="utf-8")

    report = clean_resolved_tickets(
        strategy_path=strategy,
        project_path=tmp_path,
        dry_run=True,
        backup=False,
    )

    assert report["matched_ids"] == ["Q1"]
    # Nothing was modified
    assert _read(strategy)["tasks"][0]["id"] == "Q1"
    assert "Q1" in todo.read_text(encoding="utf-8")


def test_clean_resolved_no_todo_when_disabled(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, {"tasks": [{"id": "Q1", "status": "canceled"}]})
    todo = tmp_path / "TODO.md"
    todo.write_text("- [x] Q1 done\n", encoding="utf-8")

    report = clean_resolved_tickets(
        strategy_path=strategy,
        project_path=tmp_path,
        update_todo=False,
        backup=False,
    )

    assert report["todo"] is None
    # planfile updated, TODO untouched
    assert _read(strategy).get("tasks") == []
    assert "Q1" in todo.read_text(encoding="utf-8")


def test_clean_resolved_includes_done_when_requested(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q1", "status": "canceled"},
                {"id": "Q2", "status": "done"},
                {"id": "Q3", "status": "open"},
            ]
        },
    )

    report = clean_resolved_tickets(
        strategy_path=strategy,
        project_path=tmp_path,
        statuses=["canceled", "done"],
        update_todo=False,
        backup=False,
    )

    assert sorted(report["matched_ids"]) == ["Q1", "Q2"]
    assert [t["id"] for t in _read(strategy)["tasks"]] == ["Q3"]


# ---------------------------------------------------------------------------
# CLI: `llx plan clean`
# ---------------------------------------------------------------------------


def test_cli_plan_clean_default_canceled_with_todo(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q1", "status": "canceled"},
                {"id": "Q2", "status": "open"},
            ]
        },
    )
    todo = tmp_path / "TODO.md"
    todo.write_text("- [x] Q1 done\n- [ ] Q2 active\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        llx_app,
        [
            "plan", "clean",
            str(strategy),
            "--project", str(tmp_path),
            "--no-backup",
            "--format", "yaml",
        ],
    )

    assert result.exit_code == 0, result.stdout
    parsed = yaml.safe_load(result.stdout)
    assert parsed["matched_ids"] == ["Q1"]
    assert parsed["planfile"]["removed"] == 1
    assert parsed["todo"]["removed_lines"] == 1
    assert [t["id"] for t in _read(strategy)["tasks"]] == ["Q2"]


def test_cli_plan_clean_dry_run(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, {"tasks": [{"id": "Q1", "status": "canceled"}]})
    todo = tmp_path / "TODO.md"
    todo.write_text("- [x] Q1 done\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        llx_app,
        [
            "plan", "clean",
            str(strategy),
            "--project", str(tmp_path),
            "--dry-run",
            "--no-backup",
            "--format", "yaml",
        ],
    )

    assert result.exit_code == 0
    parsed = yaml.safe_load(result.stdout)
    assert parsed["dry_run"] is True
    # Files untouched
    assert _read(strategy)["tasks"][0]["id"] == "Q1"
    assert "Q1" in todo.read_text(encoding="utf-8")


def test_cli_plan_clean_include_done(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q1", "status": "canceled"},
                {"id": "Q2", "status": "done"},
                {"id": "Q3", "status": "open"},
            ]
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        llx_app,
        [
            "plan", "clean",
            str(strategy),
            "--project", str(tmp_path),
            "--include-done",
            "--no-todo-sync",
            "--no-backup",
            "--format", "yaml",
        ],
    )

    assert result.exit_code == 0
    parsed = yaml.safe_load(result.stdout)
    assert sorted(parsed["matched_ids"]) == ["Q1", "Q2"]
    assert [t["id"] for t in _read(strategy)["tasks"]] == ["Q3"]


# ---------------------------------------------------------------------------
# Workflow: kind: plan-clean
# ---------------------------------------------------------------------------


def test_workflow_plan_clean_handler_end_to_end(tmp_path: Path) -> None:
    from llx.workflows import Workflow, WorkflowStep, run_workflow

    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q1", "status": "canceled"},
                {"id": "Q2", "status": "open"},
            ]
        },
    )
    todo = tmp_path / "TODO.md"
    todo.write_text("- [x] Q1 done\n- [ ] Q2 active\n", encoding="utf-8")

    workflow = Workflow(
        name="cleanup",
        steps=[
            WorkflowStep(
                name="clean",
                kind="plan-clean",
                params={
                    "strategy": str(strategy),
                    "backup": False,
                },
            )
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path)
    step = report.steps[0]
    assert step.status == "success"
    assert step.data["planfile_removed"] == 1
    assert step.data["todo_lines_removed"] == 1
    assert [t["id"] for t in _read(strategy)["tasks"]] == ["Q2"]
