"""Tests for the planfile ticket pruner."""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from llx.cli.app import app as llx_app
from llx.planfile.ticket_pruner import prune_planfile_tickets


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# Pure pruner
# ---------------------------------------------------------------------------


def test_prune_removes_top_level_tasks_and_creates_backup(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {"id": "Q01", "name": "keep me"},
                {"id": "Q02", "name": "drop me"},
                {"id": "Q03", "name": "drop me too"},
            ]
        },
    )

    report = prune_planfile_tickets(strategy, ticket_ids={"Q02", "Q03"})

    assert report["removed"] == 2
    assert report["removed_ids"] == ["Q02", "Q03"]
    assert report["backup_path"] is not None
    assert Path(report["backup_path"]).exists()
    assert _read(strategy) == {"tasks": [{"id": "Q01", "name": "keep me"}]}


def test_prune_with_no_backup_does_not_create_bak(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, {"tasks": [{"id": "Q01"}, {"id": "Q02"}]})

    report = prune_planfile_tickets(strategy, ticket_ids={"Q02"}, backup=False)

    assert report["removed"] == 1
    assert report["backup_path"] is None
    assert not list(tmp_path.glob("*.bak.*"))


def test_prune_returns_noop_when_ticket_ids_empty(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, {"tasks": [{"id": "Q01"}]})
    report = prune_planfile_tickets(strategy, ticket_ids=None)
    assert report["removed"] == 0
    assert report["backup_path"] is None
    # File untouched -> no backup
    assert _read(strategy) == {"tasks": [{"id": "Q01"}]}


def test_prune_handles_missing_planfile(tmp_path: Path) -> None:
    report = prune_planfile_tickets(tmp_path / "nope.yaml", ticket_ids=["Q01"])
    assert report["existed"] is False
    assert report["removed"] == 0


def test_prune_walks_sprints_and_backlog(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [{"id": "T1"}, {"id": "T2"}],
            "backlog": [{"id": "B1"}, {"id": "B2"}],
            "sprints": [
                {
                    "id": 1,
                    "task_patterns": [{"id": "S1"}, {"id": "S2"}],
                    "tasks": [{"id": "S3"}],
                    "tickets": {
                        "S4": {"id": "S4", "name": "via dict key"},
                        "S5": {"id": "S5", "name": "keep"},
                    },
                }
            ],
        },
    )

    report = prune_planfile_tickets(strategy, ticket_ids=["T2", "B1", "S2", "S4"])

    assert report["removed_ids"] == ["B1", "S2", "S4", "T2"]
    after = _read(strategy)
    assert [t["id"] for t in after["tasks"]] == ["T1"]
    assert [t["id"] for t in after["backlog"]] == ["B2"]
    sprint = after["sprints"][0]
    assert [t["id"] for t in sprint["task_patterns"]] == ["S1"]
    assert [t["id"] for t in sprint["tasks"]] == ["S3"]
    assert list(sprint["tickets"].keys()) == ["S5"]


def test_prune_handles_dict_tasks_section(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": {
                "fix": [{"id": "F1"}, {"id": "F2"}],
                "refactor": [{"id": "R1"}],
            }
        },
    )

    report = prune_planfile_tickets(strategy, ticket_ids=["F1", "R1"])

    assert report["removed"] == 2
    after = _read(strategy)
    assert [t["id"] for t in after["tasks"]["fix"]] == ["F2"]
    assert after["tasks"]["refactor"] == []


def test_prune_handles_backlog_dict_with_tickets(tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "backlog": {
                "tickets": {
                    "B1": {"id": "B1"},
                    "B2": {"id": "B2"},
                }
            }
        },
    )

    report = prune_planfile_tickets(strategy, ticket_ids=["B1"])

    assert report["removed"] == 1
    after = _read(strategy)
    assert list(after["backlog"]["tickets"].keys()) == ["B2"]


# ---------------------------------------------------------------------------
# CLI: `llx plan validate --prune-stale --prune-unknown`
# ---------------------------------------------------------------------------


def _planfile_for_cli(tmp_path: Path) -> Path:
    strategy = tmp_path / "planfile.yaml"
    _write(
        strategy,
        {
            "tasks": [
                {
                    "id": "F1",
                    "name": "keep (current)",
                    "rule_id": "unused-imports",
                    "files": ["src/a.py"],
                },
                {
                    "id": "F2",
                    "name": "stale",
                    "rule_id": "wildcard-imports",
                    "files": ["src/a.py"],
                },
                {
                    "id": "U1",
                    "name": "wrongly described",
                    # no rule_id, no file/line -> 'unknown'
                },
            ]
        },
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("import os\n", encoding="utf-8")
    return strategy


def test_plan_validate_cli_prune_stale_only(monkeypatch, tmp_path: Path) -> None:
    strategy = _planfile_for_cli(tmp_path)

    from llx.integrations.prefact import PrefactScanReport

    fake_scan = PrefactScanReport(
        issues=[{"rule_id": "unused-imports", "file": "src/a.py", "line": 1}],
        files_scanned=1,
        backend="engine",
        raw_total=1,
    )
    monkeypatch.setattr(
        "llx.planfile.ticket_freshness.scan_with_prefact",
        lambda **_kw: fake_scan,
    )

    runner = CliRunner()
    result = runner.invoke(
        llx_app,
        [
            "plan",
            "validate",
            str(strategy),
            "--project",
            str(tmp_path),
            "--prune-stale",
            "--no-cancel-stale",
            "--no-backup",
            "--format",
            "yaml",
        ],
    )

    assert result.exit_code == 0, result.stdout
    parsed = yaml.safe_load(result.stdout)
    assert parsed["prune"]["removed_ids"] == ["F2"]
    after = _read(strategy)
    assert [t["id"] for t in after["tasks"]] == ["F1", "U1"]


def test_plan_validate_cli_prune_unknown_too(monkeypatch, tmp_path: Path) -> None:
    strategy = _planfile_for_cli(tmp_path)

    from llx.integrations.prefact import PrefactScanReport

    fake_scan = PrefactScanReport(
        issues=[{"rule_id": "unused-imports", "file": "src/a.py", "line": 1}],
        files_scanned=1,
        backend="engine",
        raw_total=1,
    )
    monkeypatch.setattr(
        "llx.planfile.ticket_freshness.scan_with_prefact",
        lambda **_kw: fake_scan,
    )

    runner = CliRunner()
    result = runner.invoke(
        llx_app,
        [
            "plan",
            "validate",
            str(strategy),
            "--project",
            str(tmp_path),
            "--prune-stale",
            "--prune-unknown",
            "--no-cancel-stale",
            "--no-backup",
            "--format",
            "yaml",
        ],
    )

    assert result.exit_code == 0, result.stdout
    parsed = yaml.safe_load(result.stdout)
    assert sorted(parsed["prune"]["removed_ids"]) == ["F2", "U1"]
    after = _read(strategy)
    assert [t["id"] for t in after["tasks"]] == ["F1"]


# ---------------------------------------------------------------------------
# Workflow handler: kind: plan-prune-stale
# ---------------------------------------------------------------------------


def test_workflow_plan_prune_stale_uses_previous_validate_output(monkeypatch, tmp_path: Path) -> None:
    from llx.workflows import (
        Workflow,
        WorkflowStep,
        run_workflow,
    )

    strategy = tmp_path / "planfile.yaml"
    _write(strategy, {"tasks": [{"id": "S1"}, {"id": "S2"}, {"id": "K1"}]})

    fake_validate_report = {
        "current": 1,
        "stale": 2,
        "unknown": 0,
        "stale_ticket_ids": ["S1", "S2"],
        "review_needed_ticket_ids": [],
        "scan": {"available": True, "backend": "engine"},
    }
    monkeypatch.setattr(
        "llx.planfile.ticket_freshness.validate_tickets_with_prefact",
        lambda **_kw: dict(fake_validate_report),
    )

    workflow = Workflow(
        name="prune-after-validate",
        steps=[
            WorkflowStep(
                name="validate",
                kind="plan-validate",
                params={"strategy": str(strategy), "cancel_stale": False},
            ),
            WorkflowStep(
                name="prune",
                kind="plan-prune-stale",
                params={"strategy": str(strategy), "backup": False},
            ),
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path)
    statuses = {s.name: s.status for s in report.steps}
    assert statuses == {"validate": "success", "prune": "success"}

    prune_step = report.steps[1]
    assert prune_step.data["removed"] == 2
    after = _read(strategy)
    assert [t["id"] for t in after["tasks"]] == ["K1"]


def test_workflow_plan_prune_stale_noop_when_nothing_to_remove(tmp_path: Path) -> None:
    from llx.workflows import Workflow, WorkflowStep, run_workflow

    strategy = tmp_path / "planfile.yaml"
    _write(strategy, {"tasks": [{"id": "K1"}]})

    workflow = Workflow(
        name="prune",
        steps=[
            WorkflowStep(
                name="prune",
                kind="plan-prune-stale",
                params={"strategy": str(strategy), "backup": False},
            )
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path)
    step = report.steps[0]
    assert step.status == "success"
    assert step.summary == "nothing to prune"
    assert _read(strategy) == {"tasks": [{"id": "K1"}]}
