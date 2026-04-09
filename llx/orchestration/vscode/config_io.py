"""Persistence helpers for VS Code orchestration config."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

from .._utils import save_json
from .models import VSCodeAccount, VSCodeAccountType, VSCodeInstanceConfig, VSCodeSession


def load_vscode_config(orchestrator) -> bool:
    """Load VS Code orchestration configuration into an orchestrator instance."""
    try:
        if orchestrator.config_file.exists():
            with open(orchestrator.config_file, "r") as f:
                data = json.load(f)

            orchestrator.config.update(data.get("config", {}))

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
                orchestrator.accounts[account.account_id] = account

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
                orchestrator.instance_configs[cfg.instance_id] = cfg

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
                orchestrator.active_sessions[session.session_id] = session

            print(
                f"✅ Loaded VS Code orchestration config: "
                f"{len(orchestrator.accounts)} accounts, {len(orchestrator.instance_configs)} instances"
            )
            return True
        else:
            print("📝 No existing VS Code config found, starting fresh")
            orchestrator._create_default_config()
            return True
    except Exception as e:
        print(f"❌ Error loading VS Code config: {e}")
        return False


def save_vscode_config(orchestrator) -> bool:
    """Save VS Code orchestration configuration from an orchestrator instance."""
    try:
        data: Dict[str, Any] = {
            "config": orchestrator.config,
            "accounts": [],
            "instances": [],
            "sessions": [],
        }

        for account in orchestrator.accounts.values():
            data["accounts"].append(
                {
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
                }
            )

        for cfg in orchestrator.instance_configs.values():
            data["instances"].append(
                {
                    "instance_id": cfg.instance_id,
                    "account_id": cfg.account_id,
                    "port": cfg.port,
                    "workspace_path": cfg.workspace_path,
                    "extensions": cfg.extensions,
                    "settings": cfg.settings,
                    "environment": cfg.environment,
                    "auto_start_browser": cfg.auto_start_browser,
                    "metadata": cfg.metadata,
                }
            )

        for session in orchestrator.active_sessions.values():
            data["sessions"].append(
                {
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
                }
            )

        return save_json(orchestrator.config_file, data, "VS Code config")
    except Exception as e:
        print(f"❌ Error saving VS Code config: {e}")
        return False
