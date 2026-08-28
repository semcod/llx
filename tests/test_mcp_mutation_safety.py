"""Safety tests for write-capable MCP tools."""

from types import SimpleNamespace
import json

import pytest

pytest.importorskip("mcp", reason="MCP tests require llx[mcp] extras")

from llx.mcp.tools.planfile import _handle_planfile_apply, tool_planfile_apply
from llx.mcp.tools.privacy import _handle_llx_privacy_scan, _handle_llx_project_anonymize


@pytest.mark.asyncio
async def test_planfile_apply_defaults_to_dry_run(tmp_path, monkeypatch):
    strategy = tmp_path / "planfile.yaml"
    strategy.write_text("tasks: []\n", encoding="utf-8")
    calls = []

    def fake_execute_strategy(**kwargs):
        calls.append(kwargs)
        return []

    monkeypatch.setattr("llx.planfile.executor.execute_strategy", fake_execute_strategy)
    result = await _handle_planfile_apply(
        {"strategy_path": "planfile.yaml", "project_path": str(tmp_path), "actor": "reviewer"}
    )

    assert result["success"] is True
    assert result["dry_run"] is True
    assert result["requires_approval"] is True
    assert calls[0]["dry_run"] is True
    schema = tool_planfile_apply.definition.inputSchema
    assert schema["properties"]["dry_run"]["default"] is True


@pytest.mark.asyncio
async def test_planfile_live_apply_requires_capability_and_exact_hash(tmp_path, monkeypatch):
    strategy = tmp_path / "planfile.yaml"
    strategy.write_text("tasks: []\n", encoding="utf-8")
    calls = []

    def fake_execute_strategy(**kwargs):
        calls.append(kwargs)
        return [
            SimpleNamespace(
                status="success",
                task_name="demo",
                model_used="test-model",
                error=None,
            )
        ]

    monkeypatch.setattr("llx.planfile.executor.execute_strategy", fake_execute_strategy)
    base = {
        "strategy_path": "planfile.yaml",
        "project_path": str(tmp_path),
        "dry_run": False,
        "actor": "reviewer",
    }
    proposal = await _handle_planfile_apply(base)
    assert proposal["status"] == "approval_required"
    assert calls == []

    monkeypatch.setenv("LLX_MCP_ALLOW_WRITE", "1")
    strategy.write_text("tasks:\n  - id: changed\n", encoding="utf-8")
    stale = await _handle_planfile_apply({**base, "approval_hash": proposal["approval_hash"]})
    assert stale["status"] == "approval_required"
    assert stale["approval_hash"] != proposal["approval_hash"]
    assert calls == []

    applied = await _handle_planfile_apply({**base, "approval_hash": stale["approval_hash"]})
    assert applied["success"] is True
    assert applied["dry_run"] is False
    assert applied["approved_by"] == "reviewer"
    assert calls[0]["dry_run"] is False


@pytest.mark.asyncio
async def test_planfile_rejects_strategy_outside_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    strategy = tmp_path / "outside.yaml"
    strategy.write_text("tasks: []\n", encoding="utf-8")

    result = await _handle_planfile_apply(
        {"strategy_path": str(strategy), "project_path": str(project)}
    )
    assert result["success"] is False
    assert "escapes project root" in result["error"]


@pytest.mark.asyncio
async def test_privacy_scan_redacts_exact_secrets_by_default(monkeypatch):
    monkeypatch.delenv("LLX_MCP_ALLOW_SECRET_OUTPUT", raising=False)
    secret = "person@example.com"
    result = await _handle_llx_privacy_scan({"text": secret, "anonymize": True})

    assert secret not in json.dumps(result)
    assert result["scan"]["details"]["email"] == 1
    assert result["scan"]["sensitive_values_included"] is False


@pytest.mark.asyncio
async def test_project_anonymize_is_dry_run_then_approved_write(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("def describe_user(name):\n    return name\n", encoding="utf-8")
    base = {"path": str(tmp_path), "actor": "reviewer"}

    proposal = await _handle_llx_project_anonymize(base)
    assert proposal["success"] is True
    assert proposal["dry_run"] is True
    assert not (tmp_path / ".llx" / "anonymized").exists()

    monkeypatch.setenv("LLX_MCP_ALLOW_WRITE", "1")
    applied = await _handle_llx_project_anonymize(
        {**base, "dry_run": False, "approval_hash": proposal["approval_hash"]}
    )
    assert applied["success"] is True
    assert applied["dry_run"] is False
    assert (tmp_path / ".llx" / "anonymized" / "app.py").is_file()
    assert (tmp_path / ".llx" / "anonymized" / ".anonymization_context.json").is_file()


@pytest.mark.asyncio
async def test_server_bounds_large_tool_results(monkeypatch):
    from llx.mcp import server as mcp_server

    async def large_result(_arguments):
        return {"value": "x" * 60_000}

    monkeypatch.setitem(mcp_server._TOOL_HANDLERS, "large_test_result", large_result)
    content = await mcp_server.call_tool("large_test_result", {})
    payload = json.loads(content[0].text)

    assert payload["truncated"] is True
    assert payload["original_chars"] > 50_000
