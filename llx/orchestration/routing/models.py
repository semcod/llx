"""Routing engine data models."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class RoutingStrategy(Enum):
    """Routing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PRIORITY_BASED = "priority_based"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    AVAILABILITY_FIRST = "availability_first"


class ResourceType(Enum):
    """Types of resources to route to."""
    LLM = "llm"
    VSCODE = "vscode"
    AI_TOOLS = "ai_tools"


class RequestPriority(Enum):
    """Request priority levels (mirrors queue.models)."""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class RoutingRequest:
    """A request to be routed."""
    request_id: str
    resource_type: ResourceType
    provider: Optional[str]
    account: Optional[str]
    model: Optional[str]
    priority: RequestPriority
    strategy: RoutingStrategy
    requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """A routing decision."""
    request_id: str
    resource_type: ResourceType
    selected_resource: str
    provider: str
    account: str
    model: str
    strategy_used: RoutingStrategy
    confidence: float
    estimated_wait_time: float
    estimated_cost: float
    reasoning: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingMetrics:
    """Metrics for routing performance."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_routing_time: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    strategy_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    provider_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
