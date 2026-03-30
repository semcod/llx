"""Tests for the llx fix command aider mode."""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock

fix_mod = importlib.import_module("llx.commands.fix")


def _make_metrics() -> SimpleNamespace:
    return SimpleNamespace(
        total_files=1,
        total_lines=10,
        total_functions=1,
        total_classes=0,
        total_modules=1,
        avg_cc=1.0,
        max_cc=1,
        critical_count=0,
        max_fan_out=0,
        max_fan_in=0,
        dependency_cycles=0,
        dup_groups=0,
        dup_saved_lines=0,
        task_scope="test",
        estimated_context_tokens=100,
    )


def test_fix_uses_aider_when_code_tool_is_enabled(tmp_path, monkeypatch):
    errors_path = tmp_path / "errors.json"
    errors_path.write_text("[]", encoding="utf-8")

    metrics = _make_metrics()
    config = SimpleNamespace(code_tool="aider", run_env="local", default_tier="cheap", models={})
    print_mock = MagicMock()
    captured: dict[str, object] = {}

    monkeypatch.setattr(fix_mod, "analyze_project", lambda path: metrics)
    monkeypatch.setattr(fix_mod.LlxConfig, "load", lambda path: config)
    monkeypatch.setattr(
        fix_mod,
        "load_issue_source",
        lambda path: [{"file": "src/app.py", "message": "Fix me"}],
    )
    monkeypatch.setattr(fix_mod, "build_fix_prompt", lambda *args, **kwargs: "prompt from issues")
    monkeypatch.setattr(fix_mod, "console", SimpleNamespace(print=print_mock))

    def fake_run_aider_fix(*args, **kwargs):
        captured["called"] = True
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {
            "success": True,
            "stdout": "Aider applied changes",
            "stderr": "",
            "command": "aider --model ollama/qwen2.5-coder:7b --message prompt from issues",
            "path": str(kwargs.get("workdir", tmp_path.resolve())),
            "method": "local",
        }

    monkeypatch.setattr(fix_mod, "_run_aider_fix", fake_run_aider_fix)

    fix_mod.fix(
        str(tmp_path),
        errors=str(errors_path),
        apply=False,
        model="ollama/qwen2.5-coder:7b",
        dry_run=False,
        verbose=False,
    )

    assert captured["called"] is True
    assert captured["kwargs"]["workdir"] == tmp_path.resolve()
    assert captured["kwargs"]["prompt"] == "prompt from issues"
    assert captured["kwargs"]["model"] == "ollama/qwen2.5-coder:7b"
    assert captured["kwargs"]["files"] == ["src/app.py"]
    assert captured["kwargs"]["use_docker"] is False
    assert print_mock.called
