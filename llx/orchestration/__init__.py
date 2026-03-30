"""
llx Orchestration Package
Multi-instance LLM and VS Code orchestration with intelligent routing and rate limiting.

Sub-packages
~~~~~~~~~~~~
- session/    – session lifecycle & scheduling
- instances/  – Docker instance management
- ratelimit/  – per-provider rate limiting
- queue/      – prioritised request queues
- routing/    – intelligent request routing
- vscode/     – VS Code instance orchestration
- llm/        – LLM provider orchestration
"""

# Re-export main classes from sub-packages for backward compatibility
from .session import SessionManager
from .instances import InstanceManager
from .ratelimit import RateLimiter
from .queue import QueueManager
from .routing import RoutingEngine
from .vscode import VSCodeOrchestrator
from .llm import LLMOrchestrator

__all__ = [
    "SessionManager",
    "InstanceManager",
    "RateLimiter",
    "QueueManager",
    "RoutingEngine",
    "VSCodeOrchestrator",
    "LLMOrchestrator",
]

__version__ = "0.1.47"
