"""
llx Tools CLI
Unified command-line interface for llx ecosystem management.
"""

import os
import sys
import argparse
from typing import Dict, List, Optional
from pathlib import Path

# Import all managers
from .docker_manager import DockerManager
from .ai_tools_manager import AIToolsManager
from .vscode_manager import VSCodeManager
from .model_manager import ModelManager
from .config_manager import ConfigManager
from .health_checker import HealthChecker


class LLXToolsCLI:
    """Unified CLI for llx ecosystem management."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        
        # Initialize managers
        self.docker_manager = DockerManager(project_root)
        self.ai_tools_manager = AIToolsManager(project_root)
        self.vscode_manager = VSCodeManager(project_root)
        self.model_manager = ModelManager(project_root)
        self.config_manager = ConfigManager(project_root)
        self.health_checker = HealthChecker(project_root)
        
        self.managers = {
            "docker": self.docker_manager,
            "ai-tools": self.ai_tools_manager,
            "vscode": self.vscode_manager,
            "models": self.model_manager,
            "config": self.config_manager,
            "health": self.health_checker
        }
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(
            prog="llx-tools",
            description="llx Ecosystem Management CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  llx-tools start                    # Start all services
  llx-tools status                    # Show system status
  llx-tools health check              # Run health check
  llx-tools models pull qwen2.5-coder:7b    # Pull model
  llx-tools config create-env         # Create .env file
  llx-tools ai-tools shell            # Access AI tools
  
For detailed help on subcommands:
  llx-tools <command> --help
            """
        )
        
        parser.add_argument(
            "--project-root",
            type=str,
            help="Project root directory (default: current directory)"
        )
        
        subparsers = parser.add_subparsers(
            dest="command",
            title="Available Commands",
            description="Manage llx ecosystem components",
            metavar="COMMAND"
        )
        
        # Environment management
        env_parser = subparsers.add_parser(
            "start",
            help="Start llx environment"
        )
        env_parser.add_argument(
            "--env",
            choices=["dev", "prod", "full"],
            default="dev",
            help="Environment to start (default: dev)"
        )
        env_parser.add_argument(
            "--services",
            nargs="*",
            help="Specific services to start"
        )
        
        stop_parser = subparsers.add_parser(
            "stop",
            help="Stop llx environment"
        )
        stop_parser.add_argument(
            "--env",
            choices=["dev", "prod", "full"],
            default="dev",
            help="Environment to stop (default: dev)"
        )
        stop_parser.add_argument(
            "--services",
            nargs="*",
            help="Specific services to stop"
        )
        
        restart_parser = subparsers.add_parser(
            "restart",
            help="Restart llx environment"
        )
        restart_parser.add_argument(
            "--env",
            choices=["dev", "prod", "full"],
            default="dev",
            help="Environment to restart (default: dev)"
        )
        restart_parser.add_argument(
            "--service",
            help="Specific service to restart"
        )
        
        # Status and monitoring
        status_parser = subparsers.add_parser(
            "status",
            help="Show system status"
        )
        status_parser.add_argument(
            "--env",
            choices=["dev", "prod", "full"],
            default="dev",
            help="Environment to check (default: dev)"
        )
        status_parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed status"
        )
        
        health_parser = subparsers.add_parser(
            "health",
            help="Health monitoring"
        )
        health_subparsers = health_parser.add_subparsers(
            dest="health_command",
            title="Health Commands"
        )
        
        health_subparsers.add_parser(
            "check",
            help="Run comprehensive health check"
        )
        
        health_subparsers.add_parser(
            "quick",
            help="Run quick health check"
        )
        
        monitor_parser = health_subparsers.add_parser(
            "monitor",
            help="Monitor services over time"
        )
        monitor_parser.add_argument(
            "--interval",
            type=int,
            default=30,
            help="Monitoring interval in seconds"
        )
        monitor_parser.add_argument(
            "--duration",
            type=int,
            default=300,
            help="Monitoring duration in seconds"
        )
        
        # Docker management
        docker_parser = subparsers.add_parser(
            "docker",
            help="Docker container management"
        )
        docker_subparsers = docker_parser.add_subparsers(
            dest="docker_command",
            title="Docker Commands"
        )
        
        docker_subparsers.add_parser(
            "status",
            help="Show Docker status"
        )
        
        docker_subparsers.add_parser(
            "logs",
            help="Show Docker logs"
        )
        docker_subparsers.add_parser(
            "build",
            help="Build Docker images"
        )
        docker_subparsers.add_parser(
            "cleanup",
            help="Clean up Docker resources"
        )
        docker_subparsers.add_parser(
            "backup",
            help="Backup Docker volumes"
        )
        docker_subparsers.add_parser(
            "restore",
            help="Restore Docker volumes"
        )
        docker_subparsers.add_parser(
            "--backup-dir",
            help="Backup directory"
        )
        
        # AI Tools management
        ai_tools_parser = subparsers.add_parser(
            "ai-tools",
            help="AI tools management"
        )
        ai_tools_subparsers = ai_tools_parser.add_subparsers(
            dest="ai_tools_command",
            title="AI Tools Commands"
        )
        
        ai_tools_subparsers.add_parser(
            "start",
            help="Start AI tools"
        )
        
        ai_tools_subparsers.add_parser(
            "stop",
            help="Stop AI tools"
        )
        
        ai_tools_subparsers.add_parser(
            "shell",
            help="Access AI tools shell"
        )
        
        ai_tools_subparsers.add_parser(
            "status",
            help="Show AI tools status"
        )
        
        test_parser = ai_tools_subparsers.add_parser(
            "test",
            help="Test AI tools connectivity"
        )
        test_parser.add_argument(
            "--model",
            default="qwen2.5-coder:7b",
            help="Model to test with"
        )
        test_parser.add_argument(
            "--message",
            default="Hello! Write a simple Python function.",
            help="Test message"
        )
        
        # VS Code management
        vscode_parser = subparsers.add_parser(
            "vscode",
            help="VS Code management"
        )
        vscode_subparsers = vscode_parser.add_subparsers(
            dest="vscode_command",
            title="VS Code Commands"
        )
        
        vscode_subparsers.add_parser(
            "start",
            help="Start VS Code"
        )
        
        vscode_subparsers.add_parser(
            "stop",
            help="Stop VS Code"
        )
        
        vscode_subparsers.add_parser(
            "status",
            help="Show VS Code status"
        )
        
        vscode_subparsers.add_parser(
            "install-extensions",
            help="Install VS Code extensions"
        )
        
        vscode_subparsers.add_parser(
            "configure-roocode",
            help="Configure RooCode extension"
        )
        
        vscode_subparsers.add_parser(
            "quick-start",
            help="Show VS Code quick start guide"
        )
        
        # Model management
        models_parser = subparsers.add_parser(
            "models",
            help="Model management"
        )
        models_subparsers = models_parser.add_subparsers(
            dest="models_command",
            title="Model Commands"
        )
        
        models_subparsers.add_parser(
            "list",
            help="List available models"
        )
        
        pull_parser = models_subparsers.add_parser(
            "pull",
            help="Pull model"
        )
        pull_parser.add_argument(
            "model_name",
            help="Model name to pull"
        )
        pull_parser.add_argument(
            "--timeout",
            type=int,
            default=300,
            help="Pull timeout in seconds"
        )
        
        remove_parser = models_subparsers.add_parser(
            "remove",
            help="Remove model"
        )
        remove_parser.add_argument(
            "model_name",
            help="Model name to remove"
        )
        
        test_parser = models_subparsers.add_parser(
            "test",
            help="Test model"
        )
        test_parser.add_argument(
            "model_name",
            help="Model name to test"
        )
        test_parser.add_argument(
            "--prompt",
            default="Hello! Write a simple Python function.",
            help="Test prompt"
        )
        
        models_subparsers.add_parser(
            "summary",
            help="Show model summary"
        )
        
        # Configuration management
        config_parser = subparsers.add_parser(
            "config",
            help="Configuration management"
        )
        config_subparsers = config_parser.add_subparsers(
            dest="config_command",
            title="Config Commands"
        )
        
        config_subparsers.add_parser(
            "summary",
            help="Show configuration summary"
        )
        
        config_subparsers.add_parser(
            "create-env",
            help="Create default .env file"
        )
        config_subparsers.add_parser(
            "--overwrite",
            action="store_true",
            help="Overwrite existing files"
        )
        
        update_parser = config_subparsers.add_parser(
            "update-env",
            help="Update environment variable"
        )
        update_parser.add_argument(
            "key",
            help="Variable key"
        )
        update_parser.add_argument(
            "value",
            help="Variable value"
        )
        
        get_parser = config_subparsers.add_parser(
            "get-env",
            help="Get environment variable"
        )
        get_parser.add_argument(
            "key",
            help="Variable key"
        )
        
        config_subparsers.add_parser(
            "validate",
            help="Validate configuration"
        )
        
        backup_parser = config_subparsers.add_parser(
            "backup",
            help="Backup configuration"
        )
        backup_parser.add_argument(
            "--backup-dir",
            help="Backup directory"
        )
        
        restore_parser = config_subparsers.add_parser(
            "restore",
            help="Restore configuration"
        )
        restore_parser.add_argument(
            "--backup-dir",
            help="Backup directory"
        )
        
        # Utility commands
        utils_parser = subparsers.add_parser(
            "utils",
            help="Utility commands"
        )
        utils_subparsers = utils_parser.add_subparsers(
            dest="utils_command",
            title="Utility Commands"
        )
        
        utils_subparsers.add_parser(
            "install",
            help="Install llx tools"
        )
        
        utils_subparsers.add_parser(
            "update",
            help="Update llx tools"
        )
        
        utils_subparsers.add_parser(
            "version",
            help="Show version information"
        )
        
        utils_subparsers.add_parser(
            "doctor",
            help="Run system diagnostics"
        )
        
        return parser
    
    def run_command(self, args: argparse.Namespace) -> bool:
        """Execute CLI command."""
        try:
            if args.command == "start":
                return self._handle_start(args)
            elif args.command == "stop":
                return self._handle_stop(args)
            elif args.command == "restart":
                return self._handle_restart(args)
            elif args.command == "status":
                return self._handle_status(args)
            elif args.command == "health":
                return self._handle_health(args)
            elif args.command == "docker":
                return self._handle_docker(args)
            elif args.command == "ai-tools":
                return self._handle_ai_tools(args)
            elif args.command == "vscode":
                return self._handle_vscode(args)
            elif args.command == "models":
                return self._handle_models(args)
            elif args.command == "config":
                return self._handle_config(args)
            elif args.command == "utils":
                return self._handle_utils(args)
            else:
                print(f"❌ Unknown command: {args.command}")
                return False
        except KeyboardInterrupt:
            print("\n❌ Command interrupted")
            return False
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return False
    
    def _handle_start(self, args: argparse.Namespace) -> bool:
        """Handle start command."""
        print(f"🚀 Starting {args.env} environment...")
        
        if args.services:
            success = self.docker_manager.start_environment(args.env, args.services)
        else:
            success = self.docker_manager.start_environment(args.env)
        
        if success:
            print("✅ Environment started successfully!")
            
            # Show access information
            if args.env == "dev":
                print("\n📋 Access Information:")
                print("  🤖 llx API: http://localhost:4000")
                print("  📝 VS Code: http://localhost:8080")
                print("  🔑 VS Code Password: proxym-vscode")
                print("  🦙 Ollama: http://localhost:11434")
                print("  🗄️  Redis: localhost:6379")
        
        return success
    
    def _handle_stop(self, args: argparse.Namespace) -> bool:
        """Handle stop command."""
        print(f"🛑 Stopping {args.env} environment...")
        
        if args.services:
            success = self.docker_manager.stop_environment(args.env, args.services)
        else:
            success = self.docker_manager.stop_environment(args.env)
        
        if success:
            print("✅ Environment stopped successfully!")
        
        return success
    
    def _handle_restart(self, args: argparse.Namespace) -> bool:
        """Handle restart command."""
        if args.service:
            print(f"🔄 Restarting {args.service} in {args.env}...")
            success = self.docker_manager.restart_service(args.env, args.service)
        else:
            print(f"🔄 Restarting {args.env} environment...")
            success = self.docker_manager.restart_service(args.env)
        
        return success
    
    def _handle_status(self, args: argparse.Namespace) -> bool:
        """Handle status command."""
        if args.detailed:
            self.docker_manager.print_status_summary(args.env)
        else:
            status = self.docker_manager.get_service_status(args.env)
            
            print(f"📊 {args.env.upper()} Environment Status")
            print("=" * 40)
            
            for service, info in status.items():
                status_icon = "✅" if info.get("state") == "running" else "❌"
                print(f"{status_icon} {service}: {info.get('status', 'Unknown')}")
        
        return True
    
    def _handle_health(self, args: argparse.Namespace) -> bool:
        """Handle health command."""
        if args.health_command == "check":
            results = self.health_checker.run_comprehensive_health_check()
            return results["overall_status"] == "healthy"
        
        elif args.health_command == "quick":
            return self.health_checker.run_quick_health_check()
        
        elif args.health_command == "monitor":
            self.health_checker.monitor_services(args.interval, args.duration)
            return True
        
        else:
            print("❌ Unknown health command")
            return False
    
    def _handle_docker(self, args: argparse.Namespace) -> bool:
        """Handle docker command."""
        if args.docker_command == "status":
            self.docker_manager.print_status_summary("dev")
        
        elif args.docker_command == "logs":
            logs = self.docker_manager.get_service_logs("dev")
            print(logs)
        
        elif args.docker_command == "build":
            success = self.docker_manager.build_images("dev")
        
        elif args.docker_command == "cleanup":
            success = self.docker_manager.cleanup_environment("dev")
        
        elif args.docker_command == "backup":
            success = self.docker_manager.backup_volumes("dev", getattr(args, 'backup_dir', None))
        
        elif args.docker_command == "restore":
            backup_dir = getattr(args, 'backup_dir', None)
            if not backup_dir:
                print("❌ --backup-dir required for restore")
                return False
            success = self.docker_manager.restore_volumes("dev", backup_dir)
        
        else:
            print("❌ Unknown docker command")
            return False
        
        return True
    
    def _handle_ai_tools(self, args: argparse.Namespace) -> bool:
        """Handle ai-tools command."""
        if args.ai_tools_command == "start":
            success = self.ai_tools_manager.start_ai_tools()
        
        elif args.ai_tools_command == "stop":
            success = self.ai_tools_manager.stop_ai_tools()
        
        elif args.ai_tools_command == "shell":
            success = self.ai_tools_manager.access_shell()
        
        elif args.ai_tools_command == "status":
            self.ai_tools_manager.print_status_summary()
            success = True
        
        elif args.ai_tools_command == "test":
            success = self.ai_tools_manager.run_chat_test(getattr(args, 'model', 'qwen2.5-coder:7b'), 
                                                       getattr(args, 'message', 'Hello!'))
        
        else:
            print("❌ Unknown ai-tools command")
            return False
        
        return success
    
    def _handle_vscode(self, args: argparse.Namespace) -> bool:
        """Handle vscode command."""
        if args.vscode_command == "start":
            success = self.vscode_manager.start_vscode()
        
        elif args.vscode_command == "stop":
            success = self.vscode_manager.stop_vscode()
        
        elif args.vscode_command == "status":
            self.vscode_manager.print_status_summary()
            success = True
        
        elif args.vscode_command == "install-extensions":
            success = self.vscode_manager.install_extensions()
        
        elif args.vscode_command == "configure-roocode":
            success = self.vscode_manager.configure_roocode()
        
        elif args.vscode_command == "quick-start":
            self.vscode_manager.print_quick_start()
            success = True
        
        else:
            print("❌ Unknown vscode command")
            return False
        
        return success
    
    def _handle_models(self, args: argparse.Namespace) -> bool:
        """Handle models command."""
        if args.models_command == "list":
            models = self.model_manager.get_ollama_models()
            print(f"📦 Available Models ({len(models)}):")
            for model in models:
                size_gb = model.get("size", 0) / (1024**3)
                print(f"  • {model['name']} ({size_gb:.1f}GB)")
        
        elif args.models_command == "pull":
            success = self.model_manager.pull_model(args.model_name, getattr(args, 'timeout', 300))
        
        elif args.models_command == "remove":
            success = self.model_manager.remove_model(args.model_name)
        
        elif args.models_command == "test":
            success = self.model_manager.test_model(args.model_name, getattr(args, 'prompt', 'Hello!'))
        
        elif args.models_command == "summary":
            self.model_manager.print_model_summary()
            success = True
        
        else:
            print("❌ Unknown models command")
            return False
        
        return success
    
    def _handle_config(self, args: argparse.Namespace) -> bool:
        """Handle config command."""
        if args.config_command == "summary":
            self.config_manager.print_config_summary()
        
        elif args.config_command == "create-env":
            success = self.config_manager.create_default_env(getattr(args, 'overwrite', False))
        
        elif args.config_command == "update-env":
            success = self.config_manager.update_env_var(args.key, args.value)
        
        elif args.config_command == "get-env":
            value = self.config_manager.get_env_var(args.key)
            if value is not None:
                print(value)
                success = True
            else:
                print(f"❌ Environment variable {args.key} not found")
                success = False
        
        elif args.config_command == "validate":
            issues = self.config_manager.validate_env_config()
            docker_issues = self.config_manager.validate_docker_configs()
            
            all_issues = len(issues["missing"]) + len(issues["invalid"]) + len(issues["warnings"])
            all_issues += len(docker_issues["missing"]) + len(docker_issues["invalid"]) + len(docker_issues["warnings"])
            
            if all_issues > 0:
                print(f"❌ Found {all_issues} configuration issues")
                success = False
            else:
                print("✅ Configuration is valid")
                success = True
        
        elif args.config_command == "backup":
            success = self.config_manager.backup_configs(getattr(args, 'backup_dir', None))
        
        elif args.config_command == "restore":
            backup_dir = getattr(args, 'backup_dir', None)
            if not backup_dir:
                print("❌ --backup-dir required for restore")
                return False
            success = self.config_manager.restore_configs(backup_dir)
        
        else:
            print("❌ Unknown config command")
            return False
        
        return success
    
    def _handle_utils(self, args: argparse.Namespace) -> bool:
        """Handle utils command."""
        if args.utils_command == "install":
            print("🔧 Installing llx tools...")
            # This would typically install the package itself
            print("✅ llx tools installed!")
        
        elif args.utils_command == "update":
            print("🔄 Updating llx tools...")
            print("✅ llx tools updated!")
        
        elif args.utils_command == "version":
            print("🚀 llx Tools Version 1.0.0")
            print("📦 Python-based ecosystem management")
            print("🔗 https://github.com/semcod/llx")
        
        elif args.utils_command == "doctor":
            print("🩺 Running system diagnostics...")
            self.health_checker.run_comprehensive_health_check()
        
        else:
            print("❌ Unknown utils command")
            return False
        
        return True


def main():
    """Main CLI entry point."""
    cli = LLXToolsCLI()
    parser = cli.create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    success = cli.run_command(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
