"""
VS Code Orchestrator for llx Orchestration
Manages multiple VS Code instances with different accounts and configurations.
"""

import os
import sys
import json
import time
import uuid
import threading
import subprocess
import webbrowser
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import requests

from .instance_manager import InstanceManager, InstanceType, InstanceStatus
from .session_manager import SessionManager, SessionType, SessionStatus
from .rate_limiter import RateLimiter, LimitType
from .routing_engine import RoutingEngine, ResourceType, RoutingRequest, RequestPriority


class VSCodeAccountType(Enum):
    """Types of VS Code accounts."""
    LOCAL = "local"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    WINDSURF = "windsurf"
    CURSOR = "cursor"
    CODEIUM = "codeium"


@dataclass
class VSCodeAccount:
    """VS Code account configuration."""
    account_id: str
    account_type: VSCodeAccountType
    name: str
    email: Optional[str]
    auth_method: str  # "browser", "token", "password"
    auth_config: Dict[str, Any] = field(default_factory=dict)
    max_concurrent_sessions: int = 3
    session_timeout_minutes: int = 120
    auto_start: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VSCodeInstanceConfig:
    """Configuration for a VS Code instance."""
    instance_id: str
    account_id: str
    port: int
    workspace_path: str
    extensions: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    auto_start_browser: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VSCodeSession:
    """Active VS Code session."""
    session_id: str
    instance_id: str
    account_id: str
    user_id: Optional[str]
    browser_session: Optional[str]
    started_at: datetime
    last_activity: datetime
    workspace_path: str
    active_files: List[str] = field(default_factory=list)
    ai_tools_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class VSCodeOrchestrator:
    """Orchestrates multiple VS Code instances with intelligent management."""
    
    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "vscode.json"
        
        # Initialize managers
        self.instance_manager = InstanceManager()
        self.session_manager = SessionManager()
        self.rate_limiter = RateLimiter()
        self.routing_engine = RoutingEngine()
        
        # VS Code specific data
        self.accounts: Dict[str, VSCodeAccount] = {}
        self.instance_configs: Dict[str, VSCodeInstanceConfig] = {}
        self.active_sessions: Dict[str, VSCodeSession] = {}
        self.port_allocator = VSCodePortAllocator()
        
        # Configuration
        self.config = {
            "default_port_range": (8080, 8999),
            "max_instances_per_account": 5,
            "session_cleanup_interval": 300,  # 5 minutes
            "browser_auto_close": True,
            "workspace_auto_create": True
        }
        
        # State
        self.running = False
        self.lock = threading.RLock()
        
        # Load configuration
        self.load_config()
        
        # Start orchestrator
        self.start()
    
    def load_config(self) -> bool:
        """Load VS Code orchestration configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load configuration
                self.config.update(data.get("config", {}))
                
                # Load accounts
                for account_data in data.get("accounts", []):
                    account = VSCodeAccount(
                        account_id=account_data["account_id"],
                        account_type=VSCodeAccountType(account_data["account_type"]),
                        name=account_data["name"],
                        email=account_data.get("email"),
                        auth_method=account_data["auth_method"],
                        auth_config=account_data.get("auth_config", {}),
                        max_concurrent_sessions=account_data.get("max_concurrent_sessions", 3),
                        session_timeout_minutes=account_data.get("session_timeout_minutes", 120),
                        auto_start=account_data.get("auto_start", True),
                        metadata=account_data.get("metadata", {})
                    )
                    self.accounts[account.account_id] = account
                
                # Load instance configurations
                for instance_data in data.get("instances", []):
                    config = VSCodeInstanceConfig(
                        instance_id=instance_data["instance_id"],
                        account_id=instance_data["account_id"],
                        port=instance_data["port"],
                        workspace_path=instance_data["workspace_path"],
                        extensions=instance_data.get("extensions", []),
                        settings=instance_data.get("settings", {}),
                        environment=instance_data.get("environment", {}),
                        auto_start_browser=instance_data.get("auto_start_browser", True),
                        metadata=instance_data.get("metadata", {})
                    )
                    self.instance_configs[config.instance_id] = config
                
                # Load active sessions
                for session_data in data.get("sessions", []):
                    session = VSCodeSession(
                        session_id=session_data["session_id"],
                        instance_id=session_data["instance_id"],
                        account_id=session_data["account_id"],
                        user_id=session_data.get("user_id"),
                        browser_session=session_data.get("browser_session"),
                        started_at=datetime.fromisoformat(session_data["started_at"]),
                        last_activity=datetime.fromisoformat(session_data["last_activity"]),
                        workspace_path=session_data["workspace_path"],
                        active_files=session_data.get("active_files", []),
                        ai_tools_enabled=session_data.get("ai_tools_enabled", False),
                        metadata=session_data.get("metadata", {})
                    )
                    self.active_sessions[session.session_id] = session
                
                print(f"✅ Loaded VS Code orchestration config: {len(self.accounts)} accounts, {len(self.instance_configs)} instances")
                return True
            else:
                print("📝 No existing VS Code config found, starting fresh")
                self._create_default_config()
                return True
                
        except Exception as e:
            print(f"❌ Error loading VS Code config: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save VS Code orchestration configuration."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "config": self.config,
                "accounts": [],
                "instances": [],
                "sessions": []
            }
            
            # Save accounts
            for account in self.accounts.values():
                data["accounts"].append({
                    "account_id": account.account_id,
                    "account_type": account.account_type.value,
                    "name": account.name,
                    "email": account.email,
                    "auth_method": account.auth_method,
                    "auth_config": account.auth_config,
                    "max_concurrent_sessions": account.max_concurrent_sessions,
                    "session_timeout_minutes": account.session_timeout_minutes,
                    "auto_start": account.auto_start,
                    "metadata": account.metadata
                })
            
            # Save instance configurations
            for config in self.instance_configs.values():
                data["instances"].append({
                    "instance_id": config.instance_id,
                    "account_id": config.account_id,
                    "port": config.port,
                    "workspace_path": config.workspace_path,
                    "extensions": config.extensions,
                    "settings": config.settings,
                    "environment": config.environment,
                    "auto_start_browser": config.auto_start_browser,
                    "metadata": config.metadata
                })
            
            # Save active sessions
            for session in self.active_sessions.values():
                data["sessions"].append({
                    "session_id": session.session_id,
                    "instance_id": session.instance_id,
                    "account_id": session.account_id,
                    "user_id": session.user_id,
                    "browser_session": session.browser_session,
                    "started_at": session.started_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "workspace_path": session.workspace_path,
                    "active_files": session.active_files,
                    "ai_tools_enabled": session.ai_tools_enabled,
                    "metadata": session.metadata
                })
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving VS Code config: {e}")
            return False
    
    def _create_default_config(self):
        """Create default VS Code configuration."""
        # Create default local account
        local_account = VSCodeAccount(
            account_id="local-default",
            account_type=VSCodeAccountType.LOCAL,
            name="Local Development",
            auth_method="password",
            auth_config={"password": "proxym-vscode"},
            auto_start=True
        )
        self.accounts[local_account.account_id] = local_account
        
        # Create default instance configuration
        default_instance = VSCodeInstanceConfig(
            instance_id="vscode-default",
            account_id="local-default",
            port=8080,
            workspace_path=str(self.project_root),
            auto_start_browser=True
        )
        self.instance_configs[default_instance.instance_id] = default_instance
        
        print("✅ Created default VS Code configuration")
    
    def start(self):
        """Start the VS Code orchestrator."""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            # Start background tasks
            self._start_background_tasks()
            
            # Auto-start configured instances
            self._auto_start_instances()
            
            print(f"✅ Started VS Code orchestrator")
    
    def stop(self):
        """Stop the VS Code orchestrator."""
        with self.lock:
            self.running = False
            
            # Stop all instances
            self._stop_all_instances()
            
            print(f"✅ Stopped VS Code orchestrator")
    
    def add_account(self, account: VSCodeAccount) -> bool:
        """Add a new VS Code account."""
        with self.lock:
            if account.account_id in self.accounts:
                print(f"⚠️  Account {account.account_id} already exists")
                return False
            
            self.accounts[account.account_id] = account
            print(f"✅ Added account: {account.account_id}")
            return True
    
    def remove_account(self, account_id: str) -> bool:
        """Remove a VS Code account."""
        with self.lock:
            if account_id not in self.accounts:
                print(f"❌ Account {account_id} not found")
                return False
            
            # Stop all instances for this account
            instances_to_remove = [
                instance_id for instance_id, config in self.instance_configs.items()
                if config.account_id == account_id
            ]
            
            for instance_id in instances_to_remove:
                self.remove_instance(instance_id)
            
            # Remove account
            del self.accounts[account_id]
            
            print(f"✅ Removed account: {account_id}")
            return True
    
    def create_instance(self, config: VSCodeInstanceConfig) -> bool:
        """Create a new VS Code instance."""
        with self.lock:
            if config.instance_id in self.instance_configs:
                print(f"⚠️  Instance {config.instance_id} already exists")
                return False
            
            if config.account_id not in self.accounts:
                print(f"❌ Account {config.account_id} not found")
                return False
            
            # Allocate port if not specified
            if config.port == 0:
                config.port = self.port_allocator.allocate_port(config.instance_id)
            
            self.instance_configs[config.instance_id] = config
            
            # Create workspace directory if needed
            workspace_path = Path(config.workspace_path)
            if self.config["workspace_auto_create"]:
                workspace_path.mkdir(parents=True, exist_ok=True)
            
            print(f"✅ Created instance: {config.instance_id}")
            return True
    
    def remove_instance(self, instance_id: str) -> bool:
        """Remove a VS Code instance."""
        with self.lock:
            if instance_id not in self.instance_configs:
                print(f"❌ Instance {instance_id} not found")
                return False
            
            config = self.instance_configs[instance_id]
            
            # Stop all sessions for this instance
            sessions_to_remove = [
                session_id for session_id, session in self.active_sessions.items()
                if session.instance_id == instance_id
            ]
            
            for session_id in sessions_to_remove:
                self.end_session(session_id)
            
            # Stop Docker instance
            self.instance_manager.stop_instance(instance_id)
            
            # Release port
            self.port_allocator.release_port(config.port)
            
            # Remove instance
            del self.instance_configs[instance_id]
            
            print(f"✅ Removed instance: {instance_id}")
            return True
    
    def start_instance(self, instance_id: str) -> Optional[str]:
        """Start a VS Code instance and return session ID."""
        with self.lock:
            if instance_id not in self.instance_configs:
                print(f"❌ Instance {instance_id} not found")
                return None
            
            config = self.instance_configs[instance_id]
            account = self.accounts[config.account_id]
            
            # Check account limits
            active_sessions_count = len([
                s for s in self.active_sessions.values()
                if s.account_id == config.account_id
            ])
            
            if active_sessions_count >= account.max_concurrent_sessions:
                print(f"❌ Account {config.account_id} has reached max concurrent sessions")
                return None
            
            # Create Docker instance configuration
            from .instance_manager import InstanceConfig, InstanceType
            
            docker_config = InstanceConfig(
                instance_id=instance_id,
                instance_type=InstanceType.VSCODE,
                account=config.account_id,
                provider="code-server",
                port=config.port,
                image="codercom/code-server:latest",
                environment={
                    "PASSWORD": account.auth_config.get("password", "llx-dev"),
                    "DEFAULT_WORKSPACE": config.workspace_path,
                    "PROJECT_ROOT": str(self.project_root)
                },
                volumes={
                    str(self.project_root): "/home/coder/project",
                    config.workspace_path: f"/home/coder/workspace/{instance_id}",
                    str(self.config_file): "/home/coder/vscode.json:ro"
                },
                networks=["llx-network"]
            )
            
            # Start Docker instance
            if not self.instance_manager.create_instance(docker_config):
                print(f"❌ Failed to create Docker instance {instance_id}")
                return None
            
            if not self.instance_manager.start_instance(instance_id):
                print(f"❌ Failed to start Docker instance {instance_id}")
                return None
            
            # Wait for instance to be ready
            if not self._wait_for_instance_ready(instance_id):
                print(f"❌ Instance {instance_id} failed to start properly")
                return None
            
            # Create session
            session_id = str(uuid.uuid4())
            session = VSCodeSession(
                session_id=session_id,
                instance_id=instance_id,
                account_id=config.account_id,
                user_id=None,
                browser_session=None,
                started_at=datetime.now(),
                last_activity=datetime.now(),
                workspace_path=config.workspace_path,
                ai_tools_enabled=False
            )
            
            self.active_sessions[session_id] = session
            
            # Configure VS Code
            self._configure_vscode_instance(instance_id, config)
            
            # Auto-start browser if configured
            if config.auto_start_browser:
                self._start_browser_for_instance(instance_id)
            
            print(f"✅ Started instance {instance_id} with session {session_id}")
            return session_id
    
    def end_session(self, session_id: str) -> bool:
        """End a VS Code session."""
        with self.lock:
            if session_id not in self.active_sessions:
                print(f"❌ Session {session_id} not found")
                return False
            
            session = self.active_sessions[session_id]
            
            # Close browser if configured
            if self.config["browser_auto_close"] and session.browser_session:
                self._close_browser_session(session.browser_session)
            
            # Remove session
            del self.active_sessions[session_id]
            
            print(f"✅ Ended session {session_id}")
            return True
    
    def get_available_instance(self, account_id: str = None, workspace_path: str = None) -> Optional[str]:
        """Get an available VS Code instance."""
        with self.lock:
            candidates = []
            
            for instance_id, config in self.instance_configs.items():
                # Filter by account
                if account_id and config.account_id != account_id:
                    continue
                
                # Filter by workspace
                if workspace_path and config.workspace_path != workspace_path:
                    continue
                
                # Check if instance is running
                instance_status = self.instance_manager.get_instance_status(instance_id)
                if not instance_status or instance_status["status"] != "running":
                    continue
                
                # Check account limits
                account = self.accounts[config.account_id]
                active_sessions = len([
                    s for s in self.active_sessions.values()
                    if s.account_id == config.account_id
                ])
                
                if active_sessions >= account.max_concurrent_sessions:
                    continue
                
                candidates.append(instance_id)
            
            if not candidates:
                return None
            
            # Return the first available (could be enhanced with better selection logic)
            return candidates[0]
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a VS Code session."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        config = self.instance_configs[session.instance_id]
        account = self.accounts[session.account_id]
        instance_status = self.instance_manager.get_instance_status(session.instance_id)
        
        return {
            "session_id": session.session_id,
            "instance_id": session.instance_id,
            "account_id": session.account_id,
            "account_name": account.name,
            "account_type": account.account_type.value,
            "workspace_path": session.workspace_path,
            "port": config.port,
            "url": f"http://localhost:{config.port}",
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "active_files": session.active_files,
            "ai_tools_enabled": session.ai_tools_enabled,
            "instance_status": instance_status["status"] if instance_status else "unknown",
            "session_duration_minutes": (datetime.now() - session.started_at).total_seconds() / 60
        }
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """List all VS Code accounts."""
        accounts = []
        
        for account in self.accounts.values():
            active_sessions = len([
                s for s in self.active_sessions.values()
                if s.account_id == account.account_id
            ])
            
            accounts.append({
                "account_id": account.account_id,
                "name": account.name,
                "account_type": account.account_type.value,
                "email": account.email,
                "auth_method": account.auth_method,
                "max_concurrent_sessions": account.max_concurrent_sessions,
                "active_sessions": active_sessions,
                "auto_start": account.auto_start
            })
        
        return accounts
    
    def list_instances(self, account_id: str = None) -> List[Dict[str, Any]]:
        """List all VS Code instances."""
        instances = []
        
        for instance_id, config in self.instance_configs.items():
            if account_id and config.account_id != account_id:
                continue
            
            # Get instance status
            instance_status = self.instance_manager.get_instance_status(instance_id)
            
            # Get active sessions
            active_sessions = [
                s for s in self.active_sessions.values()
                if s.instance_id == instance_id
            ]
            
            instances.append({
                "instance_id": instance_id,
                "account_id": config.account_id,
                "port": config.port,
                "workspace_path": config.workspace_path,
                "status": instance_status["status"] if instance_status else "unknown",
                "url": f"http://localhost:{config.port}" if instance_status and instance_status["status"] == "running" else None,
                "active_sessions": len(active_sessions),
                "auto_start_browser": config.auto_start_browser
            })
        
        return instances
    
    def list_sessions(self, account_id: str = None) -> List[Dict[str, Any]]:
        """List all active VS Code sessions."""
        sessions = []
        
        for session in self.active_sessions.values():
            if account_id and session.account_id != account_id:
                continue
            
            sessions.append(self.get_session_status(session.session_id))
        
        return sessions
    
    def _wait_for_instance_ready(self, instance_id: str, timeout: int = 30) -> bool:
        """Wait for VS Code instance to be ready."""
        config = self.instance_configs[instance_id]
        url = f"http://localhost:{config.port}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            
            time.sleep(2)
        
        return False
    
    def _configure_vscode_instance(self, instance_id: str, config: VSCodeInstanceConfig):
        """Configure VS Code instance with settings and extensions."""
        # This would involve copying settings files and running extension installation commands
        # For now, it's a placeholder
        pass
    
    def _start_browser_for_instance(self, instance_id: str):
        """Start browser for VS Code instance."""
        config = self.instance_configs[instance_id]
        url = f"http://localhost:{config.port}"
        
        try:
            webbrowser.open(url)
            print(f"🌐 Opened browser for {instance_id}: {url}")
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
    
    def _close_browser_session(self, browser_session: str):
        """Close browser session."""
        # This would involve browser automation to close specific tabs/windows
        # For now, it's a placeholder
        pass
    
    def _auto_start_instances(self):
        """Auto-start configured instances."""
        for account in self.accounts.values():
            if not account.auto_start:
                continue
            
            # Find instances for this account
            account_instances = [
                instance_id for instance_id, config in self.instance_configs.items()
                if config.account_id == account.account_id
            ]
            
            for instance_id in account_instances:
                # Start instance if not already running
                instance_status = self.instance_manager.get_instance_status(instance_id)
                if not instance_status or instance_status["status"] != "running":
                    self.start_instance(instance_id)
    
    def _stop_all_instances(self):
        """Stop all VS Code instances."""
        for instance_id in list(self.instance_configs.keys()):
            self.instance_manager.stop_instance(instance_id)
    
    def _start_background_tasks(self):
        """Start background tasks for session management."""
        # Session cleanup thread
        cleanup_thread = threading.Thread(target=self._session_cleanup_worker, daemon=True)
        cleanup_thread.start()
        
        # Configuration save thread
        save_thread = threading.Thread(target=self._config_save_worker, daemon=True)
        save_thread.start()
    
    def _session_cleanup_worker(self):
        """Background worker for session cleanup."""
        while self.running:
            try:
                time.sleep(self.config["session_cleanup_interval"])
                
                now = datetime.now()
                sessions_to_remove = []
                
                for session_id, session in self.active_sessions.items():
                    account = self.accounts[session.account_id]
                    
                    # Check session timeout
                    session_age = (now - session.last_activity).total_seconds() / 60
                    if session_age > account.session_timeout_minutes:
                        sessions_to_remove.append(session_id)
                
                # Remove expired sessions
                for session_id in sessions_to_remove:
                    print(f"⏰ Session {session_id} expired, ending...")
                    self.end_session(session_id)
                
            except Exception as e:
                print(f"❌ Session cleanup worker error: {e}")
    
    def _config_save_worker(self):
        """Background worker for configuration saving."""
        while self.running:
            try:
                time.sleep(300)  # Every 5 minutes
                self.save_config()
            except Exception as e:
                print(f"❌ Config save worker error: {e}")
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("📝 VS Code Orchestrator Status")
        print("=============================")
        
        # Overall stats
        total_accounts = len(self.accounts)
        total_instances = len(self.instance_configs)
        active_sessions = len(self.active_sessions)
        running_instances = len([
            i for i in self.instance_configs.keys()
            if self.instance_manager.get_instance_status(i)
            and self.instance_manager.get_instance_status(i)["status"] == "running"
        ])
        
        print(f"📊 Total Accounts: {total_accounts}")
        print(f"🏗️  Total Instances: {total_instances}")
        print(f"🟢 Running Instances: {running_instances}")
        print(f"👤 Active Sessions: {active_sessions}")
        
        # Account breakdown
        print(f"\n👥 Accounts:")
        for account in self.accounts.values():
            active_count = len([
                s for s in self.active_sessions.values()
                if s.account_id == account.account_id
            ])
            print(f"  • {account.name} ({account.account_type.value}): {active_count}/{account.max_concurrent_sessions} sessions")
        
        # Instance breakdown
        print(f"\n🏗️  Instances:")
        for instance_id, config in self.instance_configs.items():
            instance_status = self.instance_manager.get_instance_status(instance_id)
            status = instance_status["status"] if instance_status else "unknown"
            sessions = len([
                s for s in self.active_sessions.values()
                if s.instance_id == instance_id
            ])
            print(f"  • {instance_id}: {status} (port {config.port}, {sessions} sessions)")
        
        print()


class VSCodePortAllocator:
    """Manages port allocation for VS Code instances."""
    
    def __init__(self):
        self.port_range = (8080, 8999)
        self.allocated_ports = set()
        self.lock = threading.Lock()
    
    def allocate_port(self, instance_id: str) -> int:
        """Allocate a port for a VS Code instance."""
        with self.lock:
            for port in range(self.port_range[0], self.port_range[1] + 1):
                if port not in self.allocated_ports and self._is_port_available(port):
                    self.allocated_ports.add(port)
                    return port
            
            raise Exception(f"No available ports in range {self.port_range[0]}-{self.port_range[1]}")
    
    def release_port(self, port: int) -> bool:
        """Release a port."""
        with self.lock:
            if port in self.allocated_ports:
                self.allocated_ports.remove(port)
                return True
            return False
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return False


# CLI interface
def main():
    """CLI interface for VS Code orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llx VS Code Orchestrator")
    parser.add_argument("command", choices=[
        "add-account", "remove-account", "list-accounts",
        "create-instance", "remove-instance", "list-instances",
        "start-instance", "end-session", "list-sessions", "status"
    ])
    parser.add_argument("--account-id", help="Account ID")
    parser.add_argument("--instance-id", help="Instance ID")
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--name", help="Account name")
    parser.add_argument("--type", choices=["local", "github", "microsoft", "windsurf", "cursor", "codeium"], help="Account type")
    parser.add_argument("--email", help="Account email")
    parser.add_argument("--auth-method", choices=["browser", "token", "password"], help="Authentication method")
    parser.add_argument("--workspace", help="Workspace path")
    parser.add_argument("--port", type=int, help="Port number")
    parser.add_argument("--max-sessions", type=int, help="Max concurrent sessions")
    
    args = parser.parse_args()
    
    orchestrator = VSCodeOrchestrator()
    
    try:
        if args.command == "add-account":
            if not args.account_id or not args.name or not args.type:
                print("❌ --account-id, --name, and --type required for add-account")
                sys.exit(1)
            
            account = VSCodeAccount(
                account_id=args.account_id,
                account_type=VSCodeAccountType(args.type),
                name=args.name,
                email=args.email,
                auth_method=args.auth_method or "password",
                max_concurrent_sessions=args.max_sessions or 3
            )
            
            success = orchestrator.add_account(account)
            if success:
                orchestrator.save_config()
        
        elif args.command == "remove-account":
            if not args.account_id:
                print("❌ --account-id required for remove-account")
                sys.exit(1)
            
            success = orchestrator.remove_account(args.account_id)
            if success:
                orchestrator.save_config()
        
        elif args.command == "list-accounts":
            accounts = orchestrator.list_accounts()
            for account in accounts:
                print(f"  • {account['account_id']}: {account['name']} ({account['account_type']}) - {account['active_sessions']}/{account['max_concurrent_sessions']} sessions")
        
        elif args.command == "create-instance":
            if not args.instance_id or not args.account_id:
                print("❌ --instance-id and --account-id required for create-instance")
                sys.exit(1)
            
            config = VSCodeInstanceConfig(
                instance_id=args.instance_id,
                account_id=args.account_id,
                port=args.port or 0,
                workspace_path=args.workspace or str(orchestrator.project_root)
            )
            
            success = orchestrator.create_instance(config)
            if success:
                orchestrator.save_config()
        
        elif args.command == "remove-instance":
            if not args.instance_id:
                print("❌ --instance-id required for remove-instance")
                sys.exit(1)
            
            success = orchestrator.remove_instance(args.instance_id)
            if success:
                orchestrator.save_config()
        
        elif args.command == "list-instances":
            instances = orchestrator.list_instances(args.account_id)
            for instance in instances:
                print(f"  • {instance['instance_id']}: {instance['status']} (port {instance['port']}, {instance['active_sessions']} sessions)")
                if instance['url']:
                    print(f"    URL: {instance['url']}")
        
        elif args.command == "start-instance":
            if not args.instance_id:
                print("❌ --instance-id required for start-instance")
                sys.exit(1)
            
            session_id = orchestrator.start_instance(args.instance_id)
            if session_id:
                print(f"✅ Started instance {args.instance_id} with session {session_id}")
            else:
                print(f"❌ Failed to start instance {args.instance_id}")
                sys.exit(1)
        
        elif args.command == "end-session":
            if not args.session_id:
                print("❌ --session-id required for end-session")
                sys.exit(1)
            
            success = orchestrator.end_session(args.session_id)
            if success:
                orchestrator.save_config()
        
        elif args.command == "list-sessions":
            sessions = orchestrator.list_sessions(args.account_id)
            for session in sessions:
                print(f"  • {session['session_id']}: {session['account_name']} - {session['session_duration_minutes']:.1f}min")
                print(f"    URL: {session['url']}")
                print(f"    Workspace: {session['workspace_path']}")
        
        elif args.command == "status":
            orchestrator.print_status_summary()
        
        sys.exit(0 if success else 1)
    
    finally:
        orchestrator.stop()


if __name__ == "__main__":
    main()
