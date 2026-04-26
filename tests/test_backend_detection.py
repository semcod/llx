"""Tests for backend detection system."""

import pytest
from unittest.mock import patch, MagicMock
from llx.planfile.executor_simple import (
    BackendType,
    _detect_available_backends,
    _select_best_backend,
)


class TestBackendDetection:
    """Test backend detection functionality."""

    def test_backend_type_constants(self):
        """Test that BackendType has all expected constants."""
        assert hasattr(BackendType, 'LOCAL')
        assert hasattr(BackendType, 'DOCKER')
        assert hasattr(BackendType, 'MCP')
        assert hasattr(BackendType, 'LLM_CHAT')
        assert BackendType.LOCAL == 'local'
        assert BackendType.DOCKER == 'docker'
        assert BackendType.MCP == 'mcp'
        assert BackendType.LLM_CHAT == 'llm_chat'

    @patch('llx.planfile.executor_simple.subprocess.run')
    def test_detect_local_aider_available(self, mock_run):
        """Test detection when local aider is available."""
        mock_run.return_value = MagicMock(returncode=0)
        
        backends = _detect_available_backends()
        
        assert backends[BackendType.LOCAL] == True
        assert backends[BackendType.LLM_CHAT] == True  # Always available

    @patch('llx.planfile.executor_simple.subprocess.run')
    def test_detect_local_aider_not_available(self, mock_run):
        """Test detection when local aider is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        backends = _detect_available_backends()
        
        assert backends[BackendType.LOCAL] == False
        assert backends[BackendType.LLM_CHAT] == True  # Always available

    @patch('llx.planfile.executor_simple.subprocess.run')
    def test_detect_docker_available(self, mock_run):
        """Test detection when Docker is available."""
        def side_effect(*args, **kwargs):
            if 'docker' in str(args[0]):
                return MagicMock(returncode=0)
            raise FileNotFoundError()
        
        mock_run.side_effect = side_effect
        
        backends = _detect_available_backends()
        
        assert backends[BackendType.DOCKER] == True
        assert backends[BackendType.LOCAL] == False

    @patch('llx.planfile.executor_simple.subprocess.run')
    def test_detect_docker_not_available(self, mock_run):
        """Test detection when Docker is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        backends = _detect_available_backends()
        
        assert backends[BackendType.DOCKER] == False

    @patch('llx.planfile.executor_simple.subprocess.run')
    def test_detect_mcp_available(self, mock_run):
        """Test detection when MCP is available."""
        def side_effect(*args, **kwargs):
            if 'llx' in str(args[0]) and 'mcp' in str(args[0]):
                return MagicMock(returncode=0)
            raise FileNotFoundError()
        
        mock_run.side_effect = side_effect
        
        backends = _detect_available_backends()
        
        assert backends[BackendType.MCP] == True

    @patch('llx.planfile.executor_simple.subprocess.run')
    def test_detect_mcp_not_available(self, mock_run):
        """Test detection when MCP is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        backends = _detect_available_backends()
        
        assert backends[BackendType.MCP] == False

    def test_select_best_backend_local_priority(self):
        """Test that local aider has highest priority."""
        backends = {
            BackendType.LOCAL: True,
            BackendType.DOCKER: True,
            BackendType.MCP: True,
            BackendType.LLM_CHAT: True,
        }
        
        selected = _select_best_backend(backends)
        
        assert selected == BackendType.LOCAL

    def test_select_best_backend_docker_priority(self):
        """Test that docker has second priority."""
        backends = {
            BackendType.LOCAL: False,
            BackendType.DOCKER: True,
            BackendType.MCP: True,
            BackendType.LLM_CHAT: True,
        }
        
        selected = _select_best_backend(backends)
        
        assert selected == BackendType.DOCKER

    def test_select_best_backend_llm_chat_fallback(self):
        """Test that LLM chat is fallback when others unavailable."""
        backends = {
            BackendType.LOCAL: False,
            BackendType.DOCKER: False,
            BackendType.MCP: False,
            BackendType.LLM_CHAT: True,
        }
        
        selected = _select_best_backend(backends)
        
        assert selected == BackendType.LLM_CHAT

    def test_select_best_backend_all_unavailable(self):
        """Test selection when only LLM chat is available."""
        backends = {
            BackendType.LOCAL: False,
            BackendType.DOCKER: False,
            BackendType.MCP: False,
            BackendType.LLM_CHAT: True,
        }
        
        selected = _select_best_backend(backends)
        
        assert selected == BackendType.LLM_CHAT


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
