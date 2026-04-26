from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import importlib


def test_run_plan_testql_workflow_generates_and_syncs_tickets(monkeypatch) -> None:
    app_mod = importlib.import_module("llx.cli.app")

    calls: dict[str, object] = {}

    fake_planfile = ModuleType("planfile")

    def run_testql_validation(**kwargs):
        calls["run"] = kwargs
        return {
            "ok": False,
            "passed": 2,
            "failed": 1,
            "exit_code": 1,
            "source": kwargs["scenario_path"],
            "errors": ["boom"],
            "warnings": [],
        }

    def build_testql_tickets(report, scenario_path, max_tickets):
        calls["build"] = {"scenario_path": scenario_path, "max_tickets": max_tickets}
        return [{"id": "TQL-1", "title": "t", "description": "d", "labels": ["testql"], "priority": "high"}]

    def upsert_testql_tickets(strategy_path, tickets, project_path):
        calls["upsert"] = {
            "strategy_path": strategy_path,
            "tickets": tickets,
            "project_path": project_path,
        }
        return {"created": 1, "skipped": 0, "created_ticket_ids": ["TQL-1"]}

    def sync_testql_tickets(tickets, project_path, include_configured):
        calls["sync"] = {
            "tickets": tickets,
            "project_path": project_path,
            "include_configured": include_configured,
        }
        return {"sync_order": ["markdown"], "integrations": [{"integration": "markdown", "created": 1, "skipped": 0, "failed": 0}]}

    fake_planfile.run_testql_validation = run_testql_validation
    fake_planfile.build_testql_tickets = build_testql_tickets
    fake_planfile.upsert_testql_tickets = upsert_testql_tickets
    fake_planfile.sync_testql_tickets = sync_testql_tickets

    monkeypatch.setitem(sys.modules, "planfile", fake_planfile)

    payload = app_mod._run_plan_testql_workflow(
        scenario="tests/failing.testql.toon.yaml",
        strategy="planfile.yaml",
        project_path=Path("."),
        url="http://localhost:8101",
        dry_run=False,
        create_tickets=True,
        sync_targets=True,
        max_tickets=5,
        testql_bin="testql",
        testql_repo_path=Path("/home/tom/github/semcod/testql"),
    )

    assert payload["validation"]["ok"] is False
    assert payload["tickets"]["generated"] == 1
    assert payload["tickets"]["created"] == 1
    assert payload["tickets"]["created_ticket_ids"] == ["TQL-1"]
    assert payload["tickets"]["sync"]["sync_order"] == ["markdown"]
    assert "run" in calls and "upsert" in calls and "sync" in calls
