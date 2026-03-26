"""Rate limiter data models."""

from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class LimitType(Enum):
    """Types of rate limits."""
    REQUESTS_PER_HOUR = "requests_per_hour"
    TOKENS_PER_HOUR = "tokens_per_hour"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    CONCURRENT_REQUESTS = "concurrent_requests"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    provider: str
    account: str
    limits: Dict[LimitType, int] = field(default_factory=dict)
    cooldown_minutes: int = 60
    penalty_multiplier: float = 1.5
    max_penalties: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitState:
    """Current state of rate limiting."""
    provider: str
    account: str
    current_usage: Dict[LimitType, int] = field(default_factory=dict)
    last_reset_times: Dict[LimitType, datetime] = field(default_factory=dict)
    cooldown_until: Optional[datetime] = None
    penalty_count: int = 0
    last_request_time: Optional[datetime] = None
    concurrent_requests: int = 0
    total_requests: int = 0
    rejected_requests: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
