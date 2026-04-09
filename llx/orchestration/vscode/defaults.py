"""Default configuration helpers for VS Code orchestration."""

from __future__ import annotations

from .models import VSCodeAccount, VSCodeAccountType


def create_default_vscode_config(orchestrator) -> None:
    """Populate an orchestrator with default VS Code configuration."""
    local_account = VSCodeAccount(
        account_id="local-default",
        account_type=VSCodeAccountType.LOCAL,
        name="Local Development",
        email=None,
        auth_method="local",
        auth_config={},
        max_concurrent_sessions=1,
        session_timeout_minutes=120,
        auto_start=True,
        metadata={"default": True},
    )
    orchestrator.accounts[local_account.account_id] = local_account
