"""Tests for MCP tool handlers."""

import runpy
import sys
import pytest
import asyncio
from unittest.mock import patch
import llx.mcp.server as mcp_server
from llx.cli.app import mcp_start
from llx.mcp.server import build_parser
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


class TestMcpServerCli:
    def test_mcp_start_sse_routes_to_sse_transport(self, monkeypatch, capsys):
        calls: list[list[str] | None] = []

        def fake_main(argv=None):
            calls.append(argv)
            return 0

        monkeypatch.setattr(mcp_server, "main", fake_main)

        mcp_start(mode="sse", port=8123)

        captured = capsys.readouterr()
        assert "SSE endpoint: http://localhost:8123/sse" in captured.out
        assert calls == [["--sse", "--port", "8123"]]

    def test_mcp_start_stdio_routes_to_stdio_transport(self, monkeypatch):
        calls: list[list[str] | None] = []

        def fake_main(argv=None):
            calls.append(argv)
            return 0

        monkeypatch.setattr(mcp_server, "main", fake_main)

        mcp_start(mode="stdio", port=8123)

        assert calls == [[]]

    def test_mcp_parser_defaults_align_with_sse_server(self):
        args = build_parser().parse_args([])

        assert args.sse is False
        assert args.host == "0.0.0.0"
        assert args.port == 8000


class TestMcpServerEntryPoint:
    def test_main_dispatches_to_sse_mode(self):
        from llx.mcp import server as mcp_server

        called = {}

        with patch.object(mcp_server, "run_sse_server", side_effect=lambda host, port: called.update({"host": host, "port": port})) as mock_sse, \
             patch.object(mcp_server.asyncio, "run") as mock_asyncio_run:
            rc = mcp_server.main(["--sse", "--host", "127.0.0.1", "--port", "8123"])

        assert rc == 0
        assert called == {"host": "127.0.0.1", "port": 8123}
        mock_sse.assert_called_once()
        mock_asyncio_run.assert_not_called()

    def test_main_defaults_to_stdio_mode(self):
        from llx.mcp import server as mcp_server

        def fake_asyncio_run(coro):
            coro.close()

        with patch.object(mcp_server, "run_sse_server") as mock_sse, \
             patch.object(mcp_server.asyncio, "run", side_effect=fake_asyncio_run) as mock_asyncio_run:
            rc = mcp_server.main([])

        assert rc == 0
        mock_sse.assert_not_called()
        mock_asyncio_run.assert_called_once()


class TestMcpPackageEntrypoint:
    def test_module_entrypoint_forwards_cli_args(self, monkeypatch):
        called = {}

        def fake_main_sync(argv=None):
            called["argv"] = argv
            return 0

        monkeypatch.setattr(mcp_server, "main_sync", fake_main_sync)
        monkeypatch.setattr(sys, "argv", ["llx.mcp", "--sse", "--port", "8123"])

        with pytest.raises(SystemExit) as exc:
            runpy.run_module("llx.mcp", run_name="__main__")

        assert exc.value.code == 0
        assert called["argv"] == ["--sse", "--port", "8123"]
