"""Session data models — enums and dataclasses."""

from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class SessionType(Enum):
    """Types of sessions."""
    LLM = "llm"
    VSCODE = "vscode"
    AI_TOOLS = "ai_tools"


class SessionStatus(Enum):
    """Session status."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class SessionConfig:
    """Configuration for a session."""
    session_id: str
    session_type: SessionType
    provider: str
    model: str
    account: str
    max_requests_per_hour: int = 100
    max_tokens_per_hour: int = 100000
    cooldown_minutes: int = 60
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """Current state of a session."""
    session_id: str
    status: SessionStatus
    created_at: datetime
    last_used: datetime
    requests_count: int = 0
    tokens_used: int = 0
    errors_count: int = 0
    rate_limit_until: Optional[datetime] = None
    current_request_id: Optional[str] = None
    queue_position: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
