"""Tests for MCP tool handlers."""

import pytest
import asyncio
from llx.mcp.tools import (
    _handle_llx_analyze,
    _handle_llx_select,
    _handle_llx_proxy_status,
)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestMcpAnalyze:
    def test_analyze_returns_metrics(self, event_loop, tmp_path):
        # Create minimal Python file
        (tmp_path / "main.py").write_text("def hello():\n    pass\n")
        result = event_loop.run_until_complete(
            _handle_llx_analyze({"path": str(tmp_path)})
        )
        assert "metrics" in result
        assert "selection" in result
        assert result["metrics"]["total_files"] >= 1

    def test_analyze_with_task_hint(self, event_loop, tmp_path):
        (tmp_path / "main.py").write_text("x = 1\n")
        result = event_loop.run_until_complete(
            _handle_llx_analyze({"path": str(tmp_path), "task": "quick_fix"})
        )
        assert result["selection"]["tier"] == "free"


class TestMcpSelect:
    def test_select_returns_tier(self, event_loop, tmp_path):
        (tmp_path / "main.py").write_text("pass\n")
        result = event_loop.run_until_complete(
            _handle_llx_select({"path": str(tmp_path)})
        )
        assert "tier" in result
        assert "model_id" in result


class TestMcpProxyStatus:
    def test_proxy_not_running(self, event_loop):
        result = event_loop.run_until_complete(
            _handle_llx_proxy_status({"url": "http://localhost:19999"})
        )
        assert result["running"] is False
