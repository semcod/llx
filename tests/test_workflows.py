"""Tests for the llx workflow runtime and `llx run` CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from llx import workflows as workflows_mod
from llx.cli.app import app as llx_app
from llx.workflows import (
    BUILTIN_STEP_HANDLERS,
    StepContext,
    StepOutput,
    Workflow,
    WorkflowError,
    WorkflowStep,
    load_workflows,
    load_workflows_from_data,
    report_to_dict,
    run_workflow,
)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_workflows_from_data_parses_steps() -> None:
    data = {
        "workflows": {
            "default": {
                "description": "demo",
                "steps": [
                    {"name": "a", "kind": "shell", "with": {"command": "true"}},
                    {"name": "b", "kind": "python", "params": {"target": "os:getcwd"}},
                ],
            }
        }
    }

    workflows = load_workflows_from_data(data)

    assert set(workflows) == {"default"}
    wf = workflows["default"]
    assert wf.description == "demo"
    assert [s.name for s in wf.steps] == ["a", "b"]
    assert wf.steps[0].kind == "shell"
    assert wf.steps[0].params == {"command": "true"}
    assert wf.steps[1].params == {"target": "os:getcwd"}


def test_load_workflows_rejects_step_without_kind() -> None:
    data = {"workflows": {"bad": {"steps": [{"name": "x"}]}}}
    with pytest.raises(WorkflowError):
        load_workflows_from_data(data)


def test_load_workflows_rejects_invalid_on_failure() -> None:
    data = {"workflows": {"bad": {"steps": [{"name": "x", "kind": "shell", "on_failure": "ignore"}]}}}
    with pytest.raises(WorkflowError):
        load_workflows_from_data(data)


def test_load_workflows_returns_empty_when_file_missing(tmp_path: Path) -> None:
    assert load_workflows(tmp_path / "missing.yaml") == {}


def test_load_workflows_reads_from_file(tmp_path: Path) -> None:
    yaml_path = tmp_path / "llx.yaml"
    _write(
        yaml_path,
        yaml.safe_dump(
            {
                "workflows": {
                    "demo": {
                        "steps": [
                            {"name": "echo", "kind": "shell", "with": {"command": "true"}},
                        ]
                    }
                }
            },
            sort_keys=False,
        ),
    )

    workflows = load_workflows(yaml_path)
    assert "demo" in workflows
    assert workflows["demo"].steps[0].kind == "shell"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _record_handler(history: list[str], status: str = "success", data: dict | None = None):
    def handler(ctx: StepContext) -> StepOutput:
        history.append(ctx.step.name)
        return StepOutput(status=status, summary=ctx.step.name, data=data or {})

    return handler


def test_run_workflow_executes_steps_in_order(tmp_path: Path) -> None:
    history: list[str] = []
    handlers = {"record": _record_handler(history)}
    workflow = Workflow(
        name="seq",
        steps=[
            WorkflowStep(name="alpha", kind="record"),
            WorkflowStep(name="beta", kind="record"),
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path, handlers=handlers)

    assert history == ["alpha", "beta"]
    assert report.status == "success"
    assert [s.status for s in report.steps] == ["success", "success"]


def test_run_workflow_when_skips_step(tmp_path: Path) -> None:
    history: list[str] = []
    handlers = {
        "record": _record_handler(history, data={"current": 0}),
        "noop": _record_handler(history),
    }
    workflow = Workflow(
        name="cond",
        steps=[
            WorkflowStep(name="check", kind="record", params={}),
            WorkflowStep(
                name="execute",
                kind="noop",
                when="check['current'] > 0",
            ),
            WorkflowStep(name="finalize", kind="record"),
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path, handlers=handlers)

    statuses = {s.name: s.status for s in report.steps}
    assert statuses == {"check": "success", "execute": "skipped", "finalize": "success"}
    assert history == ["check", "finalize"]


def test_run_workflow_on_failure_stop_aborts_remaining(tmp_path: Path) -> None:
    history: list[str] = []
    handlers = {
        "record": _record_handler(history),
        "boom": _record_handler(history, status="failed"),
    }
    workflow = Workflow(
        name="stop",
        steps=[
            WorkflowStep(name="ok", kind="record"),
            WorkflowStep(name="kaboom", kind="boom"),
            WorkflowStep(name="never", kind="record"),
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path, handlers=handlers)

    statuses = [s.status for s in report.steps]
    assert statuses == ["success", "failed", "skipped"]
    assert report.status == "failed"
    assert history == ["ok", "kaboom"]


def test_run_workflow_on_failure_continue_keeps_going(tmp_path: Path) -> None:
    history: list[str] = []
    handlers = {
        "record": _record_handler(history),
        "boom": _record_handler(history, status="failed"),
    }
    workflow = Workflow(
        name="cont",
        steps=[
            WorkflowStep(name="kaboom", kind="boom", on_failure="continue"),
            WorkflowStep(name="after", kind="record"),
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path, handlers=handlers)

    assert [s.status for s in report.steps] == ["failed", "success"]
    assert report.status == "partial"
    assert history == ["kaboom", "after"]


def test_run_workflow_unknown_kind_fails(tmp_path: Path) -> None:
    workflow = Workflow(
        name="bad",
        steps=[WorkflowStep(name="ghost", kind="not-registered")],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    assert report.status == "failed"
    assert "unknown step kind" in (report.steps[0].error or "")


# ---------------------------------------------------------------------------
# Built-in step handlers
# ---------------------------------------------------------------------------


def test_shell_step_captures_exit_code(tmp_path: Path) -> None:
    workflow = Workflow(
        name="sh",
        steps=[WorkflowStep(name="echo", kind="shell", params={"command": "echo hello"})],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    assert report.status == "success"
    step = report.steps[0]
    assert step.status == "success"
    assert step.data["exit_code"] == 0
    assert "hello" in step.data["stdout"]


def test_shell_step_failure_is_propagated(tmp_path: Path) -> None:
    workflow = Workflow(
        name="sh",
        steps=[WorkflowStep(name="bad", kind="shell", params={"command": "exit 7"})],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    assert report.status == "failed"
    assert report.steps[0].data["exit_code"] == 7


def test_python_step_calls_module_function(tmp_path: Path) -> None:
    workflow = Workflow(
        name="py",
        steps=[
            WorkflowStep(
                name="cwd",
                kind="python",
                params={"target": "os.path:abspath", "kwargs": {"path": str(tmp_path)}},
            )
        ],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    assert report.status == "success"
    assert report.steps[0].data["return"] == str(tmp_path.resolve())


def test_python_step_validates_target_format(tmp_path: Path) -> None:
    workflow = Workflow(
        name="py",
        steps=[WorkflowStep(name="bad", kind="python", params={"target": "no_colon"})],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    assert report.status == "failed"
    assert "module:function" in (report.steps[0].error or "")


def test_prefact_scan_step_wraps_adapter(monkeypatch, tmp_path: Path) -> None:
    from llx.integrations.prefact import PrefactScanReport

    fake_report = PrefactScanReport(
        issues=[{"rule_id": "x", "file": "a.py", "line": 1}],
        files_scanned=1,
        backend="engine",
        raw_total=1,
    )
    monkeypatch.setattr(
        "llx.integrations.prefact.scan_with_prefact",
        lambda **_kwargs: fake_report,
    )

    workflow = Workflow(
        name="pf",
        steps=[WorkflowStep(name="scan", kind="prefact-scan")],
    )
    report = run_workflow(workflow, project_path=tmp_path)

    step = report.steps[0]
    assert step.status == "success"
    assert step.data["available"] is True
    assert step.data["backend"] == "engine"
    assert step.data["issues"] == 1


def test_plan_validate_step_uses_freshness_api(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_validate(**kwargs):
        captured.update(kwargs)
        return {
            "current": 1,
            "stale": 2,
            "unknown": 0,
            "stale_ticket_ids": ["S1", "S2"],
            "scan": {"available": True, "backend": "engine"},
        }

    monkeypatch.setattr(
        "llx.planfile.ticket_freshness.validate_tickets_with_prefact",
        fake_validate,
    )

    workflow = Workflow(
        name="vd",
        steps=[
            WorkflowStep(
                name="validate",
                kind="plan-validate",
                params={"strategy": "planfile.yaml", "fail_on_stale": True},
            )
        ],
    )
    report = run_workflow(workflow, project_path=tmp_path)

    step = report.steps[0]
    assert step.status == "failed"  # fail_on_stale -> failed
    assert step.data["stale_ticket_ids"] == ["S1", "S2"]
    assert captured["strategy_path"] == "planfile.yaml"


def test_plan_run_step_passes_skip_ticket_ids_from_previous_step(monkeypatch, tmp_path: Path) -> None:
    received: dict[str, object] = {}

    class _FakeResult:
        def __init__(self, status: str) -> None:
            self.status = status

    def fake_execute(**kwargs):
        received.update(kwargs)
        return [_FakeResult("success")]

    monkeypatch.setattr(
        "llx.planfile.executor_simple.execute_strategy",
        fake_execute,
    )

    workflow = Workflow(
        name="run",
        steps=[
            WorkflowStep(
                name="validate",
                kind="plan-validate",
                params={"strategy": "planfile.yaml"},
            ),
            WorkflowStep(
                name="execute",
                kind="plan-run",
                params={"strategy": "planfile.yaml"},
            ),
        ],
    )

    monkeypatch.setattr(
        "llx.planfile.ticket_freshness.validate_tickets_with_prefact",
        lambda **_kwargs: {
            "current": 1, "stale": 1, "unknown": 0,
            "stale_ticket_ids": ["S9"],
            "scan": {"available": True, "backend": "engine"},
        },
    )

    report = run_workflow(workflow, project_path=tmp_path)

    assert report.status == "success"
    assert received["skip_ticket_ids"] == {"S9"}


# ---------------------------------------------------------------------------
# CLI: `llx run`
# ---------------------------------------------------------------------------


def _llx_yaml_with_default(tmp_path: Path) -> Path:
    path = tmp_path / "llx.yaml"
    _write(
        path,
        yaml.safe_dump(
            {
                "workflows": {
                    "default": {
                        "description": "echo only",
                        "steps": [
                            {"name": "echo", "kind": "shell", "with": {"command": "echo cli-ok"}},
                        ],
                    }
                }
            },
            sort_keys=False,
        ),
    )
    return path


def test_cli_run_executes_default_workflow(tmp_path: Path) -> None:
    _llx_yaml_with_default(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        llx_app,
        ["run", "default", "--project", str(tmp_path), "--format", "yaml"],
    )

    assert result.exit_code == 0, result.stdout
    parsed = yaml.safe_load(result.stdout)
    assert parsed["workflow"] == "default"
    assert parsed["status"] == "success"
    assert parsed["steps"][0]["name"] == "echo"


def test_cli_run_list_only(tmp_path: Path) -> None:
    _llx_yaml_with_default(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        llx_app,
        ["run", "--project", str(tmp_path), "--list"],
    )

    assert result.exit_code == 0, result.stdout
    # --list prints to stderr in our impl, mixed into combined output
    assert "default" in result.output


def test_cli_run_unknown_workflow_returns_2(tmp_path: Path) -> None:
    _llx_yaml_with_default(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        llx_app,
        ["run", "ghost", "--project", str(tmp_path)],
    )

    assert result.exit_code == 2


def test_cli_run_markdown_includes_yaml_codeblock(tmp_path: Path) -> None:
    _llx_yaml_with_default(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        llx_app,
        ["run", "default", "--project", str(tmp_path)],
    )

    assert result.exit_code == 0, result.stdout
    assert "## Workflow: default" in result.stdout
    assert "```yaml" in result.stdout
    assert "echo" in result.stdout


# ---------------------------------------------------------------------------
# Sanity: registry exposes built-ins
# ---------------------------------------------------------------------------


def test_builtin_handlers_registered() -> None:
    assert set(BUILTIN_STEP_HANDLERS) >= {
        "prefact-scan",
        "plan-validate",
        "plan-run",
        "testql",
        "shell",
        "python",
    }


def test_report_to_dict_round_trips_status() -> None:
    workflow = Workflow(
        name="t",
        steps=[WorkflowStep(name="x", kind="shell", params={"command": "true"})],
    )
    report = run_workflow(workflow, project_path=Path("/tmp"))
    payload = report_to_dict(report)
    assert payload["workflow"] == "t"
    assert payload["status"] == "success"
    assert payload["steps"][0]["status"] == "success"


# ---------------------------------------------------------------------------
# Env-variable substitution
# ---------------------------------------------------------------------------


def test_substitute_env_replaces_named_var() -> None:
    from llx.workflows import substitute_env

    assert substitute_env("hi ${NAME}", {"NAME": "world"}) == "hi world"


def test_substitute_env_uses_default_when_missing() -> None:
    from llx.workflows import substitute_env

    assert substitute_env("v=${UNSET:-fallback}", {}) == "v=fallback"


def test_substitute_env_keeps_unmatched_placeholders_verbatim() -> None:
    from llx.workflows import substitute_env

    assert substitute_env("v=${UNSET}", {}) == "v=${UNSET}"


def test_substitute_env_recurses_into_collections() -> None:
    from llx.workflows import substitute_env

    env = {"BIN": "/usr/bin/echo"}
    payload = {
        "command": ["${BIN}", "${MISSING:-default-arg}"],
        "nested": {"target": "${BIN}"},
        "tuple": ("${BIN}",),
        "untouched": 42,
    }

    resolved = substitute_env(payload, env)
    assert resolved == {
        "command": ["/usr/bin/echo", "default-arg"],
        "nested": {"target": "/usr/bin/echo"},
        "tuple": ("/usr/bin/echo",),
        "untouched": 42,
    }


def test_run_workflow_substitutes_env_in_step_params(tmp_path: Path) -> None:
    workflow = Workflow(
        name="env",
        steps=[
            WorkflowStep(
                name="echo",
                kind="shell",
                params={"command": "echo ${GREETING:-hello}-${NAME}"},
            ),
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path, env={"NAME": "tom"})

    step = report.steps[0]
    assert step.status == "success"
    assert "hello-tom" in step.data["stdout"]


def test_run_workflow_env_substitution_does_not_mutate_workflow(tmp_path: Path) -> None:
    step = WorkflowStep(
        name="echo",
        kind="shell",
        params={"command": "echo ${NAME}"},
    )
    workflow = Workflow(name="env", steps=[step])

    run_workflow(workflow, project_path=tmp_path, env={"NAME": "alice"})

    # Workflow definition must be untouched so it can be re-run.
    assert step.params == {"command": "echo ${NAME}"}


# ---------------------------------------------------------------------------
# testql step
# ---------------------------------------------------------------------------


def test_testql_step_requires_scenario(tmp_path: Path) -> None:
    workflow = Workflow(
        name="testql",
        steps=[WorkflowStep(name="run", kind="testql")],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    assert report.steps[0].status == "failed"
    assert "scenario" in (report.steps[0].error or "")


def test_testql_step_success_passes_payload_through(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_workflow(**kwargs):
        captured.update(kwargs)
        return {
            "scenario": kwargs["scenario"],
            "strategy": kwargs["strategy"],
            "validation": {"ok": True, "passed": 3, "failed": 0, "exit_code": 0,
                           "source": "real", "errors": [], "warnings": []},
            "tickets": {"generated": 0, "created": 0, "skipped": 0,
                        "created_ticket_ids": [], "sync": None},
        }

    monkeypatch.setattr("llx.cli.app._run_plan_testql_workflow", fake_workflow)

    workflow = Workflow(
        name="t",
        steps=[
            WorkflowStep(
                name="run",
                kind="testql",
                params={
                    "scenario": "tests/cases/smoke.testql.toon.yaml",
                    "strategy": "planfile.yaml",
                    "url": "http://example.invalid",
                    "max_tickets": 5,
                },
            )
        ],
    )

    report = run_workflow(workflow, project_path=tmp_path)
    step = report.steps[0]
    assert step.status == "success"
    assert step.data["validation"]["passed"] == 3
    assert captured["scenario"] == "tests/cases/smoke.testql.toon.yaml"
    assert captured["max_tickets"] == 5


def test_testql_step_marks_failed_when_validation_not_ok(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "llx.cli.app._run_plan_testql_workflow",
        lambda **_kwargs: {
            "scenario": "x",
            "strategy": "planfile.yaml",
            "validation": {"ok": False, "passed": 0, "failed": 2, "exit_code": 2,
                           "source": "real", "errors": ["e"], "warnings": []},
            "tickets": {"generated": 1, "created": 1, "skipped": 0,
                        "created_ticket_ids": ["T1"], "sync": None},
        },
    )

    workflow = Workflow(
        name="t",
        steps=[WorkflowStep(name="run", kind="testql", params={"scenario": "x"})],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    step = report.steps[0]
    assert step.status == "failed"
    assert step.data["tickets"]["created"] == 1
    assert step.error == "TestQL validation failed"


def test_testql_step_can_ignore_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "llx.cli.app._run_plan_testql_workflow",
        lambda **_kwargs: {
            "scenario": "x",
            "strategy": "planfile.yaml",
            "validation": {"ok": False, "passed": 0, "failed": 1, "exit_code": 2,
                           "source": "real", "errors": [], "warnings": []},
            "tickets": {"generated": 0, "created": 0, "skipped": 0,
                        "created_ticket_ids": [], "sync": None},
        },
    )

    workflow = Workflow(
        name="t",
        steps=[
            WorkflowStep(
                name="run",
                kind="testql",
                params={"scenario": "x", "fail_on_failure": False},
            )
        ],
    )
    report = run_workflow(workflow, project_path=tmp_path)
    assert report.steps[0].status == "success"
