"""VS Code orchestrator data models."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


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
    email: Optional[str] = None
    auth_method: str = "password"
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
    user_id: Optional[str] = None
    browser_session: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    workspace_path: str = ""
    active_files: List[str] = field(default_factory=list)
    ai_tools_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
