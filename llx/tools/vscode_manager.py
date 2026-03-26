"""
VS Code Manager for llx
Manages VS Code server with AI extensions and configurations.
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


class VSCodeManager:
    """Manages VS Code server with AI extensions."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docker_manager = DockerManager(project_root)
        self.container_name = "llx-vscode-dev"
        self.port = 8080
        self.password_env = "VSCODE_PASSWORD"
        
        # Essential extensions for AI development
        self.extensions = {
            "primary": [
                "roocode.roocode",                    # RooCode AI Assistant
                "ms-python.python",                   # Python support
                "ms-python.black-formatter",          # Python formatter
                "ms-python.flake8",                   # Python linting
                "ms-vscode.vscode-docker",            # Docker support
                "eamodio.gitlens",                    # Git supercharged
                "ms-vscode.vscode-json",              # JSON support
                "redhat.vscode-yaml",                 # YAML support
            ],
            "optional": [
                "continue.continue",                  # Continue.dev AI Assistant
                "codeium.codeium",                    # Codeium AI Autocomplete
                "tabnine.tabnine-vscode",             # TabNine AI Autocomplete
                "ms-python.mypy-type-checker",        # Python type checking
                "streetsidesoftware.code-spell-checker", # Spell checker
                "PKief.material-icon-theme",          # Material icons
                "zhuangtongfa.material-theme",        # Material theme
            ]
        }
    
    def is_vscode_running(self) -> bool:
        """Check if VS Code server is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=10
            )
            return self.container_name in result.stdout
        except:
            return False
    
    def start_vscode(self, wait_for_ready: bool = True) -> bool:
        """Start VS Code server."""
        try:
            print("📝 Starting VS Code server...")
            
            if not self.docker_manager.start_environment("dev", ["vscode"]):
                print("❌ Failed to start VS Code")
                return False
            
            if wait_for_ready:
                if self.wait_for_vscode_ready():
                    print("✅ VS Code server is ready!")
                    return True
                else:
                    print("❌ VS Code server failed to start properly")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting VS Code: {e}")
            return False
    
    def stop_vscode(self) -> bool:
        """Stop VS Code server."""
        try:
            print("🛑 Stopping VS Code server...")
            
            if self.docker_manager.stop_environment("dev", ["vscode"]):
                print("✅ VS Code server stopped!")
                return True
            else:
                print("❌ Failed to stop VS Code")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping VS Code: {e}")
            return False
    
    def restart_vscode(self) -> bool:
        """Restart VS Code server."""
        print("🔄 Restarting VS Code server...")
        
        if not self.stop_vscode():
            return False
        
        time.sleep(2)
        return self.start_vscode()
    
    def wait_for_vscode_ready(self, timeout: int = 30) -> bool:
        """Wait for VS Code server to be ready."""
        print("⏳ Waiting for VS Code server to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_vscode_health():
                print("✅ VS Code server is ready!")
                return True
            
            time.sleep(2)
        
        print("❌ Timeout waiting for VS Code server")
        return False
    
    def check_vscode_health(self) -> bool:
        """Check if VS Code server is healthy."""
        try:
            response = requests.get(f"http://localhost:{self.port}", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_vscode_url(self) -> str:
        """Get VS Code server URL."""
        return f"http://localhost:{self.port}"
    
    def get_vscode_password(self) -> str:
        """Get VS Code server password."""
        return os.getenv(self.password_env, "llx-dev")
    
    def install_extensions(self, extensions: List[str] = None) -> bool:
        """Install VS Code extensions."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        if not extensions:
            extensions = self.extensions["primary"]
        
        print(f"🔧 Installing {len(extensions)} extensions...")
        
        failed_extensions = []
        successful_extensions = []
        
        for extension in extensions:
            print(f"  🔧 Installing {extension}...")
            
            try:
                result = subprocess.run([
                    "docker", "exec", self.container_name,
                    "code", "--install-extension", extension, "--force"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    successful_extensions.append(extension)
                    print(f"    ✅ {extension}")
                else:
                    failed_extensions.append(extension)
                    print(f"    ❌ {extension}: {result.stderr.strip()}")
                    
            except subprocess.TimeoutExpired:
                failed_extensions.append(extension)
                print(f"    ❌ {extension}: Timeout")
            except Exception as e:
                failed_extensions.append(extension)
                print(f"    ❌ {extension}: {e}")
        
        print(f"\n📊 Installation Summary:")
        print(f"  ✅ Successful: {len(successful_extensions)}/{len(extensions)}")
        print(f"  ❌ Failed: {len(failed_extensions)}")
        
        if failed_extensions:
            print("\n❌ Failed extensions:")
            for ext in failed_extensions:
                print(f"  • {ext}")
        
        return len(failed_extensions) == 0
    
    def list_installed_extensions(self) -> List[str]:
        """List installed extensions."""
        if not self.is_vscode_running():
            return []
        
        try:
            result = subprocess.run([
                "docker", "exec", self.container_name,
                "code", "--list-extensions"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return [ext.strip() for ext in result.stdout.split('\n') if ext.strip()]
            
        except:
            pass
        
        return []
    
    def uninstall_extension(self, extension: str) -> bool:
        """Uninstall VS Code extension."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        try:
            result = subprocess.run([
                "docker", "exec", self.container_name,
                "code", "--uninstall-extension", extension
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print(f"✅ Uninstalled {extension}")
                return True
            else:
                print(f"❌ Failed to uninstall {extension}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error uninstalling extension: {e}")
            return False
    
    def update_extensions(self) -> bool:
        """Update all installed extensions."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        print("🔄 Updating VS Code extensions...")
        
        try:
            result = subprocess.run([
                "docker", "exec", self.container_name,
                "code", "--update-extensions"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Extensions updated successfully!")
                return True
            else:
                print(f"❌ Failed to update extensions: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating extensions: {e}")
            return False
    
    def get_vscode_logs(self, tail: int = 50) -> str:
        """Get VS Code server logs."""
        return self.docker_manager.get_service_logs("dev", "vscode", tail)
    
    def configure_roocode(self) -> bool:
        """Configure RooCode extension settings."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        # RooCode configuration
        roocode_config = {
            "roocode.enable": True,
            "roocode.autoStart": True,
            "roocode.defaultProvider": "openai-compatible",
            "roocode.model": "qwen2.5-coder:7b",
            "roocode.apiKey": "sk-proxy-local-dev",
            "roocode.apiBaseUrl": "http://localhost:4000/v1",
            "roocode.temperature": 0.2,
            "roocode.maxTokens": 4096,
            "roocode.stream": True,
            "roocode.contextLength": 32000,
            "roocode.chat.enabled": True,
            "roocode.chat.position": "right",
            "roocode.chat.size": "medium",
            "roocode.inline.enabled": True,
            "roocode.inline.triggerMode": "automatic",
            "roocode.codeActions.enabled": True,
            "roocode.shortcuts.chat": "ctrl+shift+r",
            "roocode.shortcuts.inline": "ctrl+shift+i",
            "roocode.shortcuts.explain": "ctrl+shift+e",
            "roocode.shortcuts.refactor": "ctrl+shift+f",
            "roocode.fallbackProvider": "ollama",
            "roocode.fallbackBaseUrl": "http://localhost:11434"
        }
        
        # Create settings file
        settings_path = "/home/coder/.local/share/code-server/User/settings.json"
        
        try:
            # Read existing settings
            result = subprocess.run([
                "docker", "exec", self.container_name,
                "cat", settings_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                try:
                    existing_settings = json.loads(result.stdout)
                except:
                    existing_settings = {}
            else:
                existing_settings = {}
            
            # Merge with RooCode settings
            existing_settings.update(roocode_config)
            
            # Write back settings
            settings_json = json.dumps(existing_settings, indent=2)
            
            # Create temporary file and copy to container
            temp_file = Path("/tmp/vscode_settings.json")
            temp_file.write_text(settings_json)
            
            subprocess.run([
                "docker", "cp", str(temp_file),
                f"{self.container_name}:{settings_path}"
            ])
            
            temp_file.unlink()
            
            print("✅ RooCode configuration updated!")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring RooCode: {e}")
            return False
    
    def create_workspace_tasks(self) -> bool:
        """Create VS Code tasks for llx development."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Start llx API",
                    "type": "shell",
                    "command": "python",
                    "args": ["-m", "llx", "proxy", "start", "--port", "4000"],
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "dedicated"
                    },
                    "problemMatcher": []
                },
                {
                    "label": "Test llx API",
                    "type": "shell",
                    "command": "curl",
                    "args": ["-s", "http://localhost:4000/v1/models"],
                    "group": "test",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "dedicated"
                    },
                    "problemMatcher": []
                },
                {
                    "label": "Check Ollama Models",
                    "type": "shell",
                    "command": "curl",
                    "args": ["-s", "http://localhost:11434/api/tags"],
                    "group": "test",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "dedicated"
                    },
                    "problemMatcher": []
                },
                {
                    "label": "Start AI Tools",
                    "type": "shell",
                    "command": "./ai-tools-manage.sh",
                    "args": ["start"],
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "dedicated"
                    },
                    "problemMatcher": []
                },
                {
                    "label": "Install Extensions",
                    "type": "shell",
                    "command": "python",
                    "args": ["-m", "llx.tools.vscode_manager", "install-extensions"],
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "dedicated"
                    },
                    "problemMatcher": []
                }
            ]
        }
        
        # Create tasks.json
        tasks_path = "/home/coder/project/.vscode/tasks.json"
        tasks_json = json.dumps(tasks, indent=2)
        
        try:
            # Create temporary file and copy to container
            temp_file = Path("/tmp/vscode_tasks.json")
            temp_file.write_text(tasks_json)
            
            subprocess.run([
                "docker", "cp", str(temp_file),
                f"{self.container_name}:{tasks_path}"
            ])
            
            temp_file.unlink()
            
            print("✅ VS Code tasks created!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating tasks: {e}")
            return False
    
    def create_launch_config(self) -> bool:
        """Create VS Code launch configurations."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        launch = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "justMyCode": True
                },
                {
                    "name": "llx API Debug",
                    "type": "python",
                    "request": "launch",
                    "program": "-m",
                    "args": ["llx", "proxy", "start", "--port", "4000"],
                    "console": "integratedTerminal",
                    "justMyCode": False,
                    "env": {
                        "DEBUG": "true",
                        "LOG_LEVEL": "DEBUG"
                    }
                },
                {
                    "name": "llx Tools Test",
                    "type": "python",
                    "request": "launch",
                    "program": "-m",
                    "args": ["llx.tools.health_checker", "test"],
                    "console": "integratedTerminal",
                    "justMyCode": False
                }
            ]
        }
        
        # Create launch.json
        launch_path = "/home/coder/project/.vscode/launch.json"
        launch_json = json.dumps(launch, indent=2)
        
        try:
            # Create temporary file and copy to container
            temp_file = Path("/tmp/vscode_launch.json")
            temp_file.write_text(launch_json)
            
            subprocess.run([
                "docker", "cp", str(temp_file),
                f"{self.container_name}:{launch_path}"
            ])
            
            temp_file.unlink()
            
            print("✅ VS Code launch configurations created!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating launch configurations: {e}")
            return False
    
    def backup_settings(self, backup_dir: str = None) -> bool:
        """Backup VS Code settings and extensions."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        if not backup_dir:
            backup_dir = self.project_root / "backups" / f"vscode-{int(time.time())}"
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        print(f"💾 Backing up VS Code to {backup_path}")
        
        # Backup settings
        settings_path = "/home/coder/.local/share/code-server/User/settings.json"
        try:
            subprocess.run([
                "docker", "cp", f"{self.container_name}:{settings_path}",
                str(backup_path / "settings.json")
            ])
            print("  ✅ Settings backed up")
        except:
            print("  ⚠️  Settings backup failed")
        
        # Backup extensions list
        extensions = self.list_installed_extensions()
        extensions_file = backup_path / "extensions.txt"
        extensions_file.write_text('\n'.join(extensions))
        print(f"  ✅ Extensions list backed up ({len(extensions)} extensions)")
        
        print(f"✅ Backup completed: {backup_path}")
        return True
    
    def restore_settings(self, backup_dir: str) -> bool:
        """Restore VS Code settings and extensions."""
        if not self.is_vscode_running():
            print("❌ VS Code server is not running")
            return False
        
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            print(f"❌ Backup directory not found: {backup_path}")
            return False
        
        print(f"📦 Restoring VS Code from {backup_path}")
        
        # Restore settings
        settings_file = backup_path / "settings.json"
        if settings_file.exists():
            try:
                subprocess.run([
                    "docker", "cp", str(settings_file),
                    f"{self.container_name}:/home/coder/.local/share/code-server/User/settings.json"
                ])
                print("  ✅ Settings restored")
            except:
                print("  ⚠️  Settings restore failed")
        
        # Restore extensions
        extensions_file = backup_path / "extensions.txt"
        if extensions_file.exists():
            extensions = extensions_file.read_text().strip().split('\n')
            extensions = [ext for ext in extensions if ext.strip()]
            
            print(f"🔧 Restoring {len(extensions)} extensions...")
            self.install_extensions(extensions)
        
        print("✅ Restore completed!")
        return True
    
    def get_status(self) -> Dict[str, any]:
        """Get VS Code status."""
        status = {
            "running": self.is_vscode_running(),
            "url": self.get_vscode_url() if self.is_vscode_running() else None,
            "password": self.get_vscode_password(),
            "healthy": False,
            "extensions": [],
            "roocode_installed": False
        }
        
        if status["running"]:
            status["healthy"] = self.check_vscode_health()
            status["extensions"] = self.list_installed_extensions()
            status["roocode_installed"] = "roocode.roocode" in status["extensions"]
        
        return status
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("📝 VS Code Status")
        print("=================")
        
        status = self.get_status()
        
        # Server status
        server_icon = "✅" if status["running"] else "❌"
        print(f"{server_icon} Server: {'Running' if status['running'] else 'Stopped'}")
        
        if status["running"]:
            # Health check
            health_icon = "✅" if status["healthy"] else "❌"
            print(f"{health_icon} Health: {'Healthy' if status['healthy'] else 'Unhealthy'}")
            
            # URL and password
            print(f"🌐 URL: {status['url']}")
            print(f"🔑 Password: {status['password']}")
            
            # Extensions
            print(f"📦 Extensions: {len(status['extensions'])} installed")
            
            # RooCode
            roocode_icon = "✅" if status["roocode_installed"] else "❌"
            print(f"{roocode_icon} RooCode: {'Installed' if status['roocode_installed'] else 'Not installed'}")
            
            # Key extensions
            key_extensions = ["roocode.roocode", "ms-python.python", "eamodio.gitlens"]
            print("\n🔧 Key Extensions:")
            for ext in key_extensions:
                ext_icon = "✅" if ext in status["extensions"] else "❌"
                ext_name = ext.split('.')[-1].replace('_', ' ').title()
                print(f"  {ext_icon} {ext_name}")
        
        print()
    
    def print_quick_start(self):
        """Print quick start guide."""
        print("🚀 VS Code Quick Start")
        print("=====================")
        print("")
        
        print("1️⃣ Start VS Code:")
        print("   ./docker-manage.sh dev")
        print("   # VS Code will start automatically")
        print("")
        
        print("2️⃣ Access VS Code:")
        print("   URL: http://localhost:8080")
        print("   Password: proxym-vscode (or your configured password)")
        print("")
        
        print("3️⃣ Install Extensions:")
        print("   # Extensions are auto-installed, but you can manually:")
        print("   python -m llx.tools.vscode_manager install-extensions")
        print("")
        
        print("4️⃣ Use RooCode:")
        print("   # In VS Code, use shortcuts:")
        print("   Ctrl+Shift+R  - Open RooCode chat")
        print("   Ctrl+Shift+I  - Toggle inline suggestions")
        print("   Ctrl+Shift+E  - Explain code")
        print("   Ctrl+Shift+F  - Refactor code")
        print("")
        
        print("5️⃣ VS Code Tasks:")
        print("   # Open Command Palette (Ctrl+Shift+P) and run:")
        print("   Tasks: Start llx API")
        print("   Tasks: Test llx API")
        print("   Tasks: Check Ollama Models")
        print("   Tasks: Start AI Tools")
        print("")
        
        print("🎯 Pro Tips:")
        print("   • Use Ctrl+Shift+P → Tasks to run llx commands")
        print("   • RooCode works with local Ollama models")
        print("   • All changes are synced to your local filesystem")
        print("   • Use Git integration for version control")
        print("   • Extensions are persisted across restarts")
        print()


# CLI interface

def _build_parser() -> "argparse.ArgumentParser":
    import argparse
    parser = argparse.ArgumentParser(description="llx VS Code Manager")
    parser.add_argument("command", choices=[
        "start", "stop", "restart", "status", "logs", "install-extensions",
        "list-extensions", "uninstall-extension", "update-extensions",
        "configure-roocode", "create-tasks", "create-launch",
        "backup", "restore", "quick-start"
    ])
    parser.add_argument("--extension", help="Specific extension")
    parser.add_argument("--backup-dir", help="Backup directory")
    parser.add_argument("--tail", type=int, default=50, help="Log tail lines")
    return parser


def _dispatch(args, manager: "VSCodeManager") -> bool:
    if args.command == "start":
        return manager.start_vscode()
    elif args.command == "stop":
        return manager.stop_vscode()
    elif args.command == "restart":
        return manager.restart_vscode()
    elif args.command == "status":
        manager.print_status_summary()
        return True
    elif args.command == "logs":
        logs = manager.get_vscode_logs(args.tail)
        print(logs)
        return True
    elif args.command == "install-extensions":
        return manager.install_extensions()
    elif args.command == "list-extensions":
        extensions = manager.list_installed_extensions()
        print(f"📦 Installed Extensions ({len(extensions)}):")
        for ext in extensions:
            print(f"  • {ext}")
        return True
    elif args.command == "uninstall-extension":
        if not args.extension:
            print("❌ --extension required for uninstall")
            return False
        return manager.uninstall_extension(args.extension)
    elif args.command == "update-extensions":
        return manager.update_extensions()
    elif args.command == "configure-roocode":
        return manager.configure_roocode()
    elif args.command == "create-tasks":
        return manager.create_workspace_tasks()
    elif args.command == "create-launch":
        return manager.create_launch_config()
    elif args.command == "backup":
        return manager.backup_settings(args.backup_dir)
    elif args.command == "restore":
        if not args.backup_dir:
            print("❌ --backup-dir required for restore")
            return False
        return manager.restore_settings(args.backup_dir)
    elif args.command == "quick-start":
        manager.print_quick_start()
        return True
    return False


def main():
    """CLI entry point for VS Code manager."""
    cli_main(_build_parser, _dispatch, VSCodeManager)


if __name__ == "__main__":
    main()
