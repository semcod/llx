"""Instance data models."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class InstanceType(Enum):
    """Types of instances."""
    VSCODE = "vscode"
    AI_TOOLS = "ai_tools"
    LLM_PROXY = "llm_proxy"


class InstanceStatus(Enum):
    """Instance status."""
    CREATING = "creating"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class InstanceConfig:
    """Configuration for an instance."""
    instance_id: str
    instance_type: InstanceType
    account: str
    provider: str
    port: int
    image: str
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)
    auto_start: bool = True
    auto_restart: bool = True
    max_uptime_hours: int = 24
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstanceState:
    """Current state of an instance."""
    instance_id: str
    status: InstanceStatus = InstanceStatus.STOPPED
    container_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    last_used: datetime = field(default_factory=datetime.now)
    stopped_at: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_usage: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    health_check_url: Optional[str] = None
    health_status: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
