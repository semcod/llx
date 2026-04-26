from __future__ import annotations

import importlib

from llx.planfile.executor.base import TaskResult
from llx.planfile.executor.task import _parse_llm_response


def test_parse_llm_response_ignores_no_changes_inside_code_blocks() -> None:
    response = (
        "```python:llx/cli/app.py\n"
        "def f():\n"
        "    console.print(\"No changes needed\")\n"
        "```\n"
    )

    parsed = _parse_llm_response(response)

    assert parsed["issue_not_found"] is False
    assert parsed["changes_made"] is True
    assert parsed["message"] == "LLM reports changes made"


def test_persist_failed_results_skips_synthetic_ticket_ids(tmp_path, monkeypatch) -> None:
    app_mod = importlib.import_module("llx.cli.app")
    calls: list[tuple[str, str, str, str]] = []
    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text("tasks:\n  - id: Q01\n", encoding="utf-8")

    def fake_update(planfile_path: str, task_id: str, status: str, comment: str) -> bool:
        calls.append((planfile_path, task_id, status, comment))
        return True

    monkeypatch.setattr("llx.planfile.executor.strategy._update_task_in_planfile", fake_update)

    app_mod._persist_failed_results(
        [
            TaskResult(
                ticket_id="task-abc123",
                task_name="Fix issue",
                status="no_changes",
                model_used="m",
                response="",
                validation_message="No changes needed: No action needed.",
            )
        ],
        str(strategy_path),
    )

    assert calls == []


def test_persist_failed_results_updates_top_level_q_tickets(tmp_path, monkeypatch) -> None:
    app_mod = importlib.import_module("llx.cli.app")
    calls: list[tuple[str, str, str, str]] = []
    strategy_path = tmp_path / "planfile.yaml"
    strategy_path.write_text("tasks:\n  - id: Q01\n", encoding="utf-8")

    def fake_update(planfile_path: str, task_id: str, status: str, comment: str) -> bool:
        calls.append((planfile_path, task_id, status, comment))
        return True

    monkeypatch.setattr("llx.planfile.executor.strategy._update_task_in_planfile", fake_update)

    app_mod._persist_failed_results(
        [
            TaskResult(
                ticket_id="Q01",
                task_name="Fix issue",
                status="no_changes",
                model_used="m",
                response="",
                validation_message="No changes needed: No action needed.",
            )
        ],
        str(strategy_path),
    )

    assert len(calls) == 1
    assert calls[0][1] == "Q01"
    # 'no_changes' result status maps to 'canceled' ticket status (issue not found)
    assert calls[0][2] == "canceled"
