"""
LLM orchestration data models.
Enums and dataclasses for providers, models, requests, and responses.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class LLMProviderType(Enum):
    """Types of LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"


class ModelCapability(Enum):
    """Model capabilities."""
    CODE_GENERATION = "code_generation"
    TEXT_GENERATION = "text_generation"
    REASONING = "reasoning"
    MATH = "math"
    MULTIMODAL = "multimodal"
    FUNCTION_CALLING = "function_calling"
    CHAT = "chat"
    COMPLETION = "completion"


@dataclass
class LLMModel:
    """LLM model configuration."""
    model_id: str
    provider: LLMProviderType
    name: str
    display_name: str
    capabilities: List[ModelCapability]
    context_window: int
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    average_latency_ms: float
    quality_score: float  # 0.0-1.0
    reliability_score: float  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMProvider:
    """LLM provider configuration."""
    provider_id: str
    provider_type: LLMProviderType
    name: str
    api_base: Optional[str]
    auth_method: str  # "api_key", "oauth", "none"
    auth_config: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, LLMModel] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    health_check_endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    """LLM request."""
    request_id: str
    provider: str
    model: str
    messages: List[Dict[str, Any]]
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    priority: Any = None  # RequestPriority — late-bound to avoid circular import
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM response."""
    request_id: str
    provider: str
    model: str
    content: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
