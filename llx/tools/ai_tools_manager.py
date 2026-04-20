"""
AI Tools Manager for llx
Manages shell-based AI tools (Aider, Claude Code, Cursor) in Docker.
"""

import subprocess
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests
from .docker_manager import DockerManager
from ._utils import cli_main
from ._docker import is_container_running as _is_container_running, docker_exec, docker_cp


class AIToolsManager:
    """Manages AI tools container and operations."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docker_manager = DockerManager(project_root)
        self.container_name = "llx-ai-tools-dev"
        self.tools = {
            "aider": {
                "command": "aider-llx",
                "local_command": "aider-local",
                "description": "AI pair programming tool"
            },
            "claude": {
                "command": "claude-llx", 
                "local_command": "claude-local",
                "description": "Claude Code assistant"
            },
            "cursor": {
                "command": "cursor-llx",
                "local_command": "cursor-local", 
                "description": "Cursor AI assistant"
            }
        }
    
    def is_container_running(self) -> bool:
        """Check if AI tools container is running."""
        return _is_container_running(self.container_name)
    
    def _ensure_llx_api_running(self, wait_for_ready: bool) -> bool:
        """Ensure llx API is running."""
        if not self.docker_manager.check_service_health("llx-api"):
            print("🔧 Starting llx API first...")
            if not self.docker_manager.start_environment("dev", ["llx-api"]):
                print("❌ Failed to start llx API")
                return False
            
            if wait_for_ready:
                if not self.docker_manager.wait_for_service("llx-api", "dev"):
                    print("❌ llx API not ready")
                    return False
        return True
    
    def _start_ai_tools_container(self, wait_for_ready: bool) -> bool:
        """Start the AI tools container."""
        if not self.docker_manager.start_environment("dev", ["ai-tools"]):
            print("❌ Failed to start AI tools container")
            return False
        
        if wait_for_ready:
            print("⏳ Waiting for AI tools to be ready...")
            time.sleep(5)
        
        if self.is_container_running():
            print("✅ AI tools environment started!")
            return True
        else:
            print("❌ AI tools container failed to start")
            return False
    
    def start_ai_tools(self, wait_for_ready: bool = True) -> bool:
        """Start AI tools container."""
        try:
            print("🤖 Starting AI tools environment...")
            
            if not self._ensure_llx_api_running(wait_for_ready):
                return False
            
            return self._start_ai_tools_container(wait_for_ready)
            
        except Exception as e:
            print(f"❌ Error starting AI tools: {e}")
            return False
    
    def stop_ai_tools(self) -> bool:
        """Stop AI tools container."""
        try:
            print("🛑 Stopping AI tools environment...")
            
            if self.docker_manager.stop_environment("dev", ["ai-tools"]):
                print("✅ AI tools stopped!")
                return True
            else:
                print("❌ Failed to stop AI tools")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping AI tools: {e}")
            return False
    
    def restart_ai_tools(self) -> bool:
        """Restart AI tools container."""
        print("🔄 Restarting AI tools...")
        
        if not self.stop_ai_tools():
            return False
        
        time.sleep(2)
        return self.start_ai_tools()
    
    def _print_shell_help(self) -> None:
        """Print shell help information."""
        print("🤖 Entering AI tools environment...")
        print("")
        print("📋 Available commands:")
        for tool_name, tool_info in self.tools.items():
            print(f"  {tool_info['command']} - {tool_info['description']}")
            print(f"  {tool_info['local_command']} - {tool_info['description']} (local Ollama)")
        print("")
        print("🔧 Utility commands:")
        print("  ai-status - Check status")
        print("  ai-test - Test connectivity")
        print("  ai-chat model 'message' - Quick chat")
        print("  ai-help - Show help")
        print("")
        print("📁 Workspace: /workspace")
        print("📁 Examples: /workspace/ai-tools-examples")
        print("")
    
    def access_shell(self) -> bool:
        """Access AI tools shell."""
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            print("🚀 Start it first: ./ai-tools-manage.sh start")
            return False
        
        try:
            self._print_shell_help()
            
            # Use interactive shell
            docker_exec(self.container_name, ["/bin/bash"], interactive=True)
            
            return True
            
        except Exception as e:
            print(f"❌ Error accessing shell: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute command in AI tools container."""
        if not self.is_container_running():
            return False, "AI tools container is not running"
        
        try:
            result = docker_exec(
                self.container_name, ["/bin/bash", "-c", command], timeout=timeout
            )
            
            return result.returncode == 0, result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, f"Error executing command: {e}"
    
    def _get_service_statuses(self) -> Dict[str, bool]:
        services = {"llx-api": False, "ollama": False}
        services["llx-api"] = self.docker_manager.check_service_health("llx-api", "dev")

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            services["ollama"] = response.status_code == 200
        except:
            services["ollama"] = False

        return services

    def _get_tool_statuses(self) -> Dict[str, bool]:
        tools = {}
        for tool_name in self.tools.keys():
            success, _ = self.execute_command(f"command -v {tool_name}-llx", timeout=5)
            tools[tool_name] = success
        return tools

    def _get_workspace_status(self) -> Optional[str]:
        success, output = self.execute_command("pwd && ls -la", timeout=5)
        if not success:
            return None

        lines = output.strip().split('\n')
        return lines[0] if lines else None

    def get_status(self) -> Dict[str, any]:
        """Get AI tools status."""
        status = {
            "container_running": self.is_container_running(),
            "services": {},
            "tools": {},
            "workspace": None
        }
        
        if status["container_running"]:
            status["services"] = self._get_service_statuses()
            status["tools"] = self._get_tool_statuses()
            status["workspace"] = self._get_workspace_status()
        
        return status
    
    def _test_llx_api_connectivity(self) -> bool:
        """Test llx API connectivity."""
        try:
            response = requests.get("http://localhost:4000/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _test_ollama_connectivity(self) -> bool:
        """Test Ollama connectivity."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_connectivity(self) -> Dict[str, bool]:
        """Test AI tools connectivity."""
        results = {}
        
        if not self.is_container_running():
            return {"container": False}
        
        results["llx_api"] = self._test_llx_api_connectivity()
        results["ollama"] = self._test_ollama_connectivity()
        
        # Test tools in container (assuming incomplete, but keeping as is)
        return results
