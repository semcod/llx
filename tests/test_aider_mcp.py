"""Unit tests for aider MCP tool."""

import pytest
from unittest.mock import patch, MagicMock

pytest.importorskip("mcp", reason="Aider MCP tests require llx[mcp] extras")

from llx.mcp.tools.code_edit import _handle_aider


async def _approved_args(args, monkeypatch):
    proposal = await _handle_aider({**args, "actor": "reviewer"})
    assert proposal["status"] == "approval_required"
    monkeypatch.setenv("LLX_MCP_ALLOW_WRITE", "1")
    return {
        **args,
        "apply": True,
        "actor": "reviewer",
        "approval_hash": proposal["approval_hash"],
    }


class TestAiderTool:
    """Test cases for aider MCP tool."""

    @pytest.mark.asyncio
    async def test_aider_not_installed(self, monkeypatch):
        """Test when aider is not installed."""
        args = await _approved_args(
            {"prompt": "Add type hints", "path": ".", "model": "ollama/qwen2.5-coder:7b"},
            monkeypatch,
        )
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("aider not found")
            result = await _handle_aider(args)

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_aider_success(self, monkeypatch):
        """Test successful aider execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully added type hints"
        mock_result.stderr = ""

        args = await _approved_args(
            {
                "prompt": "Add type hints",
                "path": ".",
                "model": "ollama/qwen2.5-coder:7b",
                "files": ["test.py"],
            },
            monkeypatch,
        )
        with patch("subprocess.run", return_value=mock_result):
            result = await _handle_aider(args)

            assert result["success"] is True
            assert result["stdout"] == "Successfully added type hints"
            assert "aider" in result["command"]

    @pytest.mark.asyncio
    async def test_aider_timeout(self, monkeypatch):
        """Test aider timeout."""
        import subprocess

        args = await _approved_args({"prompt": "Add type hints", "path": "."}, monkeypatch)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)
            result = await _handle_aider(args)

            assert result["success"] is False
            assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_aider_with_files(self, monkeypatch):
        """Test aider with specific files."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Modified files"
        mock_result.stderr = ""

        args = await _approved_args(
            {"prompt": "Refactor", "path": ".", "files": ["file1.py", "file2.py"]},
            monkeypatch,
        )
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            await _handle_aider(args)

            # Check that files were passed to aider
            cmd = mock_run.call_args[0][0]
            assert any(item.endswith("file1.py") for item in cmd)
            assert any(item.endswith("file2.py") for item in cmd)

    @pytest.mark.asyncio
    async def test_aider_is_safe_by_default_and_binds_prompt(self, monkeypatch):
        args = {"prompt": "Refactor safely", "path": ".", "actor": "reviewer"}
        with patch("subprocess.run") as mock_run:
            proposal = await _handle_aider(args)
        mock_run.assert_not_called()
        assert proposal["status"] == "approval_required"

        monkeypatch.setenv("LLX_MCP_ALLOW_WRITE", "1")
        changed = await _handle_aider(
            {
                **args,
                "prompt": "Different prompt",
                "apply": True,
                "approval_hash": proposal["approval_hash"],
            }
        )
        assert changed["status"] == "approval_required"
        assert changed["approval_hash"] != proposal["approval_hash"]

    def test_tool_definition(self):
        """Test that tool is properly defined."""
        from llx.mcp.tools.code_edit import tool_aider

        assert tool_aider.definition.name == "aider"
        assert "pair programming" in tool_aider.definition.description.lower()
        assert "prompt" in tool_aider.definition.inputSchema["required"]
        assert "model" in tool_aider.definition.inputSchema["properties"]
        assert tool_aider.definition.inputSchema["properties"]["apply"]["default"] is False
        assert (
            tool_aider.definition.inputSchema["properties"]["model"]["default"]
            == "ollama/qwen2.5-coder:7b"
        )
