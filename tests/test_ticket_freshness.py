"""Tests for prefact-driven ticket freshness validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from llx.cli.app import app as llx_app
from llx.integrations import prefact as prefact_adapter
from llx.integrations.prefact import (
    PrefactError,
    PrefactScanReport,
    _record_from_issue,
    scan_with_prefact,
)
from llx.planfile.ticket_freshness import validate_tickets_with_prefact


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _planfile_with_two_rule_tickets() -> str:
    return yaml.safe_dump(
        {
            "tasks": [
                {
                    "id": "F1",
                    "name": "Fix unused imports",
                    "rule_id": "unused-imports",
                    "files": ["src/a.py"],
                },
                {
                    "id": "F2",
                    "name": "Fix wildcard imports",
                    "rule_id": "wildcard-imports",
                    "files": ["src/a.py"],
                },
            ]
        },
        sort_keys=False,
    )


# ---------------------------------------------------------------------------
# scan_with_prefact / record normalisation
# ---------------------------------------------------------------------------


class _FakeIssue:
    """Minimal stand-in for prefact's Issue dataclass."""

    def __init__(self, rule_id: str, file: Path, line: int, col: int = 1) -> None:
        self.rule_id = rule_id
        self.file = file
        self.line = line
        self.col = col
        self.message = f"{rule_id} at {file}:{line}"
        self.severity = "warning"


def test_record_from_issue_normalises_relative_path(tmp_path: Path) -> None:
    issue = _FakeIssue("unused-imports", tmp_path / "src/a.py", 3)
    record = _record_from_issue(issue, tmp_path)

    assert record == {
        "rule_id": "unused-imports",
        "file": "src/a.py",
        "line": 3,
        "col": 1,
        "severity": "warning",
        "message": f"unused-imports at {tmp_path / 'src/a.py'}:3",
    }


def test_record_from_issue_drops_records_without_rule_id(tmp_path: Path) -> None:
    issue = _FakeIssue("", tmp_path / "src/a.py", 3)
    assert _record_from_issue(issue, tmp_path) is None


def test_scan_with_prefact_uses_engine(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "src/a.py"
    _write(target, "import os\n")
    issues = [_FakeIssue("unused-imports", target, 1)]

    def fake_engine_scan(project_path, prefact_yaml):  # noqa: ARG001
        return PrefactScanReport(
            issues=[
                rec for rec in (
                    _record_from_issue(item, project_path) for item in issues
                ) if rec is not None
            ],
            files_scanned=1,
            backend="engine",
            raw_total=1,
        )

    monkeypatch.setattr(prefact_adapter, "_scan_with_engine", fake_engine_scan)

    report = scan_with_prefact(tmp_path)

    assert report.backend == "engine"
    assert report.issues == [
        {
            "rule_id": "unused-imports",
            "file": "src/a.py",
            "line": 1,
            "col": 1,
            "severity": "warning",
            "message": f"unused-imports at {target}:1",
        }
    ]


def test_scan_with_prefact_falls_back_to_subprocess(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(prefact_adapter, "_scan_with_engine", lambda *a, **k: None)

    fallback_report = PrefactScanReport(
        issues=[{"rule_id": "wildcard-imports", "file": "src/a.py", "line": 2, "col": 1, "severity": "error", "message": "x"}],
        files_scanned=1,
        backend="subprocess",
        raw_total=1,
    )
    monkeypatch.setattr(
        prefact_adapter,
        "_scan_with_subprocess",
        lambda *a, **k: fallback_report,
    )

    report = scan_with_prefact(tmp_path)
    assert report.backend == "subprocess"
    assert report.issues[0]["rule_id"] == "wildcard-imports"


def test_scan_with_prefact_raises_when_no_backend(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(prefact_adapter, "_scan_with_engine", lambda *a, **k: None)
    monkeypatch.setattr(prefact_adapter, "_scan_with_subprocess", lambda *a, **k: None)

    with pytest.raises(PrefactError):
        scan_with_prefact(tmp_path)


# ---------------------------------------------------------------------------
# validate_tickets_with_prefact composition
# ---------------------------------------------------------------------------


def _patch_scan(monkeypatch, issues: list[dict[str, Any]] | None, *, backend: str = "engine") -> None:
    def fake_scan(project_path, **kwargs):  # noqa: ARG001
        if issues is None:
            raise PrefactError("prefact unavailable in this test")
        return PrefactScanReport(
            issues=issues,
            files_scanned=len({i["file"] for i in issues}),
            backend=backend,
            raw_total=len(issues),
        )

    monkeypatch.setattr(
        "llx.planfile.ticket_freshness.scan_with_prefact",
        fake_scan,
    )


def test_validate_tickets_with_prefact_marks_current_and_stale(monkeypatch, tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, _planfile_with_two_rule_tickets())
    _write(tmp_path / "src/a.py", "import os\n")

    _patch_scan(
        monkeypatch,
        [{"rule_id": "unused-imports", "file": "src/a.py", "line": 1, "col": 1, "severity": "info", "message": ""}],
    )

    report = validate_tickets_with_prefact(strategy_path=strategy, project_path=tmp_path)

    assert report["scan"]["available"] is True
    assert report["scan"]["backend"] == "engine"
    assert report["confirmed_current_ticket_ids"] == ["F1"]
    assert report["stale_ticket_ids"] == ["F2"]


def test_validate_tickets_with_prefact_handles_missing_scanner(monkeypatch, tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, _planfile_with_two_rule_tickets())
    _write(tmp_path / "src/a.py", "import os\n")

    _patch_scan(monkeypatch, None)

    report = validate_tickets_with_prefact(strategy_path=strategy, project_path=tmp_path)

    assert report["scan"]["available"] is False
    # Without scan, rule-based tickets fall back to "scan_unavailable" reason
    assert report["current"] == 0
    assert all(t["status"] in {"unknown", "stale"} for t in report["tickets"])


def test_validate_tickets_with_prefact_require_scan_propagates(monkeypatch, tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, _planfile_with_two_rule_tickets())

    _patch_scan(monkeypatch, None)

    with pytest.raises(PrefactError):
        validate_tickets_with_prefact(
            strategy_path=strategy,
            project_path=tmp_path,
            require_scan=True,
        )


# ---------------------------------------------------------------------------
# CLI: `llx plan validate`
# ---------------------------------------------------------------------------


def test_plan_validate_emits_markdown_with_yaml_codeblock(monkeypatch, tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, _planfile_with_two_rule_tickets())
    _write(tmp_path / "src/a.py", "import os\n")

    _patch_scan(
        monkeypatch,
        [{"rule_id": "unused-imports", "file": "src/a.py", "line": 1, "col": 1, "severity": "info", "message": ""}],
    )

    runner = CliRunner()
    result = runner.invoke(
        llx_app,
        ["plan", "validate", str(strategy), "--project", str(tmp_path)],
    )

    assert result.exit_code == 0, result.stdout
    assert "## Ticket Freshness" in result.stdout
    assert "```yaml" in result.stdout
    assert "F1" in result.stdout
    assert "F2" in result.stdout


def test_plan_validate_yaml_format_emits_pure_yaml(monkeypatch, tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, _planfile_with_two_rule_tickets())
    _write(tmp_path / "src/a.py", "import os\n")

    _patch_scan(
        monkeypatch,
        [{"rule_id": "unused-imports", "file": "src/a.py", "line": 1, "col": 1, "severity": "info", "message": ""}],
    )

    runner = CliRunner()
    result = runner.invoke(
        llx_app,
        ["plan", "validate", str(strategy), "--project", str(tmp_path), "--format", "yaml"],
    )

    assert result.exit_code == 0, result.stdout
    parsed = yaml.safe_load(result.stdout)
    assert parsed["confirmed_current_ticket_ids"] == ["F1"]
    assert parsed["stale_ticket_ids"] == ["F2"]
    assert parsed["scan"]["available"] is True


def test_load_planfile_validator_uses_top_level_when_available(monkeypatch) -> None:
    import sys
    import types

    from llx.planfile import ticket_freshness as tf

    sentinel = lambda **_kwargs: {"sentinel": "top-level"}  # noqa: E731
    fake_pkg = types.ModuleType("planfile")
    fake_pkg.validate_planfile_tickets = sentinel
    monkeypatch.setitem(sys.modules, "planfile", fake_pkg)

    resolved = tf._load_planfile_validator()
    assert resolved is sentinel


def test_load_planfile_validator_falls_back_to_submodule(monkeypatch) -> None:
    import sys
    import types

    from llx.planfile import ticket_freshness as tf

    # Top-level module exists but does NOT export the function
    pkg = types.ModuleType("planfile")
    monkeypatch.setitem(sys.modules, "planfile", pkg)

    sentinel = lambda **_kwargs: {"sentinel": "submodule"}  # noqa: E731
    sub = types.ModuleType("planfile.ticket_validation")
    sub.validate_planfile_tickets = sentinel
    monkeypatch.setitem(sys.modules, "planfile.ticket_validation", sub)

    resolved = tf._load_planfile_validator()
    assert resolved is sentinel


def test_load_planfile_validator_raises_prefacterror_when_missing(monkeypatch) -> None:
    import sys
    import types

    from llx.planfile import ticket_freshness as tf

    pkg = types.ModuleType("planfile")
    monkeypatch.setitem(sys.modules, "planfile", pkg)
    monkeypatch.setitem(
        sys.modules,
        "planfile.ticket_validation",
        types.ModuleType("planfile.ticket_validation"),
    )
    monkeypatch.setitem(
        sys.modules,
        "planfile.validation",
        types.ModuleType("planfile.validation"),
    )

    with pytest.raises(PrefactError):
        tf._load_planfile_validator()


def test_validate_tickets_with_prefact_uses_submodule_validator(monkeypatch, tmp_path: Path) -> None:
    """End-to-end: when only the submodule export exists, validation still works."""
    import sys
    import types

    from llx.planfile import ticket_freshness as tf

    captured: dict[str, object] = {}

    def fake_validator(**kwargs):
        captured.update(kwargs)
        return {
            "current": 1, "stale": 0, "unknown": 0,
            "stale_ticket_ids": [], "review_needed_ticket_ids": [],
            "tickets": [], "filtered_ticket_ids": [],
            "strategy_path": str(kwargs["strategy_path"]),
            "project_path": str(kwargs["project_path"]),
            "scan_available": True, "total": 1,
            "confirmed_current_ticket_ids": ["F1"],
        }

    pkg = types.ModuleType("planfile")
    monkeypatch.setitem(sys.modules, "planfile", pkg)

    sub = types.ModuleType("planfile.ticket_validation")
    sub.validate_planfile_tickets = fake_validator
    monkeypatch.setitem(sys.modules, "planfile.ticket_validation", sub)

    _patch_scan(
        monkeypatch,
        [{"rule_id": "unused-imports", "file": "src/a.py", "line": 1}],
    )

    strategy = tmp_path / "planfile.yaml"
    _write(strategy, _planfile_with_two_rule_tickets())
    _write(tmp_path / "src/a.py", "import os\n")

    report = tf.validate_tickets_with_prefact(
        strategy_path=strategy,
        project_path=tmp_path,
    )

    assert report["confirmed_current_ticket_ids"] == ["F1"]
    assert report["scan"]["available"] is True
    # Submodule validator was actually invoked
    assert captured  # not empty


def test_plan_validate_fail_on_stale_returns_nonzero(monkeypatch, tmp_path: Path) -> None:
    strategy = tmp_path / "planfile.yaml"
    _write(strategy, _planfile_with_two_rule_tickets())
    _write(tmp_path / "src/a.py", "import os\n")

    _patch_scan(
        monkeypatch,
        [{"rule_id": "unused-imports", "file": "src/a.py", "line": 1, "col": 1, "severity": "info", "message": ""}],
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
            "--fail-on-stale",
        ],
    )

    assert result.exit_code == 1
