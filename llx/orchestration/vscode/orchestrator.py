"""
VS Code Orchestrator — core orchestration logic for VS Code instances.
Extracted from the monolithic vscode_orchestrator.py.
"""

import json
import time
import uuid
import threading
import webbrowser
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import requests

from .models import VSCodeAccountType, VSCodeAccount, VSCodeInstanceConfig, VSCodeSession
from .ports import VSCodePortAllocator
from .._utils import save_json
from ..instances.manager import InstanceManager
from ..instances.models import InstanceType, InstanceConfig
from ..session.manager import SessionManager
from ..ratelimit.limiter import RateLimiter
from ..routing.engine import RoutingEngine


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
            "session_cleanup_interval": 300,
            "browser_auto_close": True,
            "workspace_auto_create": True,
        }

        # State
        self.running = False
        self.lock = threading.RLock()

        self.load_config()
        self.start()

    # ── Config persistence ──────────────────────────────────

    def load_config(self) -> bool:
        """Load VS Code orchestration configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    data = json.load(f)

                self.config.update(data.get("config", {}))

                for ad in data.get("accounts", []):
                    account = VSCodeAccount(
                        account_id=ad["account_id"],
                        account_type=VSCodeAccountType(ad["account_type"]),
                        name=ad["name"],
                        email=ad.get("email"),
                        auth_method=ad["auth_method"],
                        auth_config=ad.get("auth_config", {}),
                        max_concurrent_sessions=ad.get("max_concurrent_sessions", 3),
                        session_timeout_minutes=ad.get("session_timeout_minutes", 120),
                        auto_start=ad.get("auto_start", True),
                        metadata=ad.get("metadata", {}),
                    )
                    self.accounts[account.account_id] = account

                for id_ in data.get("instances", []):
                    cfg = VSCodeInstanceConfig(
                        instance_id=id_["instance_id"],
                        account_id=id_["account_id"],
                        port=id_["port"],
                        workspace_path=id_["workspace_path"],
                        extensions=id_.get("extensions", []),
                        settings=id_.get("settings", {}),
                        environment=id_.get("environment", {}),
                        auto_start_browser=id_.get("auto_start_browser", True),
                        metadata=id_.get("metadata", {}),
                    )
                    self.instance_configs[cfg.instance_id] = cfg

                for sd in data.get("sessions", []):
                    session = VSCodeSession(
                        session_id=sd["session_id"],
                        instance_id=sd["instance_id"],
                        account_id=sd["account_id"],
                        user_id=sd.get("user_id"),
                        browser_session=sd.get("browser_session"),
                        started_at=datetime.fromisoformat(sd["started_at"]),
                        last_activity=datetime.fromisoformat(sd["last_activity"]),
                        workspace_path=sd["workspace_path"],
                        active_files=sd.get("active_files", []),
                        ai_tools_enabled=sd.get("ai_tools_enabled", False),
                        metadata=sd.get("metadata", {}),
                    )
                    self.active_sessions[session.session_id] = session

                print(
                    f"✅ Loaded VS Code orchestration config: "
                    f"{len(self.accounts)} accounts, {len(self.instance_configs)} instances"
                )
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
            data: Dict[str, Any] = {
                "config": self.config,
                "accounts": [],
                "instances": [],
                "sessions": [],
            }

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
                    "metadata": account.metadata,
                })

            for cfg in self.instance_configs.values():
                data["instances"].append({
                    "instance_id": cfg.instance_id,
                    "account_id": cfg.account_id,
                    "port": cfg.port,
                    "workspace_path": cfg.workspace_path,
                    "extensions": cfg.extensions,
                    "settings": cfg.settings,
                    "environment": cfg.environment,
                    "auto_start_browser": cfg.auto_start_browser,
                    "metadata": cfg.metadata,
                })

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
                    "metadata": session.metadata,
                })

            return save_json(self.config_file, data, "VS Code config")

        except Exception as e:
            print(f"❌ Error saving VS Code config: {e}")
            return False

    def _create_default_config(self):
        """Create default VS Code configuration."""
        local_account = VSCodeAccount(
            account_id="local-default",
            account_type=VSCodeAccountType.LOCAL,
            name="Local Development",
            auth_method="password",
            auth_config={"password": "proxym-vscode"},
            auto_start=True,
        )
        self.accounts[local_account.account_id] = local_account

        default_instance = VSCodeInstanceConfig(
            instance_id="vscode-default",
            account_id="local-default",
            port=8080,
            workspace_path=str(self.project_root),
            auto_start_browser=True,
        )
        self.instance_configs[default_instance.instance_id] = default_instance
        print("✅ Created default VS Code configuration")

    # ── Lifecycle ───────────────────────────────────────────

    def start(self):
        """Start the VS Code orchestrator."""
        with self.lock:
            if self.running:
                return
            self.running = True
            self._start_background_tasks()
            self._auto_start_instances()
            print("✅ Started VS Code orchestrator")

    def stop(self):
        """Stop the VS Code orchestrator."""
        with self.lock:
            self.running = False
            self._stop_all_instances()
            print("✅ Stopped VS Code orchestrator")

    # ── Account CRUD ────────────────────────────────────────

    def add_account(self, account: VSCodeAccount) -> bool:
        with self.lock:
            if account.account_id in self.accounts:
                print(f"⚠️  Account {account.account_id} already exists")
                return False
            self.accounts[account.account_id] = account
            print(f"✅ Added account: {account.account_id}")
            return True

    def remove_account(self, account_id: str) -> bool:
        with self.lock:
            if account_id not in self.accounts:
                print(f"❌ Account {account_id} not found")
                return False

            instances_to_remove = [
                iid for iid, cfg in self.instance_configs.items() if cfg.account_id == account_id
            ]
            for iid in instances_to_remove:
                self.remove_instance(iid)

            del self.accounts[account_id]
            print(f"✅ Removed account: {account_id}")
            return True

    # ── Instance CRUD ───────────────────────────────────────

    def create_instance(self, config: VSCodeInstanceConfig) -> bool:
        with self.lock:
            if config.instance_id in self.instance_configs:
                print(f"⚠️  Instance {config.instance_id} already exists")
                return False
            if config.account_id not in self.accounts:
                print(f"❌ Account {config.account_id} not found")
                return False

            if config.port == 0:
                config.port = self.port_allocator.allocate_port(config.instance_id)

            self.instance_configs[config.instance_id] = config

            if self.config["workspace_auto_create"]:
                Path(config.workspace_path).mkdir(parents=True, exist_ok=True)

            print(f"✅ Created instance: {config.instance_id}")
            return True

    def remove_instance(self, instance_id: str) -> bool:
        with self.lock:
            if instance_id not in self.instance_configs:
                print(f"❌ Instance {instance_id} not found")
                return False

            config = self.instance_configs[instance_id]

            sessions_to_remove = [
                sid for sid, s in self.active_sessions.items() if s.instance_id == instance_id
            ]
            for sid in sessions_to_remove:
                self.end_session(sid)

            self.instance_manager.stop_instance(instance_id)
            self.port_allocator.release_port(config.port)

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

            active_count = len(
                [s for s in self.active_sessions.values() if s.account_id == config.account_id]
            )
            if active_count >= account.max_concurrent_sessions:
                print(f"❌ Account {config.account_id} has reached max concurrent sessions")
                return None

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
                    "PROJECT_ROOT": str(self.project_root),
                },
                volumes={
                    str(self.project_root): "/home/coder/project",
                    config.workspace_path: f"/home/coder/workspace/{instance_id}",
                    str(self.config_file): "/home/coder/vscode.json:ro",
                },
                networks=["llx-network"],
            )

            if not self.instance_manager.create_instance(docker_config):
                print(f"❌ Failed to create Docker instance {instance_id}")
                return None
            if not self.instance_manager.start_instance(instance_id):
                print(f"❌ Failed to start Docker instance {instance_id}")
                return None
            if not self._wait_for_instance_ready(instance_id):
                print(f"❌ Instance {instance_id} failed to start properly")
                return None

            session_id = str(uuid.uuid4())
            session = VSCodeSession(
                session_id=session_id,
                instance_id=instance_id,
                account_id=config.account_id,
                started_at=datetime.now(),
                last_activity=datetime.now(),
                workspace_path=config.workspace_path,
            )
            self.active_sessions[session_id] = session

            self._configure_vscode_instance(instance_id, config)
            if config.auto_start_browser:
                self._start_browser_for_instance(instance_id)

            print(f"✅ Started instance {instance_id} with session {session_id}")
            return session_id

    def end_session(self, session_id: str) -> bool:
        with self.lock:
            if session_id not in self.active_sessions:
                print(f"❌ Session {session_id} not found")
                return False
            session = self.active_sessions[session_id]
            if self.config["browser_auto_close"] and session.browser_session:
                self._close_browser_session(session.browser_session)
            del self.active_sessions[session_id]
            print(f"✅ Ended session {session_id}")
            return True

    # ── Query methods ───────────────────────────────────────

    def get_available_instance(
        self, account_id: str = None, workspace_path: str = None
    ) -> Optional[str]:
        with self.lock:
            candidates = []
            for instance_id, config in self.instance_configs.items():
                if account_id and config.account_id != account_id:
                    continue
                if workspace_path and config.workspace_path != workspace_path:
                    continue
                status = self.instance_manager.get_instance_status(instance_id)
                if not status or status["status"] != "running":
                    continue
                account = self.accounts[config.account_id]
                active = len(
                    [s for s in self.active_sessions.values() if s.account_id == config.account_id]
                )
                if active >= account.max_concurrent_sessions:
                    continue
                candidates.append(instance_id)

            return candidates[0] if candidates else None

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id not in self.active_sessions:
            return None
        session = self.active_sessions[session_id]
        config = self.instance_configs[session.instance_id]
        account = self.accounts[session.account_id]
        inst_status = self.instance_manager.get_instance_status(session.instance_id)
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
            "instance_status": inst_status["status"] if inst_status else "unknown",
            "session_duration_minutes": (datetime.now() - session.started_at).total_seconds() / 60,
        }

    def list_accounts(self) -> List[Dict[str, Any]]:
        accounts = []
        for account in self.accounts.values():
            active = len(
                [s for s in self.active_sessions.values() if s.account_id == account.account_id]
            )
            accounts.append({
                "account_id": account.account_id,
                "name": account.name,
                "account_type": account.account_type.value,
                "email": account.email,
                "auth_method": account.auth_method,
                "max_concurrent_sessions": account.max_concurrent_sessions,
                "active_sessions": active,
                "auto_start": account.auto_start,
            })
        return accounts

    def list_instances(self, account_id: str = None) -> List[Dict[str, Any]]:
        instances = []
        for instance_id, config in self.instance_configs.items():
            if account_id and config.account_id != account_id:
                continue
            inst_status = self.instance_manager.get_instance_status(instance_id)
            active_sessions = [
                s for s in self.active_sessions.values() if s.instance_id == instance_id
            ]
            instances.append({
                "instance_id": instance_id,
                "account_id": config.account_id,
                "port": config.port,
                "workspace_path": config.workspace_path,
                "status": inst_status["status"] if inst_status else "unknown",
                "url": (
                    f"http://localhost:{config.port}"
                    if inst_status and inst_status["status"] == "running"
                    else None
                ),
                "active_sessions": len(active_sessions),
                "auto_start_browser": config.auto_start_browser,
            })
        return instances

    def list_sessions(self, account_id: str = None) -> List[Dict[str, Any]]:
        sessions = []
        for session in self.active_sessions.values():
            if account_id and session.account_id != account_id:
                continue
            sessions.append(self.get_session_status(session.session_id))
        return sessions

    # ── Internal helpers ────────────────────────────────────

    def _wait_for_instance_ready(self, instance_id: str, timeout: int = 30) -> bool:
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
        pass

    def _start_browser_for_instance(self, instance_id: str):
        config = self.instance_configs[instance_id]
        url = f"http://localhost:{config.port}"
        try:
            webbrowser.open(url)
            print(f"🌐 Opened browser for {instance_id}: {url}")
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")

    def _close_browser_session(self, browser_session: str):
        pass

    def _auto_start_instances(self):
        for account in self.accounts.values():
            if not account.auto_start:
                continue
            account_instances = [
                iid for iid, cfg in self.instance_configs.items() if cfg.account_id == account.account_id
            ]
            for iid in account_instances:
                inst_status = self.instance_manager.get_instance_status(iid)
                if not inst_status or inst_status["status"] != "running":
                    self.start_instance(iid)

    def _stop_all_instances(self):
        for instance_id in list(self.instance_configs.keys()):
            self.instance_manager.stop_instance(instance_id)

    # ── Background tasks ────────────────────────────────────

    def _start_background_tasks(self):
        threading.Thread(target=self._session_cleanup_worker, daemon=True).start()
        threading.Thread(target=self._config_save_worker, daemon=True).start()

    def _session_cleanup_worker(self):
        while self.running:
            try:
                time.sleep(self.config["session_cleanup_interval"])
                now = datetime.now()
                sessions_to_remove = []
                for session_id, session in self.active_sessions.items():
                    account = self.accounts[session.account_id]
                    age = (now - session.last_activity).total_seconds() / 60
                    if age > account.session_timeout_minutes:
                        sessions_to_remove.append(session_id)
                for sid in sessions_to_remove:
                    print(f"⏰ Session {sid} expired, ending...")
                    self.end_session(sid)
            except Exception as e:
                print(f"❌ Session cleanup worker error: {e}")

    def _config_save_worker(self):
        while self.running:
            try:
                time.sleep(300)
                self.save_config()
            except Exception as e:
                print(f"❌ Config save worker error: {e}")

    # ── Print summary ───────────────────────────────────────

    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("📝 VS Code Orchestrator Status")
        print("=============================")

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

        print("\n👥 Accounts:")
        for account in self.accounts.values():
            active = len(
                [s for s in self.active_sessions.values() if s.account_id == account.account_id]
            )
            print(
                f"  • {account.name} ({account.account_type.value}): "
                f"{active}/{account.max_concurrent_sessions} sessions"
            )

        print("\n🏗️  Instances:")
        for instance_id, config in self.instance_configs.items():
            inst_status = self.instance_manager.get_instance_status(instance_id)
            status = inst_status["status"] if inst_status else "unknown"
            sessions = len(
                [s for s in self.active_sessions.values() if s.instance_id == instance_id]
            )
            print(f"  • {instance_id}: {status} (port {config.port}, {sessions} sessions)")

        print()
