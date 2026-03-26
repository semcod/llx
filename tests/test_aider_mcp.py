"""Unit tests for aider MCP tool."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from llx.mcp.tools import _handle_aider


class TestAiderTool:
    """Test cases for aider MCP tool."""
    
    @pytest.mark.asyncio
    async def test_aider_not_installed(self):
        """Test when aider is not installed."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = await _handle_aider({
                'prompt': 'Add type hints',
                'path': '.',
                'model': 'ollama/qwen2.5-coder:7b'
            })
            
            assert result['success'] is False
            assert 'Aider not found' in result['error']
    
    @pytest.mark.asyncio
    async def test_aider_success(self):
        """Test successful aider execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully added type hints"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            result = await _handle_aider({
                'prompt': 'Add type hints',
                'path': '.',
                'model': 'ollama/qwen2.5-coder:7b',
                'files': ['test.py']
            })
            
            assert result['success'] is True
            assert result['stdout'] == "Successfully added type hints"
            assert 'aider' in result['command']
    
    @pytest.mark.asyncio
    async def test_aider_timeout(self):
        """Test aider timeout."""
        import subprocess
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('cmd', 300)
            
            result = await _handle_aider({
                'prompt': 'Add type hints',
                'path': '.'
            })
            
            assert result['success'] is False
            assert 'timed out' in result['error']
    
    @pytest.mark.asyncio
    async def test_aider_with_files(self):
        """Test aider with specific files."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Modified files"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            await _handle_aider({
                'prompt': 'Refactor',
                'path': '.',
                'files': ['file1.py', 'file2.py']
            })
            
            # Check that files were passed to aider
            cmd = mock_run.call_args[0][0]
            assert 'file1.py' in cmd
            assert 'file2.py' in cmd
    
    def test_tool_definition(self):
        """Test that tool is properly defined."""
        from llx.mcp.tools import tool_aider
        
        assert tool_aider.definition.name == "aider"
        assert "pair programming" in tool_aider.definition.description.lower()
        assert "prompt" in tool_aider.definition.inputSchema["required"]
        assert "model" in tool_aider.definition.inputSchema["properties"]
        assert tool_aider.definition.inputSchema["properties"]["model"]["default"] == "ollama/qwen2.5-coder:7b"


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_aider_tool())
