"""
AI Tools Manager for llx
Manages shell-based AI tools (Aider, Claude Code, Cursor) in Docker.
"""

import os
import sys
import subprocess
import json
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
    
    def start_ai_tools(self, wait_for_ready: bool = True) -> bool:
        """Start AI tools container."""
        try:
            print("🤖 Starting AI tools environment...")
            
            # Start llx-api first if not running
            if not self.docker_manager.check_service_health("llx-api"):
                print("🔧 Starting llx API first...")
                if not self.docker_manager.start_environment("dev", ["llx-api"]):
                    print("❌ Failed to start llx API")
                    return False
                
                if wait_for_ready:
                    if not self.docker_manager.wait_for_service("llx-api", "dev"):
                        print("❌ llx API not ready")
                        return False
            
            # Start AI tools container
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
    
    def access_shell(self) -> bool:
        """Access AI tools shell."""
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            print("🚀 Start it first: ./ai-tools-manage.sh start")
            return False
        
        try:
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
    
    def test_connectivity(self) -> Dict[str, bool]:
        """Test AI tools connectivity."""
        results = {}
        
        if not self.is_container_running():
            return {"container": False}
        
        # Test llx API
        try:
            response = requests.get("http://localhost:4000/v1/models", timeout=5)
            results["llx_api"] = response.status_code == 200
        except:
            results["llx_api"] = False
        
        # Test Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            results["ollama"] = response.status_code == 200
        except:
            results["ollama"] = False
        
        # Test tools in container
        for tool_name in self.tools.keys():
            success, _ = self.execute_command(f"python -c 'import {tool_name}'", timeout=10)
            results[f"{tool_name}_package"] = success
            
            success, _ = self.execute_command(f"command -v {tool_name}-llx", timeout=5)
            results[f"{tool_name}_wrapper"] = success
        
        return results
    
    def run_chat_test(self, model: str = "qwen2.5-coder:7b", message: str = "Hello! Write a simple Python function.") -> bool:
        """Run chat completion test."""
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            return False
        
        command = f'ai-chat "{model}" "{message}"'
        success, output = self.execute_command(command, timeout=30)
        
        if success:
            print("✅ Chat test successful!")
            print("Response:")
            print(output[:500] + "..." if len(output) > 500 else output)
        else:
            print("❌ Chat test failed")
            print("Error:", output)
        
        return success
    
    def get_available_models(self) -> List[str]:
        """Get available models."""
        models = []
        
        # Get Ollama models
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models.extend([model["name"] for model in data.get("models", [])])
        except:
            pass
        
        # Get llx API models
        try:
            response = requests.get("http://localhost:4000/v1/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                llx_models = [model["id"] for model in data.get("data", [])]
                # Add llx models if not already present
                for model in llx_models:
                    if model not in models:
                        models.append(model)
        except:
            pass
        
        return models
    
    def install_tool(self, tool_name: str) -> bool:
        """Install specific AI tool."""
        if tool_name not in self.tools:
            print(f"❌ Unknown tool: {tool_name}")
            return False
        
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            return False
        
        print(f"🔧 Installing {tool_name}...")
        
        install_commands = {
            "aider": "pip install aider-chat",
            "claude": "pip install claude-code",
            "cursor": "pip install cursor-cli"
        }
        
        command = install_commands.get(tool_name, f"pip install {tool_name}")
        success, output = self.execute_command(command, timeout=60)
        
        if success:
            print(f"✅ {tool_name} installed successfully!")
        else:
            print(f"❌ Failed to install {tool_name}")
            print("Error:", output)
        
        return success
    
    def update_tools(self) -> bool:
        """Update all AI tools."""
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            return False
        
        print("🔄 Updating AI tools...")
        
        update_command = """
        pip install --upgrade aider-chat claude-code cursor-cli 2>/dev/null || echo "Some packages may not be available"
        """
        
        success, output = self.execute_command(update_command, timeout=120)
        
        if success:
            print("✅ AI tools updated successfully!")
        else:
            print("⚠️  Update completed with some issues:")
            print(output)
        
        return success
    
    def get_logs(self, tail: int = 50) -> str:
        """Get AI tools container logs."""
        return self.docker_manager.get_service_logs("dev", "ai-tools", tail)
    
    def create_workspace_example(self, project_name: str = "ai-project") -> bool:
        """Create example workspace for AI tools."""
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            return False
        
        print(f"📁 Creating example workspace: {project_name}")
        
        commands = [
            f"mkdir -p /workspace/{project_name}",
            f"cd /workspace/{project_name}",
            "git init",
            "echo '# AI Tools Example Project' > README.md",
            "echo 'print(\"Hello, AI!\")' > main.py",
            "git add .",
            "git commit -m 'Initial commit' || true"
        ]
        
        for command in commands:
            success, output = self.execute_command(command, timeout=10)
            if not success:
                print(f"❌ Failed to execute: {command}")
                return False
        
        print(f"✅ Example workspace created: /workspace/{project_name}")
        print("🚀 Use it to test AI tools:")
        print(f"  cd /workspace/{project_name}")
        print("  aider-llx")
        
        return True
    
    def backup_configurations(self, backup_dir: str = None) -> bool:
        """Backup AI tools configurations."""
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            return False
        
        if not backup_dir:
            backup_dir = self.project_root / "backups" / f"ai-tools-{int(time.time())}"
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        print(f"💾 Backing up AI tools configurations to {backup_path}")
        
        # Backup configurations
        configs = [
            ("/root/.config/aider", "aider-config"),
            ("/root/.config/claude-code", "claude-config"),
            ("/root/.config/cursor", "cursor-config"),
            ("/root/.ai-tools-config", "ai-tools-config")
        ]
        
        for config_path, backup_name in configs:
            success, _ = self.execute_command(f"tar -czf /tmp/{backup_name}.tar {config_path} 2>/dev/null || true", timeout=10)
            if success:
                # Copy backup from container
                docker_cp(
                    f"{self.container_name}:/tmp/{backup_name}.tar",
                    str(backup_path / f"{backup_name}.tar")
                )
                print(f"  ✅ Backed up {backup_name}")
        
        print(f"✅ Backup completed: {backup_path}")
        return True
    
    def restore_configurations(self, backup_dir: str) -> bool:
        """Restore AI tools configurations."""
        if not self.is_container_running():
            print("❌ AI tools container is not running")
            return False
        
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            print(f"❌ Backup directory not found: {backup_path}")
            return False
        
        print(f"📦 Restoring AI tools configurations from {backup_path}")
        
        # Copy backups to container
        for backup_file in backup_path.glob("*.tar"):
            docker_cp(str(backup_file), f"{self.container_name}:/tmp/")
            
            # Restore in container
            filename = backup_file.name
            success, _ = self.execute_command(f"cd / && tar -xzf /tmp/{filename} 2>/dev/null || true", timeout=10)
            
            if success:
                print(f"  ✅ Restored {filename}")
        
        print("✅ Configurations restored!")
        return True
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🤖 AI Tools Status")
        print("==================")
        
        status = self.get_status()
        
        # Container status
        container_icon = "✅" if status["container_running"] else "❌"
        print(f"{container_icon} Container: {'Running' if status['container_running'] else 'Stopped'}")
        
        if status["container_running"]:
            # Services status
            print("\n🔍 Services:")
            for service, is_healthy in status["services"].items():
                service_icon = "✅" if is_healthy else "❌"
                print(f"  {service_icon} {service}: {'Healthy' if is_healthy else 'Unhealthy'}")
            
            # Tools status
            print("\n🛠️  Tools:")
            for tool, is_available in status["tools"].items():
                tool_icon = "✅" if is_available else "❌"
                tool_info = self.tools.get(tool, {})
                print(f"  {tool_icon} {tool}: {tool_info.get('description', 'Unknown')}")
            
            # Workspace
            if status["workspace"]:
                print(f"\n📁 Workspace: {status['workspace']}")
            
            # Available models
            models = self.get_available_models()
            print(f"\n📦 Available Models: {len(models)}")
            for model in models[:5]:
                print(f"  • {model}")
            if len(models) > 5:
                print(f"  ... and {len(models) - 5} more")
        
        print()
    
    def print_usage_examples(self):
        """Print usage examples."""
        print("📚 AI Tools Usage Examples")
        print("==========================")
        print("")
        
        print("🚀 Quick Start:")
        print("  ./ai-tools-manage.sh start      # Start AI tools")
        print("  ./ai-tools-manage.sh shell     # Access shell")
        print("")
        
        print("🤖 In AI Tools Shell:")
        for tool_name, tool_info in self.tools.items():
            print(f"  {tool_info['command']}      # {tool_info['description']}")
            print(f"  {tool_info['local_command']}  # {tool_info['description']} (local)")
        print("")
        
        print("🔧 Utility Commands:")
        print("  ai-status                      # Check status")
        print("  ai-test                        # Test connectivity")
        print("  ai-chat model 'message'        # Quick chat")
        print("  ai-help                        # Show help")
        print("")
        
        print("📁 File Operations:")
        for tool_name in self.tools.keys():
            tool_info = self.tools[tool_name]
            print(f"  {tool_info['command']} file.py    # Edit specific file")
        print("")
        
        print("🔗 Integration with Git:")
        print("  git init && aider-llx           # Start Aider in new repo")
        print("  claude-llx --commit            # Auto-commit changes")
        print("  cursor-llx --diff              # Review changes")
        print("")
        
        print("🎯 Examples:")
        print("  aider-llx --message 'Add type hints' file.py")
        print("  claude-llx --task 'Refactor function' file.py")
        print("  cursor-llx --prompt 'Optimize code' file.py")


# CLI interface - Command handlers registry to reduce CC from 21

import argparse
from typing import Callable, Dict

CmdHandler = Callable[[argparse.Namespace, "AIToolsManager"], bool]


def _cmd_start(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.start_ai_tools()


def _cmd_stop(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.stop_ai_tools()


def _cmd_restart(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.restart_ai_tools()


def _cmd_shell(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.access_shell()


def _cmd_status(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    manager.print_status_summary()
    return True


def _cmd_logs(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    logs = manager.get_logs(args.tail)
    print(logs)
    return True


def _cmd_test(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    results = manager.test_connectivity()
    print("🧪 Connectivity Test Results:")
    for test, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {test}")
    return all(results.values())


def _cmd_chat(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.run_chat_test(args.model, args.message)


def _cmd_models(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    models = manager.get_available_models()
    print(f"📦 Available Models ({len(models)}):")
    for model in models:
        print(f"  • {model}")
    return True


def _cmd_install(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    if not args.tool:
        print("❌ --tool required for install")
        return False
    return manager.install_tool(args.tool)


def _cmd_update(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.update_tools()


def _cmd_backup(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.backup_configurations(args.backup_dir)


def _cmd_restore(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    if not args.backup_dir:
        print("❌ --backup-dir required for restore")
        return False
    return manager.restore_configurations(args.backup_dir)


def _cmd_workspace(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    return manager.create_workspace_example(args.project)


def _cmd_examples(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    manager.print_usage_examples()
    return True


# Command registry: maps command names to handler functions
_COMMAND_HANDLERS: Dict[str, CmdHandler] = {
    "start": _cmd_start,
    "stop": _cmd_stop,
    "restart": _cmd_restart,
    "shell": _cmd_shell,
    "status": _cmd_status,
    "logs": _cmd_logs,
    "test": _cmd_test,
    "chat": _cmd_chat,
    "models": _cmd_models,
    "install": _cmd_install,
    "update": _cmd_update,
    "backup": _cmd_backup,
    "restore": _cmd_restore,
    "workspace": _cmd_workspace,
    "examples": _cmd_examples,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx AI Tools Manager")
    parser.add_argument("command", choices=list(_COMMAND_HANDLERS.keys()))
    parser.add_argument("--tool", help="Specific tool")
    parser.add_argument("--model", default="qwen2.5-coder:7b", help="Model for chat")
    parser.add_argument("--message", default="Hello! Write a simple Python function.", help="Chat message")
    parser.add_argument("--project", default="ai-project", help="Project name for workspace")
    parser.add_argument("--backup-dir", help="Backup directory")
    parser.add_argument("--tail", type=int, default=50, help="Log tail lines")
    return parser


def _dispatch(args: argparse.Namespace, manager: "AIToolsManager") -> bool:
    """Dispatch command to appropriate handler using registry pattern.

    CC reduced from 21 to ~3 by using handler registry instead of if-elif chain.
    """
    handler = _COMMAND_HANDLERS.get(args.command)
    if handler:
        return handler(args, manager)
    return False


def main():
    """CLI entry point for AI tools manager."""
    cli_main(_build_parser, _dispatch, AIToolsManager)


if __name__ == "__main__":
    main()
