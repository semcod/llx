"""Queue data models."""

from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class QueueStatus(Enum):
    """Queue status."""
    IDLE = "idle"
    PROCESSING = "processing"
    FULL = "full"
    PAUSED = "paused"


class RequestPriority(Enum):
    """Request priority levels."""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class QueueRequest:
    """A request in the queue."""
    request_id: str
    provider: str
    account: str
    request_type: str
    priority: RequestPriority
    created_at: datetime
    tokens: int = 0
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """For priority queue ordering."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


@dataclass
class QueueConfig:
    """Configuration for a queue."""
    queue_id: str
    provider: str
    account: str
    max_size: int = 100
    max_concurrent: int = 5
    default_timeout: int = 300
    retry_policy: str = "exponential_backoff"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueueState:
    """Current state of a queue."""
    queue_id: str
    status: QueueStatus
    created_at: datetime
    last_processed: Optional[datetime] = None
    total_requests: int = 0
    processed_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    current_processing: int = 0
    average_wait_time: float = 0.0
    average_processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
