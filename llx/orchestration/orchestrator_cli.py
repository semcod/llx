"""
Orchestrator CLI for llx
Unified command-line interface for the complete llx orchestration system.
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import all orchestrator components
from .session_manager import SessionManager, SessionType, SessionStatus
from .instance_manager import InstanceManager, InstanceType, InstanceStatus
from .rate_limiter import RateLimiter, LimitType
from .queue_manager import QueueManager, RequestPriority
from .routing_engine import RoutingEngine, ResourceType, RoutingStrategy
from .vscode_orchestrator import VSCodeOrchestrator, VSCodeAccountType
from .llm_orchestrator import LLMOrchestrator, LLMProviderType, ModelCapability


class OrchestratorCLI:
    """Unified CLI for llx orchestration system."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        
        # Initialize all orchestrators
        self.session_manager = SessionManager()
        self.instance_manager = InstanceManager()
        self.rate_limiter = RateLimiter()
        self.queue_manager = QueueManager()
        self.routing_engine = RoutingEngine()
        self.vscode_orchestrator = VSCodeOrchestrator()
        self.llm_orchestrator = LLMOrchestrator()
        
        self.orchestrators = {
            "sessions": self.session_manager,
            "instances": self.instance_manager,
            "rate_limits": self.rate_limiter,
            "queues": self.queue_manager,
            "routing": self.routing_engine,
            "vscode": self.vscode_orchestrator,
            "llm": self.llm_orchestrator
        }
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(
            prog="llx-orchestrator",
            description="llx Orchestration System CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  llx-orchestrator start                    # Start all orchestrators
  llx-orchestrator status                    # Show system status
  llx-orchestrator vscode start              # Start VS Code instance
  llx-orchestrator llm complete             # Complete LLM request
  llx-orchestrator route llm "Hello world"   # Route request to best provider
  llx-orchestrator monitor                   # Monitor system health
  
For detailed help on subcommands:
  llx-orchestrator <command> --help
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
            description="Manage llx orchestration system",
            metavar="COMMAND"
        )
        
        # System management
        system_parser = subparsers.add_parser(
            "start",
            help="Start all orchestrators"
        )
        
        stop_parser = subparsers.add_parser(
            "stop",
            help="Stop all orchestrators"
        )
        
        restart_parser = subparsers.add_parser(
            "restart",
            help="Restart all orchestrators"
        )
        
        status_parser = subparsers.add_parser(
            "status",
            help="Show system status"
        )
        
        health_parser = subparsers.add_parser(
            "health",
            help="Check system health"
        )
        
        monitor_parser = subparsers.add_parser(
            "monitor",
            help="Monitor system metrics"
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
            help="Start VS Code instance"
        )
        
        vscode_start_parser = vscode_subparsers.add_parser(
            "start-instance",
            help="Start specific VS Code instance"
        )
        vscode_start_parser.add_argument(
            "--instance-id",
            help="Instance ID to start"
        )
        vscode_start_parser.add_argument(
            "--account-id",
            help="Account ID to use"
        )
        vscode_start_parser.add_argument(
            "--workspace",
            help="Workspace path"
        )
        
        vscode_subparsers.add_parser(
            "stop",
            help="Stop VS Code instance"
        )
        vscode_stop_parser = vscode_subparsers.add_parser(
            "stop-instance",
            help="Stop specific VS Code instance"
        )
        vscode_stop_parser.add_argument(
            "--instance-id",
            help="Instance ID to stop"
        )
        
        vscode_subparsers.add_parser(
            "list-instances",
            help="List VS Code instances"
        )
        vscode_subparsers.add_parser(
            "list-sessions",
            help="List VS Code sessions"
        )
        vscode_subparsers.add_parser(
            "add-account",
            help="Add VS Code account"
        )
        vscode_add_parser = vscode_subparsers.add_parser(
            "add-account",
            help="Add VS Code account"
        )
        vscode_add_parser.add_argument(
            "--account-id",
            required=True,
            help="Account ID"
        )
        vscode_add_parser.add_argument(
            "--name",
            required=True,
            help="Account name"
        )
        vscode_add_parser.add_argument(
            "--type",
            choices=["local", "github", "microsoft", "windsurf", "cursor", "codeium"],
            required=True,
            help="Account type"
        )
        vscode_add_parser.add_argument(
            "--email",
            help="Account email"
        )
        vscode_add_parser.add_argument(
            "--auth-method",
            choices=["browser", "token", "password"],
            default="password",
            help="Authentication method"
        )
        
        # LLM management
        llm_parser = subparsers.add_parser(
            "llm",
            help="LLM management"
        )
        llm_subparsers = llm_parser.add_subparsers(
            dest="llm_command",
            title="LLM Commands"
        )
        
        llm_subparsers.add_parser(
            "list-providers",
            help="List LLM providers"
        )
        
        llm_subparsers.add_parser(
            "list-models",
            help="List available models"
        )
        llm_list_parser = llm_subparsers.add_parser(
            "list-models",
            help="List available models"
        )
        llm_list_parser.add_argument(
            "--provider",
            help="Filter by provider"
        )
        llm_list_parser.add_argument(
            "--capability",
            choices=["code_generation", "text_generation", "reasoning", "math", "multimodal", "function_calling", "chat", "completion"],
            help="Filter by capability"
        )
        
        llm_subparsers.add_parser(
            "model-info",
            help="Get model information"
        )
        llm_info_parser = llm_subparsers.add_parser(
            "model-info",
            help="Get model information"
        )
        llm_info_parser.add_argument(
            "--model-id",
            required=True,
            help="Model ID"
        )
        
        llm_subparsers.add_parser(
            "complete",
            help="Complete LLM request"
        )
        llm_complete_parser = llm_subparsers.add_parser(
            "complete",
            help="Complete LLM request"
        )
        llm_complete_parser.add_argument(
            "--provider",
            help="Provider to use"
        )
        llm_complete_parser.add_argument(
            "--model",
            help="Model to use"
        )
        llm_complete_parser.add_argument(
            "--prompt",
            required=True,
            help="Prompt to complete"
        )
        llm_complete_parser.add_argument(
            "--temperature",
            type=float,
            default=0.7,
            help="Temperature"
        )
        llm_complete_parser.add_argument(
            "--max-tokens",
            type=int,
            default=1000,
            help="Max tokens"
        )
        llm_complete_parser.add_argument(
            "--stream",
            action="store_true",
            help="Stream response"
        )
        
        # Request routing
        route_parser = subparsers.add_parser(
            "route",
            help="Route requests to optimal resources"
        )
        route_parser.add_argument(
            "resource_type",
            choices=["llm", "vscode", "ai_tools"],
            help="Resource type to route to"
        )
        route_parser.add_argument(
            "prompt",
            help="Prompt or request content"
        )
        route_parser.add_argument(
            "--provider",
            help="Preferred provider"
        )
        route_parser.add_argument(
            "--account",
            help="Preferred account"
        )
        route_parser.add_argument(
            "--model",
            help="Preferred model"
        )
        route_parser.add_argument(
            "--strategy",
            choices=["round_robin", "least_loaded", "priority_based", "cost_optimized", "performance_optimized", "availability_first"],
            default="availability_first",
            help="Routing strategy"
        )
        route_parser.add_argument(
            "--priority",
            choices=["urgent", "high", "normal", "low", "background"],
            default="normal",
            help="Request priority"
        )
        
        # Queue management
        queue_parser = subparsers.add_parser(
            "queue",
            help="Queue management"
        )
        queue_subparsers = queue_parser.add_subparsers(
            dest="queue_command",
            title="Queue Commands"
        )
        
        queue_subparsers.add_parser(
            "status",
            help="Show queue status"
        )
        
        queue_subparsers.add_parser(
            "metrics",
            help="Show queue metrics"
        )
        queue_metrics_parser = queue_subparsers.add_parser(
            "metrics",
            help="Show queue metrics"
        )
        queue_metrics_parser.add_argument(
            "--queue-id",
            help="Specific queue ID"
        )
        
        # Rate limiting
        rate_parser = subparsers.add_parser(
            "rate-limit",
            help="Rate limiting management"
        )
        rate_subparsers = rate_parser.add_subparsers(
            dest="rate_command",
            title="Rate Limit Commands"
        )
        
        rate_subparsers.add_parser(
            "status",
            help="Show rate limit status"
        )
        rate_subparsers.add_parser(
            "available",
            help="Show available providers"
        )
        rate_available_parser = rate_subparsers.add_parser(
            "available",
            help="Show available providers"
        )
        rate_available_parser.add_argument(
            "--type",
            choices=["requests_per_hour", "tokens_per_hour", "requests_per_minute", "concurrent_requests"],
            default="requests_per_hour",
            help="Limit type"
        )
        
        # Session management
        session_parser = subparsers.add_parser(
            "session",
            help="Session management"
        )
        session_subparsers = session_parser.add_subparsers(
            dest="session_command",
            title="Session Commands"
        )
        
        session_subparsers.add_parser(
            "list",
            help="List sessions"
        )
        session_list_parser = session_subparsers.add_parser(
            "list",
            help="List sessions"
        )
        session_list_parser.add_argument(
            "--type",
            choices=["llm", "vscode", "ai_tools"],
            help="Filter by session type"
        )
        session_list_parser.add_argument(
            "--status",
            choices=["idle", "active", "busy", "rate_limited", "error", "terminated"],
            help="Filter by status"
        )
        
        session_subparsers.add_parser(
            "create",
            help="Create session"
        )
        session_create_parser = session_subparsers.add_parser(
            "create",
            help="Create session"
        )
        session_create_parser.add_argument(
            "--session-id",
            required=True,
            help="Session ID"
        )
        session_create_parser.add_argument(
            "--type",
            choices=["llm", "vscode", "ai_tools"],
            required=True,
            help="Session type"
        )
        session_create_parser.add_argument(
            "--provider",
            required=True,
            help="Provider"
        )
        session_create_parser.add_argument(
            "--model",
            help="Model"
        )
        session_create_parser.add_argument(
            "--account",
            default="default",
            help="Account"
        )
        
        # Instance management
        instance_parser = subparsers.add_parser(
            "instance",
            help="Instance management"
        )
        instance_subparsers = instance_parser.add_subparsers(
            dest="instance_command",
            title="Instance Commands"
        )
        
        instance_subparsers.add_parser(
            "list",
            help="List instances"
        )
        instance_list_parser = instance_subparsers.add_parser(
            "list",
            help="List instances"
        )
        instance_list_parser.add_argument(
            "--type",
            choices=["vscode", "ai_tools", "llm_proxy"],
            help="Filter by instance type"
        )
        instance_list_parser.add_argument(
            "--status",
            choices=["creating", "running", "stopping", "stopped", "error", "maintenance"],
            help="Filter by status"
        )
        
        instance_subparsers.add_parser(
            "create",
            help="Create instance"
        )
        instance_create_parser = instance_subparsers.add_parser(
            "create",
            help="Create instance"
        )
        instance_create_parser.add_argument(
            "--instance-id",
            required=True,
            help="Instance ID"
        )
        instance_create_parser.add_argument(
            "--type",
            choices=["vscode", "ai_tools", "llm_proxy"],
            required=True,
            help="Instance type"
        )
        instance_create_parser.add_argument(
            "--account",
            default="default",
            help="Account"
        )
        instance_create_parser.add_argument(
            "--provider",
            default="default",
            help="Provider"
        )
        instance_create_parser.add_argument(
            "--port",
            type=int,
            help="Port number"
        )
        instance_create_parser.add_argument(
            "--image",
            help="Docker image"
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
            "show",
            help="Show configuration"
        )
        config_show_parser = config_subparsers.add_parser(
            "show",
            help="Show configuration"
        )
        config_show_parser.add_argument(
            "--component",
            choices=["sessions", "instances", "rate_limits", "queues", "routing", "vscode", "llm"],
            help="Specific component"
        )
        
        config_subparsers.add_parser(
            "save",
            help="Save configuration"
        )
        
        config_subparsers.add_parser(
            "load",
            help="Load configuration"
        )
        
        # Utilities
        utils_parser = subparsers.add_parser(
            "utils",
            help="Utility commands"
        )
        utils_subparsers = utils_parser.add_subparsers(
            dest="utils_command",
            title="Utility Commands"
        )
        
        utils_subparsers.add_parser(
            "cleanup",
            help="Cleanup resources"
        )
        
        utils_subparsers.add_parser(
            "reset",
            help="Reset system state"
        )
        
        utils_subparsers.add_parser(
            "doctor",
            help="Run system diagnostics"
        )
        
        utils_subparsers.add_parser(
            "benchmark",
            help="Run performance benchmarks"
        )
        utils_benchmark_parser = utils_subparsers.add_parser(
            "benchmark",
            help="Run performance benchmarks"
        )
        utils_benchmark_parser.add_argument(
            "--component",
            choices=["routing", "rate_limiting", "queue", "all"],
            default="all",
            help="Component to benchmark"
        )
        utils_benchmark_parser.add_argument(
            "--iterations",
            type=int,
            default=100,
            help="Number of iterations"
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
            elif args.command == "monitor":
                return self._handle_monitor(args)
            elif args.command == "vscode":
                return self._handle_vscode(args)
            elif args.command == "llm":
                return self._handle_llm(args)
            elif args.command == "route":
                return self._handle_route(args)
            elif args.command == "queue":
                return self._handle_queue(args)
            elif args.command == "rate-limit":
                return self._handle_rate_limit(args)
            elif args.command == "session":
                return self._handle_session(args)
            elif args.command == "instance":
                return self._handle_instance(args)
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
        print("🚀 Starting llx orchestration system...")
        
        # Start all orchestrators
        for name, orchestrator in self.orchestrators.items():
            if hasattr(orchestrator, 'start'):
                orchestrator.start()
                print(f"  ✅ Started {name}")
        
        print("✅ All orchestrators started!")
        return True
    
    def _handle_stop(self, args: argparse.Namespace) -> bool:
        """Handle stop command."""
        print("🛑 Stopping llx orchestration system...")
        
        # Stop all orchestrators
        for name, orchestrator in self.orchestrators.items():
            if hasattr(orchestrator, 'stop'):
                orchestrator.stop()
                print(f"  ✅ Stopped {name}")
        
        print("✅ All orchestrators stopped!")
        return True
    
    def _handle_restart(self, args: argparse.Namespace) -> bool:
        """Handle restart command."""
        print("🔄 Restarting llx orchestration system...")
        
        self._handle_stop(args)
        time.sleep(2)
        self._handle_start(args)
        
        return True
    
    def _handle_status(self, args: argparse.Namespace) -> bool:
        """Handle status command."""
        print("📊 llx Orchestration System Status")
        print("=================================")
        
        # Show overall system status
        print("\n🏗️  System Components:")
        for name, orchestrator in self.orchestrators.items():
            if hasattr(orchestrator, 'print_status_summary'):
                print(f"\n{name.title()}:")
                orchestrator.print_status_summary()
            else:
                print(f"\n{name.title()}: Running")
        
        return True
    
    def _handle_health(self, args: argparse.Namespace) -> bool:
        """Handle health command."""
        print("🏥 System Health Check")
        print("====================")
        
        # Check all components
        health_results = {}
        
        for name, orchestrator in self.orchestrators.items():
            if hasattr(orchestrator, 'health_check_all'):
                results = orchestrator.health_check_all()
                health_results[name] = results
            elif hasattr(orchestrator, 'get_queue_status'):
                status = orchestrator.get_queue_status()
                health_results[name] = {"healthy": True, "details": status}
            else:
                health_results[name] = {"healthy": True, "details": "Running"}
        
        # Display results
        for name, results in health_results.items():
            status = "✅ Healthy" if results.get("healthy") else "❌ Unhealthy"
            print(f"{status} {name}")
        
        return all(results.get("healthy") for results in health_results.values())
    
    def _handle_monitor(self, args: argparse.Namespace) -> bool:
        """Handle monitor command."""
        print(f"🔍 Monitoring system (interval: {args.interval}s, duration: {args.duration}s)")
        print("=" * 50)
        
        start_time = time.time()
        
        while time.time() - start_time < args.duration:
            # Collect metrics
            timestamp = time.strftime("%H:%M:%S")
            
            metrics = {
                "timestamp": timestamp,
                "sessions": len(self.session_manager.session_states),
                "instances": len(self.instance_manager.instances),
                "queues": len(self.queue_manager.queues)
            }
            
            # Display metrics
            print(f"\r{timestamp} | Sessions: {metrics['sessions']} | Instances: {metrics['instances']} | Queues: {metrics['queues']}", end="", flush=True)
            
            time.sleep(args.interval)
        
        print("\n✅ Monitoring completed")
        return True
    
    def _handle_vscode(self, args: argparse.Namespace) -> bool:
        """Handle VS Code commands."""
        if not args.vscode_command:
            print("❌ VS Code command required")
            return False
        
        if args.vscode_command == "start-instance":
            if not args.instance_id:
                print("❌ --instance-id required for start-instance")
                return False
            
            session_id = self.vscode_orchestrator.start_instance(args.instance_id)
            if session_id:
                print(f"✅ Started VS Code instance {args.instance_id}")
                print(f"   Session ID: {session_id}")
                
                # Get session details
                session_status = self.vscode_orchestrator.get_session_status(session_id)
                if session_status:
                    print(f"   URL: {session_status['url']}")
                    print(f"   Workspace: {session_status['workspace_path']}")
            else:
                print(f"❌ Failed to start VS Code instance {args.instance_id}")
                return False
        
        elif args.vscode_command == "stop-instance":
            if not args.instance_id:
                print("❌ --instance-id required for stop-instance")
                return False
            
            success = self.vscode_orchestrator.remove_instance(args.instance_id)
            if success:
                print(f"✅ Stopped VS Code instance {args.instance_id}")
            else:
                print(f"❌ Failed to stop VS Code instance {args.instance_id}")
                return False
        
        elif args.vscode_command == "list-instances":
            instances = self.vscode_orchestrator.list_instances()
            print(f"📋 VS Code Instances ({len(instances)}):")
            for instance in instances:
                status_icon = "🟢" if instance["status"] == "running" else "🔴"
                print(f"  {status_icon} {instance['instance_id']}: {instance['status']} (port {instance['port']})")
                if instance.get('url'):
                    print(f"    URL: {instance['url']}")
        
        elif args.vscode_command == "list-sessions":
            sessions = self.vscode_orchestrator.list_sessions()
            print(f"👥 VS Code Sessions ({len(sessions)}):")
            for session in sessions:
                duration = session.get('session_duration_minutes', 0)
                print(f"  • {session['session_id']}: {session['account_name']} - {duration:.1f}min")
                print(f"    URL: {session['url']}")
        
        elif args.vscode_command == "add-account":
            from .vscode_orchestrator import VSCodeAccount
            
            account = VSCodeAccount(
                account_id=args.account_id,
                account_type=VSCodeAccountType(args.type),
                name=args.name,
                email=args.email,
                auth_method=args.auth_method
            )
            
            success = self.vscode_orchestrator.add_account(account)
            if success:
                self.vscode_orchestrator.save_config()
                print(f"✅ Added VS Code account: {args.account_id}")
            else:
                print(f"❌ Failed to add VS Code account: {args.account_id}")
                return False
        
        return True
    
    def _handle_llm(self, args: argparse.Namespace) -> bool:
        """Handle LLM commands."""
        if not args.llm_command:
            print("❌ LLM command required")
            return False
        
        if args.llm_command == "list-providers":
            status = self.llm_orchestrator.get_provider_status()
            print(f"🏢 LLM Providers ({status['total_providers']}):")
            for provider_id, provider_status in status["providers"].items():
                health_icon = "🟢" if provider_status["health_status"] == "healthy" else "🔴"
                print(f"  {health_icon} {provider_id}: {provider_status['name']} ({provider_status['models_count']} models)")
        
        elif args.llm_command == "list-models":
            from .llm_orchestrator import ModelCapability
            
            capability = ModelCapability(args.capability) if args.capability else None
            models = self.llm_orchestrator.list_models(args.provider, capability)
            
            print(f"🤖 Available Models ({len(models)}):")
            for model in models:
                print(f"  • {model['model_id']}: {model['display_name']} ({model['provider']})")
                print(f"    Capabilities: {', '.join(model['capabilities'])}")
                print(f"    Cost: ${model['cost_per_1k_input']:.4f}/{model['cost_per_1k_output']:.4f} per 1K tokens")
        
        elif args.llm_command == "model-info":
            if not args.model_id:
                print("❌ --model-id required for model-info")
                return False
            
            model_info = self.llm_orchestrator.get_model_info(args.model_id)
            if model_info:
                print(json.dumps(model_info, indent=2))
            else:
                print(f"❌ Model {args.model_id} not found")
                return False
        
        elif args.llm_command == "complete":
            from .llm_orchestrator import LLMRequest, RequestPriority
            
            # Create request
            request_id = f"cli-{int(time.time())}"
            request = LLMRequest(
                request_id=request_id,
                provider=args.provider or "ollama-local",
                model=args.model or "qwen2.5-coder:7b",
                messages=[{"role": "user", "content": args.prompt}],
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                stream=args.stream,
                priority=RequestPriority.NORMAL
            )
            
            print(f"🤖 Completing LLM request...")
            print(f"   Provider: {request.provider}")
            print(f"   Model: {request.model}")
            print(f"   Prompt: {args.prompt[:100]}...")
            
            # Complete request
            response = self.llm_orchestrator.complete_request(request)
            
            if response.success:
                print(f"✅ Request completed successfully!")
                print(f"   Tokens: {response.total_tokens}")
                print(f"   Cost: ${response.cost:.6f}")
                print(f"   Latency: {response.latency_ms:.0f}ms")
                print(f"   Response: {response.content[:200]}...")
            else:
                print(f"❌ Request failed: {response.error}")
                return False
        
        return True
    
    def _handle_route(self, args: argparse.Namespace) -> bool:
        """Handle routing command."""
        from .routing_engine import ResourceType, RoutingRequest, RequestPriority, RoutingStrategy
        
        # Create routing request
        request_id = f"route-{int(time.time())}"
        routing_request = RoutingRequest(
            request_id=request_id,
            resource_type=ResourceType(args.resource_type),
            provider=args.provider,
            account=args.account,
            model=args.model,
            priority=RequestPriority(args.priority),
            strategy=RoutingStrategy(args.strategy),
            requirements={"estimated_tokens": 1000}
        )
        
        print(f"🧭 Routing request to optimal resource...")
        print(f"   Resource Type: {args.resource_type}")
        print(f"   Strategy: {args.strategy}")
        print(f"   Priority: {args.priority}")
        
        # Route request
        decision = self.routing_engine.route_request(routing_request)
        
        if decision and decision.confidence > 0:
            print(f"✅ Routing successful!")
            print(f"   Selected Resource: {decision.selected_resource}")
            print(f"   Provider: {decision.provider}")
            print(f"   Model: {decision.model}")
            print(f"   Strategy: {decision.strategy_used.value}")
            print(f"   Confidence: {decision.confidence:.2f}")
            print(f"   Estimated Wait: {decision.estimated_wait_time:.1f}s")
            print(f"   Estimated Cost: ${decision.estimated_cost:.6f}")
            print(f"   Reasoning: {' | '.join(decision.reasoning)}")
        else:
            print(f"❌ Routing failed: No suitable resource found")
            return False
        
        return True
    
    def _handle_queue(self, args: argparse.Namespace) -> bool:
        """Handle queue commands."""
        if not args.queue_command:
            print("❌ Queue command required")
            return False
        
        if args.queue_command == "status":
            status = self.queue_manager.get_queue_status()
            print(json.dumps(status, indent=2))
        
        elif args.queue_command == "metrics":
            if args.queue_id:
                metrics = self.queue_manager.get_queue_metrics(args.queue_id)
                if metrics:
                    print(json.dumps(metrics, indent=2))
                else:
                    print(f"❌ No metrics available for queue {args.queue_id}")
            else:
                self.queue_manager.print_status_summary()
        
        return True
    
    def _handle_rate_limit(self, args: argparse.Namespace) -> bool:
        """Handle rate limit commands."""
        if not args.rate_command:
            print("❌ Rate limit command required")
            return False
        
        if args.rate_command == "status":
            status = self.rate_limiter.get_status()
            print(json.dumps(status, indent=2))
        
        elif args.rate_command == "available":
            from .rate_limiter import LimitType
            
            limit_type = LimitType(args.type)
            available = self.rate_limiter.get_available_providers(limit_type)
            
            print(f"📋 Available Providers for {args.type}:")
            for provider in available:
                print(f"  • {provider['provider']}:{provider['account']} (score: {provider['score']:.1f}, utilization: {provider['utilization']:.1f}%)")
        
        return True
    
    def _handle_session(self, args: argparse.Namespace) -> bool:
        """Handle session commands."""
        if not args.session_command:
            print("❌ Session command required")
            return False
        
        if args.session_command == "list":
            from .session_manager import SessionType, SessionStatus
            
            session_type = SessionType(args.type) if args.type else None
            session_status = SessionStatus(args.status) if args.status else None
            
            sessions = self.session_manager.list_sessions(session_type, session_status)
            print(f"📋 Sessions ({len(sessions)}):")
            for session in sessions:
                print(f"  • {session['session_id']}: {session['status']} ({session['type']})")
        
        elif args.session_command == "create":
            from .session_manager import SessionConfig, SessionType
            
            config = SessionConfig(
                session_id=args.session_id,
                session_type=SessionType(args.type),
                provider=args.provider,
                model=args.model or "default",
                account=args.account
            )
            
            success = self.session_manager.create_session(config)
            if success:
                self.session_manager.save_sessions()
                print(f"✅ Created session: {args.session_id}")
            else:
                print(f"❌ Failed to create session: {args.session_id}")
                return False
        
        return True
    
    def _handle_instance(self, args: argparse.Namespace) -> bool:
        """Handle instance commands."""
        if not args.instance_command:
            print("❌ Instance command required")
            return False
        
        if args.instance_command == "list":
            from .instance_manager import InstanceType, InstanceStatus
            
            instance_type = InstanceType(args.type) if args.type else None
            instance_status = InstanceStatus(args.status) if args.status else None
            
            instances = self.instance_manager.list_instances(instance_type, instance_status)
            print(f"📋 Instances ({len(instances)}):")
            for instance in instances:
                print(f"  • {instance['instance_id']}: {instance['status']} ({instance['type']}, port {instance['port']})")
        
        elif args.instance_command == "create":
            from .instance_manager import InstanceConfig, InstanceType
            
            config = InstanceConfig(
                instance_id=args.instance_id,
                instance_type=InstanceType(args.type),
                account=args.account,
                provider=args.provider,
                port=args.port or 0,
                image=args.image or "default"
            )
            
            success = self.instance_manager.create_instance(config)
            if success:
                self.instance_manager.save_instances()
                print(f"✅ Created instance: {args.instance_id}")
            else:
                print(f"❌ Failed to create instance: {args.instance_id}")
                return False
        
        return True
    
    def _handle_config(self, args: argparse.Namespace) -> bool:
        """Handle configuration commands."""
        if not args.config_command:
            print("❌ Config command required")
            return False
        
        if args.config_command == "show":
            if args.component:
                orchestrator = self.orchestrators.get(args.component)
                if orchestrator and hasattr(orchestrator, 'print_status_summary'):
                    orchestrator.print_status_summary()
                else:
                    print(f"❌ Component {args.component} not found or has no status")
                    return False
            else:
                self._handle_status(args)
        
        elif args.config_command == "save":
            # Save all configurations
            for name, orchestrator in self.orchestrators.items():
                if hasattr(orchestrator, 'save_config'):
                    orchestrator.save_config()
                    print(f"  ✅ Saved {name} configuration")
        
        elif args.config_command == "load":
            # Load all configurations
            for name, orchestrator in self.orchestrators.items():
                if hasattr(orchestrator, 'load_config'):
                    orchestrator.load_config()
                    print(f"  ✅ Loaded {name} configuration")
        
        return True
    
    def _handle_utils(self, args: argparse.Namespace) -> bool:
        """Handle utility commands."""
        if not args.utils_command:
            print("❌ Utils command required")
            return False
        
        if args.utils_command == "cleanup":
            print("🧹 Cleaning up resources...")
            
            # Cleanup all orchestrators
            for name, orchestrator in self.orchestrators.items():
                if hasattr(orchestrator, 'save_config'):
                    orchestrator.save_config()
            
            print("✅ Cleanup completed")
        
        elif args.utils_command == "reset":
            print("🔄 Resetting system state...")
            
            # Reset all orchestrators
            for name, orchestrator in self.orchestrators.items():
                if hasattr(orchestrator, 'stop'):
                    orchestrator.stop()
                if hasattr(orchestrator, 'start'):
                    orchestrator.start()
            
            print("✅ System reset completed")
        
        elif args.utils_command == "doctor":
            print("🩺 Running system diagnostics...")
            
            # Run comprehensive health check
            health_status = self._handle_health(args)
            
            # Check configuration files
            config_files = [
                self.project_root / "orchestration" / "sessions.json",
                self.project_root / "orchestration" / "instances.json",
                self.project_root / "orchestration" / "rate_limits.json",
                self.project_root / "orchestration" / "queues.json",
                self.project_root / "orchestration" / "routing.json",
                self.project_root / "orchestration" / "vscode.json",
                self.project_root / "orchestration" / "llm.json"
            ]
            
            print("\n📁 Configuration Files:")
            for config_file in config_files:
                status = "✅" if config_file.exists() else "❌"
                print(f"  {status} {config_file.name}")
            
            return health_status
        
        elif args.utils_command == "benchmark":
            print(f"🏃 Running benchmarks ({args.iterations} iterations)...")
            
            if args.component == "all" or args.component == "routing":
                print("\n🧭 Routing Benchmark:")
                self._benchmark_routing(args.iterations)
            
            if args.component == "all" or args.component == "rate_limiting":
                print("\n⏱️  Rate Limiting Benchmark:")
                self._benchmark_rate_limiting(args.iterations)
            
            if args.component == "all" or args.component == "queue":
                print("\n📋 Queue Benchmark:")
                self._benchmark_queue(args.iterations)
            
            print("✅ Benchmarks completed")
        
        return True
    
    def _benchmark_routing(self, iterations: int):
        """Benchmark routing performance."""
        import time
        from .routing_engine import ResourceType, RoutingRequest, RequestPriority, RoutingStrategy
        
        start_time = time.time()
        successful_routes = 0
        
        for i in range(iterations):
            request = RoutingRequest(
                request_id=f"benchmark-{i}",
                resource_type=ResourceType.LLM,
                strategy=RoutingStrategy.AVAILABILITY_FIRST,
                priority=RequestPriority.NORMAL
            )
            
            decision = self.routing_engine.route_request(request)
            if decision:
                successful_routes += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"  Total Time: {total_time:.3f}s")
        print(f"  Average Time: {(total_time / iterations * 1000):.2f}ms")
        print(f"  Success Rate: {(successful_routes / iterations * 100):.1f}%")
        print(f"  Throughput: {(iterations / total_time):.1f} requests/sec")
    
    def _benchmark_rate_limiting(self, iterations: int):
        """Benchmark rate limiting performance."""
        import time
        from .rate_limiter import LimitType
        
        start_time = time.time()
        successful_checks = 0
        
        for i in range(iterations):
            allowed, _ = self.rate_limiter.check_rate_limit("ollama", "default", LimitType.REQUESTS_PER_HOUR)
            if allowed:
                successful_checks += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"  Total Time: {total_time:.3f}s")
        print(f"  Average Time: {(total_time / iterations * 1000):.2f}ms")
        print(f"  Success Rate: {(successful_checks / iterations * 100):.1f}%")
        print(f"  Throughput: {(iterations / total_time):.1f} checks/sec")
    
    def _benchmark_queue(self, iterations: int):
        """Benchmark queue performance."""
        import time
        from .queue_manager import QueueRequest, RequestPriority
        
        start_time = time.time()
        successful_enqueues = 0
        
        for i in range(iterations):
            request = QueueRequest(
                request_id=f"benchmark-{i}",
                provider="ollama",
                account="default",
                request_type="test",
                priority=RequestPriority.NORMAL,
                created_at=time.time()
            )
            
            success = self.queue_manager.enqueue_request(request)
            if success:
                successful_enqueues += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"  Total Time: {total_time:.3f}s")
        print(f"  Average Time: {(total_time / iterations * 1000):.2f}ms")
        print(f"  Success Rate: {(successful_enqueues / iterations * 100):.1f}%")
        print(f"  Throughput: {(iterations / total_time):.1f} enqueues/sec")


def main():
    """Main CLI entry point."""
    cli = OrchestratorCLI()
    parser = cli.create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    success = cli.run_command(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
