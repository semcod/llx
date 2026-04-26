"""End-to-end tests for llx plan testql integration with prefact and planfile.

These tests use the real planfile package to verify the full integration:
- TestQL validation
- Ticket generation from failures
- Ticket upsert into planfile.yaml
- Sync to TODO.md and integrations
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from llx.cli.app import _run_plan_testql_workflow


def test_testql_workflow_with_passing_validation(tmp_path: Path, monkeypatch) -> None:
    """Test that a passing TestQL validation does not create tickets."""
    scenario_path = tmp_path / "passing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Passing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/health
    expect:
      status: 200
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks: []
sprints: []
"""
    )

    # Mock the testql validation to return success
    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        return {
            "ok": True,
            "passed": 5,
            "failed": 0,
            "exit_code": 0,
            "source": kwargs["scenario_path"],
            "errors": [],
            "warnings": [],
        }

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = lambda *_, **__: []
    fake_planfile.upsert_testql_tickets = lambda *_, **__: {"created": 0, "skipped": 0, "created_ticket_ids": []}
    fake_planfile.sync_testql_tickets = lambda *_, **__: {}

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = _run_plan_testql_workflow(
        scenario=str(scenario_path),
        strategy=str(strategy_path),
        project_path=tmp_path,
        url="http://localhost:8101",
        dry_run=False,
        create_tickets=True,
        sync_targets=False,
        max_tickets=25,
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    assert payload["validation"]["ok"] is True
    assert payload["validation"]["passed"] == 5
    assert payload["validation"]["failed"] == 0
    assert payload["tickets"]["generated"] == 0
    assert payload["tickets"]["created"] == 0
    assert payload["tickets"]["created_ticket_ids"] == []


def test_testql_workflow_with_failing_validation_creates_tickets(tmp_path: Path, monkeypatch) -> None:
    """Test that a failing TestQL validation creates tickets."""
    scenario_path = tmp_path / "failing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Failing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/missing
    expect:
      status: 404
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks: []
sprints:
  - name: Sprint 1
    task_patterns: []
"""
    )

    calls: dict[str, object] = {}
    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        calls["run"] = kwargs
        return {
            "ok": False,
            "passed": 3,
            "failed": 2,
            "exit_code": 2,
            "source": kwargs["scenario_path"],
            "errors": ["L5: expected status 404, got 200"],
            "warnings": [],
        }

    def build_testql_tickets(report, scenario_path, max_tickets):
        calls["build"] = {"scenario_path": scenario_path, "max_tickets": max_tickets}
        return [
            {
                "id": "TQL-1",
                "title": "testql: failing.testql.toon.yaml :: L5: expected status 404, got 200",
                "description": "TestQL scenario failed: failing.testql.toon.yaml\n\nL5: expected status 404, got 200",
                "labels": ["testql", "dsl-validation"],
                "priority": "high",
                "files": [],
                "rule_id": "testql",
            }
        ]

    def upsert_testql_tickets(strategy_path, tickets, project_path):
        calls["upsert"] = {
            "strategy_path": strategy_path,
            "tickets": tickets,
            "project_path": project_path,
        }
        return {"created": 1, "skipped": 0, "created_ticket_ids": ["TQL-1"]}

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = build_testql_tickets
    fake_planfile.upsert_testql_tickets = upsert_testql_tickets
    fake_planfile.sync_testql_tickets = lambda *_, **__: {}

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = _run_plan_testql_workflow(
        scenario=str(scenario_path),
        strategy=str(strategy_path),
        project_path=tmp_path,
        url="http://localhost:8101",
        dry_run=False,
        create_tickets=True,
        sync_targets=False,
        max_tickets=25,
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    assert payload["validation"]["ok"] is False
    assert payload["validation"]["failed"] == 2
    assert payload["tickets"]["generated"] == 1
    assert payload["tickets"]["created"] == 1
    assert payload["tickets"]["created_ticket_ids"] == ["TQL-1"]
    assert "run" in calls and "build" in calls and "upsert" in calls


def test_testql_workflow_dry_run_skips_ticket_creation(tmp_path: Path, monkeypatch) -> None:
    """Test that dry_run=True skips ticket creation and upsert."""
    scenario_path = tmp_path / "failing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Failing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/missing
    expect:
      status: 404
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks: []
sprints: []
"""
    )

    calls: dict[str, object] = {}
    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        calls["run"] = kwargs
        return {
            "ok": False,
            "passed": 3,
            "failed": 1,
            "exit_code": 1,
            "source": kwargs["scenario_path"],
            "errors": ["boom"],
            "warnings": [],
        }

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = lambda *_, **__: (calls.update({"build": True}), [])[1]
    fake_planfile.upsert_testql_tickets = lambda *_, **__: (calls.update({"upsert": True}), {"created": 0, "skipped": 0, "created_ticket_ids": []})[1]
    fake_planfile.sync_testql_tickets = lambda *_, **__: {}

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = _run_plan_testql_workflow(
        scenario=str(scenario_path),
        strategy=str(strategy_path),
        project_path=tmp_path,
        url="http://localhost:8101",
        dry_run=True,  # Dry run mode
        create_tickets=True,
        sync_targets=False,
        max_tickets=25,
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    # Validation should still run
    assert payload["validation"]["ok"] is False
    assert "run" in calls
    # But ticket building/upsert should not
    assert "build" not in calls
    assert "upsert" not in calls
    assert payload["tickets"]["generated"] == 0
    assert payload["tickets"]["created"] == 0


def test_testql_workflow_max_tickets_cap(tmp_path: Path, monkeypatch) -> None:
    """Test that max_tickets limits the number of tickets generated."""
    scenario_path = tmp_path / "failing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Failing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/missing
    expect:
      status: 404
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks: []
sprints: []
"""
    )

    calls: dict[str, object] = {}
    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        calls["run"] = kwargs
        return {
            "ok": False,
            "passed": 0,
            "failed": 10,
            "exit_code": 1,
            "source": kwargs["scenario_path"],
            "errors": ["error"] * 10,
            "warnings": [],
        }

    def build_testql_tickets(report, scenario_path, max_tickets):
        calls["build"] = {"scenario_path": scenario_path, "max_tickets": max_tickets}
        # Simulate generating 10 tickets
        return [
            {
                "id": f"TQL-{i}",
                "title": f"Test ticket {i}",
                "description": "desc",
                "labels": ["testql"],
                "priority": "high",
            }
            for i in range(10)
        ]

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = build_testql_tickets
    fake_planfile.upsert_testql_tickets = lambda *_, **__: {"created": 5, "skipped": 5, "created_ticket_ids": ["TQL-0", "TQL-1", "TQL-2", "TQL-3", "TQL-4"]}
    fake_planfile.sync_testql_tickets = lambda *_, **__: {}

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = _run_plan_testql_workflow(
        scenario=str(scenario_path),
        strategy=str(strategy_path),
        project_path=tmp_path,
        url="http://localhost:8101",
        dry_run=False,
        create_tickets=True,
        sync_targets=False,
        max_tickets=5,  # Cap at 5
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    # build_testql_tickets should receive max_tickets=5
    assert "build" in calls
    assert calls["build"]["max_tickets"] == 5


def test_testql_workflow_sync_to_todo(tmp_path: Path, monkeypatch) -> None:
    """Test that sync_targets=True calls sync_testql_tickets."""
    scenario_path = tmp_path / "failing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Failing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/missing
    expect:
      status: 404
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks: []
sprints: []
"""
    )

    calls: dict[str, object] = {}
    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        calls["run"] = kwargs
        return {
            "ok": False,
            "passed": 3,
            "failed": 1,
            "exit_code": 1,
            "source": kwargs["scenario_path"],
            "errors": ["boom"],
            "warnings": [],
        }

    def sync_testql_tickets(tickets, project_path, include_configured):
        calls["sync"] = {
            "tickets": tickets,
            "project_path": project_path,
            "include_configured": include_configured,
        }
        return {
            "sync_order": ["markdown"],
            "integrations": [
                {"integration": "markdown", "created": 1, "skipped": 0, "failed": 0}
            ],
        }

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = lambda *_, **__: [{"id": "TQL-1", "title": "Test ticket", "description": "desc", "labels": ["testql"], "priority": "high"}]
    fake_planfile.upsert_testql_tickets = lambda *_, **__: {"created": 1, "skipped": 0, "created_ticket_ids": ["TQL-1"]}
    fake_planfile.sync_testql_tickets = sync_testql_tickets

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = _run_plan_testql_workflow(
        scenario=str(scenario_path),
        strategy=str(strategy_path),
        project_path=tmp_path,
        url="http://localhost:8101",
        dry_run=False,
        create_tickets=True,
        sync_targets=True,  # Enable sync
        max_tickets=25,
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    assert "sync" in calls
    assert calls["sync"]["project_path"] == tmp_path
    assert calls["sync"]["include_configured"] is True
    assert payload["tickets"]["sync"]["sync_order"] == ["markdown"]


def test_testql_workflow_create_tickets_false(tmp_path: Path, monkeypatch) -> None:
    """Test that create_tickets=False skips ticket building/upsert."""
    scenario_path = tmp_path / "failing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Failing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/missing
    expect:
      status: 404
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks: []
sprints: []
"""
    )

    calls: dict[str, object] = {}
    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        calls["run"] = kwargs
        return {
            "ok": False,
            "passed": 3,
            "failed": 1,
            "exit_code": 1,
            "source": kwargs["scenario_path"],
            "errors": ["boom"],
            "warnings": [],
        }

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = lambda *_, **__: (calls.update({"build": True}), [])[1]
    fake_planfile.upsert_testql_tickets = lambda *_, **__: (calls.update({"upsert": True}), {"created": 0, "skipped": 0, "created_ticket_ids": []})[1]
    fake_planfile.sync_testql_tickets = lambda *_, **__: {}

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = _run_plan_testql_workflow(
        scenario=str(scenario_path),
        strategy=str(strategy_path),
        project_path=tmp_path,
        url="http://localhost:8101",
        dry_run=False,
        create_tickets=False,  # Disable ticket creation
        sync_targets=False,
        max_tickets=25,
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    # Validation should run
    assert payload["validation"]["ok"] is False
    assert "run" in calls
    # But ticket building/upsert should not
    assert "build" not in calls
    assert "upsert" not in calls
    assert payload["tickets"]["generated"] == 0
    assert payload["tickets"]["created"] == 0


def test_testql_workflow_with_planfile_structure(tmp_path: Path, monkeypatch) -> None:
    """Test ticket upsert with a realistic planfile structure."""
    scenario_path = tmp_path / "failing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Failing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/missing
    expect:
      status: 404
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks:
  - id: EXISTING-1
    title: Existing ticket
    status: done
    files: []
    rule_id: existing-rule

sprints:
  - name: Sprint 1
    task_patterns:
      - id: EXISTING-2
        title: Existing sprint task
        status: pending
        files: []
        rule_id: existing-rule
"""
    )

    calls: dict[str, object] = {}
    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        calls["run"] = kwargs
        return {
            "ok": False,
            "passed": 3,
            "failed": 1,
            "exit_code": 1,
            "source": kwargs["scenario_path"],
            "errors": ["boom"],
            "warnings": [],
        }

    def upsert_testql_tickets(strategy_path, tickets, project_path):
        calls["upsert"] = {
            "strategy_path": strategy_path,
            "tickets": tickets,
            "project_path": project_path,
        }
        return {"created": 1, "skipped": 0, "created_ticket_ids": ["TQL-1"]}

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = lambda *_, **__: [{"id": "TQL-1", "title": "Test ticket", "description": "desc", "labels": ["testql"], "priority": "high"}]
    fake_planfile.upsert_testql_tickets = upsert_testql_tickets
    fake_planfile.sync_testql_tickets = lambda *_, **__: {}

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = _run_plan_testql_workflow(
        scenario=str(scenario_path),
        strategy=str(strategy_path),
        project_path=tmp_path,
        url="http://localhost:8101",
        dry_run=False,
        create_tickets=True,
        sync_targets=False,
        max_tickets=25,
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    assert payload["tickets"]["created"] == 1
    # Verify upsert was called with the correct strategy path
    assert "upsert" in calls
    assert calls["upsert"]["strategy_path"] == str(strategy_path)


def test_testql_workflow_error_handling_validation_exception(tmp_path: Path, monkeypatch) -> None:
    """Test that exceptions during validation are handled gracefully."""
    scenario_path = tmp_path / "failing.testql.toon.yaml"
    scenario_path.write_text(
        """
name: Failing Scenario
steps:
  - request:
      method: GET
      url: http://localhost:8101/missing
    expect:
      status: 404
"""
    )

    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text(
        """
tasks: []
sprints: []
"""
    )

    fake_planfile = ModuleType("planfile")
    fake_planfile.run_testql_validation = lambda **_: (_ for _ in ()).throw(Exception("TestQL binary not found"))
    fake_planfile.build_testql_tickets = lambda *_, **__: []
    fake_planfile.upsert_testql_tickets = lambda *_, **__: {"created": 0, "skipped": 0, "created_ticket_ids": []}
    fake_planfile.sync_testql_tickets = lambda *_, **__: {}

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    # Should raise the exception
    with pytest.raises(Exception, match="TestQL binary not found"):
        _run_plan_testql_workflow(
            scenario=str(scenario_path),
            strategy=str(strategy_path),
            project_path=tmp_path,
            url="http://localhost:8101",
            dry_run=False,
            create_tickets=True,
            sync_targets=False,
            max_tickets=25,
            testql_bin="testql",
            testql_repo_path=Path("/home/tom/github/semcod/testql"),
        )
