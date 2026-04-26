"""Workflow runtime for llx.

A *workflow* is an ordered sequence of steps declared in ``llx.yaml`` under
``workflows:``. Each step has a ``kind`` that maps to a built-in handler,
optional ``with`` parameters, an optional ``when`` condition, and an
``on_failure`` policy.

Schema example::

    workflows:
      default:
        description: "Default llx pipeline: scan, validate, execute"
        steps:
          - name: scan
            kind: prefact-scan
            with:
              project: "."
          - name: validate
            kind: plan-validate
            with:
              strategy: planfile.yaml
              cancel_stale: true
          - name: execute
            kind: plan-run
            when: "validate.current > 0"
            with:
              strategy: planfile.yaml
              tier: balanced
          - name: notify
            kind: shell
            on_failure: continue
            with:
              command: echo 'done'

Built-in step kinds (registered in :data:`BUILTIN_STEP_HANDLERS`):

- ``prefact-scan``       – run a prefact code scan; outputs ``issues`` count
- ``plan-validate``      – run prefact-driven ticket-freshness validation
- ``plan-prune-stale``   – physically remove stale (and optional unknown) tickets
- ``plan-run``           – execute planfile tasks (re-uses ``execute_strategy``)
- ``testql``             – run a TestQL scenario through the planfile bridge
- ``shell``              – run a shell command via subprocess
- ``python``             – call ``module:function`` with kwargs

Each handler receives a :class:`StepContext` exposing previous step outputs
(by step name) and is expected to return a :class:`StepOutput`.

Step parameters support shell-style substitution: ``${NAME}`` is replaced with
``os.environ['NAME']`` and ``${NAME:-default}`` falls back to ``default`` when
the variable is unset. Substitution is applied recursively to dicts/lists
before the handler runs, so nested values (e.g. ``with.command``) work too.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

import yaml as _yaml


# ---------------------------------------------------------------------------
# Env-variable substitution
# ---------------------------------------------------------------------------


# Matches ${NAME} or ${NAME:-default} (default may contain anything except `}`).
_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def _substitute_string(value: str, env: Mapping[str, str]) -> str:
    def replace(match: "re.Match[str]") -> str:
        name, default = match.group(1), match.group(2)
        if name in env:
            return env[name]
        if default is not None:
            return default
        return match.group(0)  # leave ${NAME} verbatim if undefined

    return _ENV_VAR_RE.sub(replace, value)


def substitute_env(value: Any, env: Optional[Mapping[str, str]] = None) -> Any:
    """Recursively substitute ``${NAME}`` / ``${NAME:-default}`` in a value.

    Supports ``str``, ``list``, ``tuple`` and ``dict``. Other types are returned
    unchanged. The default environment is ``os.environ`` when ``env`` is None.
    """
    source = os.environ if env is None else env

    if isinstance(value, str):
        return _substitute_string(value, source)
    if isinstance(value, list):
        return [substitute_env(item, source) for item in value]
    if isinstance(value, tuple):
        return tuple(substitute_env(item, source) for item in value)
    if isinstance(value, dict):
        return {key: substitute_env(item, source) for key, item in value.items()}
    return value


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass
class WorkflowStep:
    """Declarative description of a single workflow step."""

    name: str
    kind: str
    params: dict[str, Any] = field(default_factory=dict)
    when: Optional[str] = None
    on_failure: str = "stop"  # "stop" | "continue"


@dataclass
class Workflow:
    """A named ordered sequence of steps."""

    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)


@dataclass
class StepOutput:
    """Result of executing a single step."""

    status: str  # "success" | "failed" | "skipped"
    summary: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class StepContext:
    """Per-step execution context exposed to handlers."""

    project_root: Path
    step: WorkflowStep
    outputs: dict[str, StepOutput]


@dataclass
class StepReport:
    """Structured report row for a finished step."""

    name: str
    kind: str
    status: str
    duration_s: float
    summary: str = ""
    error: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowReport:
    """Aggregate report of a workflow execution."""

    workflow: str
    project: str
    status: str  # "success" | "failed" | "partial"
    steps: list[StepReport] = field(default_factory=list)
    total_duration_s: float = 0.0


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class WorkflowError(RuntimeError):
    """Raised on workflow loading / dispatch errors that should abort the run."""


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _coerce_step(raw: Any, fallback_index: int) -> WorkflowStep:
    if not isinstance(raw, dict):
        raise WorkflowError(f"Workflow step #{fallback_index} must be a mapping")

    name = str(raw.get("name") or f"step-{fallback_index}").strip()
    kind = str(raw.get("kind") or "").strip()
    if not kind:
        raise WorkflowError(f"Workflow step '{name}' is missing 'kind'")

    params_raw = raw.get("with") or raw.get("params") or {}
    if not isinstance(params_raw, dict):
        raise WorkflowError(f"Workflow step '{name}' has non-mapping 'with'/'params'")

    on_failure = str(raw.get("on_failure") or "stop").strip().lower()
    if on_failure not in {"stop", "continue"}:
        raise WorkflowError(
            f"Workflow step '{name}' has invalid on_failure='{on_failure}' (use stop|continue)"
        )

    when = raw.get("when")
    when_str = str(when).strip() if when not in (None, "") else None

    return WorkflowStep(
        name=name,
        kind=kind,
        params=dict(params_raw),
        when=when_str,
        on_failure=on_failure,
    )


def load_workflows_from_data(data: dict[str, Any]) -> dict[str, Workflow]:
    """Load workflows from a parsed YAML mapping.

    Accepts the shape ``{"workflows": {<name>: {...}}}`` (preferred) or a
    bare ``{<name>: {...}}`` mapping.
    """
    raw = data.get("workflows") if isinstance(data, dict) else None
    if raw is None:
        raw = data if isinstance(data, dict) else {}
    if not isinstance(raw, dict):
        raise WorkflowError("'workflows' must be a mapping of name -> definition")

    workflows: dict[str, Workflow] = {}
    for wf_name, wf_data in raw.items():
        if not isinstance(wf_data, dict):
            continue
        steps_raw = wf_data.get("steps") or []
        if not isinstance(steps_raw, list):
            raise WorkflowError(f"Workflow '{wf_name}' steps must be a list")

        steps = [_coerce_step(item, idx) for idx, item in enumerate(steps_raw)]
        workflows[str(wf_name)] = Workflow(
            name=str(wf_name),
            description=str(wf_data.get("description") or ""),
            steps=steps,
        )

    return workflows


def load_workflows(yaml_path: str | Path) -> dict[str, Workflow]:
    """Load workflows from an ``llx.yaml`` (or compatible) file."""
    path = Path(yaml_path)
    if not path.exists():
        return {}
    try:
        data = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise WorkflowError(f"Could not parse {path}: {exc}") from exc
    return load_workflows_from_data(data if isinstance(data, dict) else {})


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------


StepHandler = Callable[[StepContext], StepOutput]


def _resolve_project_path(ctx: StepContext, override: Any = None) -> Path:
    if override:
        candidate = Path(str(override))
        if not candidate.is_absolute():
            candidate = (ctx.project_root / candidate).resolve()
        return candidate
    return ctx.project_root


def _step_prefact_scan(ctx: StepContext) -> StepOutput:
    from llx.integrations.prefact import PrefactError, scan_with_prefact

    project = _resolve_project_path(ctx, ctx.step.params.get("project"))
    prefact_yaml = ctx.step.params.get("prefact_yaml") or ctx.step.params.get("config")
    prefact_bin = ctx.step.params.get("prefact_bin")

    try:
        report = scan_with_prefact(
            project_path=project,
            prefact_yaml=prefact_yaml,
            prefact_bin=prefact_bin,
        )
    except PrefactError as exc:
        return StepOutput(
            status="failed",
            summary="prefact scan unavailable",
            error=str(exc),
            data={"available": False},
        )

    return StepOutput(
        status="success",
        summary=f"prefact found {len(report.issues)} issue(s)",
        data={
            "available": True,
            "backend": report.backend,
            "issues": len(report.issues),
            "files_scanned": report.files_scanned,
            "config_path": str(report.config_path) if report.config_path else None,
            "issue_records": report.issues,
        },
    )


def _step_plan_validate(ctx: StepContext) -> StepOutput:
    from llx.planfile.ticket_freshness import validate_tickets_with_prefact
    from llx.planfile.executor.strategy import _update_task_in_planfile
    from llx.planfile.ticket_pruner import prune_planfile_tickets

    project = _resolve_project_path(ctx, ctx.step.params.get("project"))
    strategy = str(ctx.step.params.get("strategy") or "planfile.yaml")
    ticket_id = ctx.step.params.get("ticket_id")
    require_scan = bool(ctx.step.params.get("require_scan") or False)
    fail_on_stale = bool(ctx.step.params.get("fail_on_stale") or False)
    cancel_stale = bool(
        ctx.step.params.get("cancel_stale")
        if "cancel_stale" in ctx.step.params
        else True
    )
    prune_stale = bool(ctx.step.params.get("prune_stale") or False)
    prune_unknown = bool(ctx.step.params.get("prune_unknown") or False)
    backup = bool(
        ctx.step.params.get("backup") if "backup" in ctx.step.params else True
    )

    report = validate_tickets_with_prefact(
        strategy_path=strategy,
        project_path=project,
        ticket_ids=[str(ticket_id)] if ticket_id else None,
        prefact_yaml=ctx.step.params.get("prefact_yaml"),
        prefact_bin=ctx.step.params.get("prefact_bin"),
        require_scan=require_scan,
    )

    stale_ids = list(report.get("stale_ticket_ids") or [])
    unknown_ids = list(report.get("review_needed_ticket_ids") or [])
    if cancel_stale:
        for tid in stale_ids:
            try:
                _update_task_in_planfile(
                    planfile_path=strategy,
                    task_id=tid,
                    status="canceled",
                    comment="Workflow validate: prefact scan no longer detects issue.",
                )
            except Exception:
                continue

    prune_report: dict[str, Any] | None = None
    if prune_stale or prune_unknown:
        ids_to_prune: set[str] = set()
        if prune_stale:
            ids_to_prune.update(stale_ids)
        if prune_unknown:
            ids_to_prune.update(unknown_ids)
        if ids_to_prune:
            prune_report = prune_planfile_tickets(
                strategy_path=strategy,
                ticket_ids=ids_to_prune,
                backup=backup,
            )
            report["prune"] = prune_report

    summary = (
        f"current={report.get('current', 0)} "
        f"stale={report.get('stale', 0)} "
        f"unknown={report.get('unknown', 0)}"
    )
    if prune_report:
        summary += f" pruned={prune_report['removed']}"

    output = StepOutput(
        status="success",
        summary=summary,
        data={
            "report": report,
            "current": int(report.get("current", 0)),
            "stale": int(report.get("stale", 0)),
            "unknown": int(report.get("unknown", 0)),
            "stale_ticket_ids": stale_ids,
            "unknown_ticket_ids": unknown_ids,
            "pruned_ids": prune_report["removed_ids"] if prune_report else [],
        },
    )

    if fail_on_stale and output.data["stale"] > 0:
        output.status = "failed"
        output.error = f"{output.data['stale']} stale ticket(s) detected"

    return output


def _step_plan_prune_stale(ctx: StepContext) -> StepOutput:
    """Standalone pruner step: remove specified ticket IDs from the planfile."""
    from llx.planfile.ticket_pruner import prune_planfile_tickets

    strategy = str(ctx.step.params.get("strategy") or "planfile.yaml")
    backup = bool(
        ctx.step.params.get("backup") if "backup" in ctx.step.params else True
    )

    explicit_ids = ctx.step.params.get("ticket_ids")
    ids: set[str] = _coerce_skip_ids(explicit_ids) or set()

    # Pull from previous validate-style steps when no explicit IDs given.
    if not ids:
        for prev in ctx.outputs.values():
            data = prev.data or {}
            if ctx.step.params.get("include_unknown"):
                ids.update(str(t) for t in (data.get("unknown_ticket_ids") or []))
            ids.update(str(t) for t in (data.get("stale_ticket_ids") or []))

    if not ids:
        return StepOutput(
            status="success",
            summary="nothing to prune",
            data={"removed": 0, "removed_ids": []},
        )

    prune_report = prune_planfile_tickets(
        strategy_path=strategy,
        ticket_ids=ids,
        backup=backup,
    )
    return StepOutput(
        status="success",
        summary=(
            f"removed={prune_report['removed']} "
            f"backup={prune_report.get('backup_path') or '(no backup)'}"
        ),
        data=prune_report,
    )


def _coerce_skip_ids(value: Any) -> Optional[set[str]]:
    if not value:
        return None
    if isinstance(value, (list, tuple, set)):
        ids = {str(item).strip() for item in value if str(item).strip()}
        return ids or None
    return {str(value).strip()} if str(value).strip() else None


def _step_plan_run(ctx: StepContext) -> StepOutput:
    from llx.planfile.executor_simple import execute_strategy

    project = _resolve_project_path(ctx, ctx.step.params.get("project"))
    strategy = str(ctx.step.params.get("strategy") or "planfile.yaml")
    sprint = ctx.step.params.get("sprint")
    ticket_id = ctx.step.params.get("ticket_id")
    dry_run = bool(ctx.step.params.get("dry_run") or False)
    use_aider = bool(ctx.step.params.get("use_aider") or False)
    max_concurrent = int(ctx.step.params.get("max_concurrent") or 1)
    max_tasks = ctx.step.params.get("max_tasks")
    tier = ctx.step.params.get("tier")

    skip_param = ctx.step.params.get("skip_ticket_ids")
    skip_ids = _coerce_skip_ids(skip_param)
    if skip_ids is None:
        # Fallback: pull stale ticket ids from a previous validate step.
        for prev_name, prev in ctx.outputs.items():
            stale = prev.data.get("stale_ticket_ids") if prev.data else None
            if stale:
                skip_ids = {str(s) for s in stale}
                break

    model_override = None
    if tier:
        from llx.config import LlxConfig

        config = LlxConfig.load(str(project))
        tier_model = config.models.get(str(tier))
        if tier_model is not None:
            model_override = tier_model.model_id

    results = execute_strategy(
        strategy_path=strategy,
        project_path=project,
        sprint_filter=int(sprint) if sprint is not None else None,
        ticket_id=str(ticket_id) if ticket_id else None,
        dry_run=dry_run,
        on_progress=None,
        model_override=model_override,
        max_concurrent=max_concurrent,
        max_tasks=int(max_tasks) if max_tasks else None,
        use_aider=use_aider,
        skip_ticket_ids=skip_ids,
    )

    counts: dict[str, int] = {}
    for result in results:
        status = getattr(result, "status", "unknown") or "unknown"
        counts[status] = counts.get(status, 0) + 1

    overall = "success" if results and counts.get("failed", 0) == 0 else (
        "failed" if counts.get("failed", 0) else "success"
    )

    return StepOutput(
        status=overall,
        summary=f"executed={len(results)} " + " ".join(f"{k}={v}" for k, v in counts.items()),
        data={
            "executed": len(results),
            "counts": counts,
            "skipped_stale": sorted(skip_ids) if skip_ids else [],
        },
    )


def _step_shell(ctx: StepContext) -> StepOutput:
    command = ctx.step.params.get("command")
    if not command:
        return StepOutput(status="failed", error="shell step missing 'command'")

    cwd = _resolve_project_path(ctx, ctx.step.params.get("cwd"))
    env_extra = ctx.step.params.get("env") or {}
    timeout = ctx.step.params.get("timeout")
    check = bool(ctx.step.params.get("check") if "check" in ctx.step.params else True)

    if isinstance(command, list):
        argv = [str(item) for item in command]
        shell = False
    else:
        argv = str(command)
        shell = bool(ctx.step.params.get("shell") if "shell" in ctx.step.params else True)
        if not shell:
            argv = shlex.split(argv)

    import os

    env = None
    if env_extra:
        env = {**os.environ, **{str(k): str(v) for k, v in env_extra.items()}}

    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return StepOutput(
            status="failed",
            summary="shell timeout",
            error=str(exc),
        )
    except FileNotFoundError as exc:
        return StepOutput(status="failed", error=str(exc))

    failed = proc.returncode != 0 and check
    return StepOutput(
        status="failed" if failed else "success",
        summary=f"exit={proc.returncode}",
        error=(proc.stderr.strip() if failed else None) or None,
        data={
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        },
    )


def _step_testql(ctx: StepContext) -> StepOutput:
    """Run TestQL DSL validation and bridge results into planfile."""
    from llx.cli.app import _run_plan_testql_workflow

    project = _resolve_project_path(ctx, ctx.step.params.get("project"))
    scenario = ctx.step.params.get("scenario")
    if not scenario:
        return StepOutput(status="failed", error="testql step requires 'scenario'")

    strategy = str(ctx.step.params.get("strategy") or "planfile.yaml")
    url = str(ctx.step.params.get("url") or "http://localhost:8101")
    dry_run = bool(ctx.step.params.get("dry_run") or False)
    create_tickets = bool(
        ctx.step.params.get("create_tickets")
        if "create_tickets" in ctx.step.params
        else True
    )
    sync_targets = bool(
        ctx.step.params.get("sync_targets")
        if "sync_targets" in ctx.step.params
        else True
    )
    max_tickets = int(ctx.step.params.get("max_tickets") or 25)
    testql_bin = str(ctx.step.params.get("testql_bin") or "testql")
    testql_repo_path = ctx.step.params.get("testql_repo_path") or "/home/tom/github/oqlos/testql"
    fail_on_failure = bool(
        ctx.step.params.get("fail_on_failure")
        if "fail_on_failure" in ctx.step.params
        else True
    )

    try:
        payload = _run_plan_testql_workflow(
            scenario=str(scenario),
            strategy=strategy,
            project_path=project,
            url=url,
            dry_run=dry_run,
            create_tickets=create_tickets,
            sync_targets=sync_targets,
            max_tickets=max_tickets,
            testql_bin=testql_bin,
            testql_repo_path=Path(str(testql_repo_path)),
        )
    except Exception as exc:
        return StepOutput(status="failed", error=f"{type(exc).__name__}: {exc}")

    validation = payload.get("validation", {})
    tickets = payload.get("tickets", {})
    summary = (
        f"passed={int(validation.get('passed') or 0)} "
        f"failed={int(validation.get('failed') or 0)} "
        f"tickets_created={int(tickets.get('created') or 0)}"
    )
    status = "success" if (not fail_on_failure or bool(validation.get("ok"))) else "failed"

    output = StepOutput(
        status=status,
        summary=summary,
        data={
            "validation": dict(validation),
            "tickets": dict(tickets),
            "scenario": payload.get("scenario"),
            "strategy": payload.get("strategy"),
        },
    )
    if status == "failed":
        output.error = "TestQL validation failed"
    return output


def _step_python(ctx: StepContext) -> StepOutput:
    target = ctx.step.params.get("target") or ctx.step.params.get("call")
    if not target or ":" not in str(target):
        return StepOutput(
            status="failed",
            error="python step requires 'target' as 'module:function'",
        )

    module_name, _, attr = str(target).partition(":")
    kwargs = ctx.step.params.get("kwargs") or {}
    if not isinstance(kwargs, dict):
        return StepOutput(status="failed", error="python step 'kwargs' must be a mapping")

    try:
        module = import_module(module_name)
        func = getattr(module, attr)
        result = func(**kwargs) if callable(func) else None
    except Exception as exc:
        return StepOutput(status="failed", error=f"{type(exc).__name__}: {exc}")

    return StepOutput(
        status="success",
        summary=f"called {target}",
        data={"return": result},
    )


BUILTIN_STEP_HANDLERS: dict[str, StepHandler] = {
    "prefact-scan": _step_prefact_scan,
    "plan-validate": _step_plan_validate,
    "plan-prune-stale": _step_plan_prune_stale,
    "plan-run": _step_plan_run,
    "testql": _step_testql,
    "shell": _step_shell,
    "python": _step_python,
}


# ---------------------------------------------------------------------------
# Conditional evaluation
# ---------------------------------------------------------------------------


def _build_when_context(outputs: dict[str, StepOutput]) -> dict[str, Any]:
    """Build a flat mapping of previous-step data for ``when`` evaluation."""
    ctx: dict[str, Any] = {}
    for name, output in outputs.items():
        ctx[name] = {
            "status": output.status,
            "summary": output.summary,
            "error": output.error,
            **(output.data or {}),
        }
    return ctx


def _evaluate_when(expr: Optional[str], outputs: dict[str, StepOutput]) -> bool:
    if not expr:
        return True
    try:
        # Restricted evaluation: no builtins, only previous-step outputs.
        return bool(eval(expr, {"__builtins__": {}}, _build_when_context(outputs)))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_workflow(
    workflow: Workflow,
    project_path: str | Path = ".",
    *,
    handlers: Optional[dict[str, StepHandler]] = None,
    on_step: Optional[Callable[[StepReport], None]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> WorkflowReport:
    """Execute a workflow synchronously and return an aggregate report.

    ``env`` is used to expand ``${VAR}`` / ``${VAR:-default}`` references in
    step parameters. Defaults to ``os.environ``.
    """
    project_root = Path(project_path).resolve()
    registry = dict(BUILTIN_STEP_HANDLERS)
    if handlers:
        registry.update(handlers)
    env_source = os.environ if env is None else env

    outputs: dict[str, StepOutput] = {}
    step_reports: list[StepReport] = []
    workflow_failed = False
    aborted = False

    started_total = time.perf_counter()
    for step in workflow.steps:
        if aborted:
            skipped = StepOutput(status="skipped", summary="previous step aborted")
            outputs[step.name] = skipped
            report = StepReport(
                name=step.name,
                kind=step.kind,
                status="skipped",
                duration_s=0.0,
                summary=skipped.summary,
            )
            step_reports.append(report)
            if on_step:
                on_step(report)
            continue

        if not _evaluate_when(step.when, outputs):
            skipped = StepOutput(status="skipped", summary=f"when='{step.when}' false")
            outputs[step.name] = skipped
            report = StepReport(
                name=step.name,
                kind=step.kind,
                status="skipped",
                duration_s=0.0,
                summary=skipped.summary,
            )
            step_reports.append(report)
            if on_step:
                on_step(report)
            continue

        handler = registry.get(step.kind)
        started = time.perf_counter()
        if handler is None:
            output = StepOutput(
                status="failed",
                error=f"unknown step kind '{step.kind}'",
            )
        else:
            resolved_step = WorkflowStep(
                name=step.name,
                kind=step.kind,
                params=substitute_env(step.params, env_source),
                when=step.when,
                on_failure=step.on_failure,
            )
            try:
                output = handler(StepContext(
                    project_root=project_root,
                    step=resolved_step,
                    outputs=outputs,
                ))
            except Exception as exc:
                output = StepOutput(status="failed", error=f"{type(exc).__name__}: {exc}")
        duration = time.perf_counter() - started

        outputs[step.name] = output
        report = StepReport(
            name=step.name,
            kind=step.kind,
            status=output.status,
            duration_s=duration,
            summary=output.summary,
            error=output.error,
            data=output.data,
        )
        step_reports.append(report)
        if on_step:
            on_step(report)

        if output.status == "failed":
            workflow_failed = True
            if step.on_failure == "stop":
                aborted = True

    total_duration = time.perf_counter() - started_total
    if aborted:
        overall = "failed"
    elif workflow_failed:
        overall = "partial"
    else:
        overall = "success"

    return WorkflowReport(
        workflow=workflow.name,
        project=str(project_root),
        status=overall,
        steps=step_reports,
        total_duration_s=total_duration,
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def report_to_dict(report: WorkflowReport) -> dict[str, Any]:
    return {
        "workflow": report.workflow,
        "project": report.project,
        "status": report.status,
        "total_duration_s": round(report.total_duration_s, 3),
        "steps": [
            {
                "name": step.name,
                "kind": step.kind,
                "status": step.status,
                "duration_s": round(step.duration_s, 3),
                "summary": step.summary,
                "error": step.error,
                "data": step.data,
            }
            for step in report.steps
        ],
    }
