"""Model filtering and selection utilities for LLX."""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ModelProvider(Enum):
    """Available model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LOCAL = "local"

class ModelTier(Enum):
    """Model pricing tiers."""
    FREE = "free"
    CHEAP = "cheap"
    BALANCED = "balanced"
    PREMIUM = "premium"


_PROVIDER_PREFIXES = {
    ModelProvider.OLLAMA: ("ollama/",),
    ModelProvider.LOCAL: ("ollama/",),
    ModelProvider.OPENROUTER: ("openrouter/",),
    ModelProvider.OPENAI: ("openai/",),
    ModelProvider.ANTHROPIC: ("anthropic/",),
}

@dataclass
class ModelFilter:
    """Filter criteria for model selection."""
    provider: Optional[ModelProvider] = None
    tier: Optional[ModelTier] = None
    max_cost_per_input: Optional[float] = None
    max_cost_per_output: Optional[float] = None
    requires_api_key: Optional[bool] = None
    local_only: bool = False
    cloud_only: bool = False
    
    def matches(self, model_id: str, model_info: Dict[str, Any]) -> bool:
        """Check if model matches filter criteria."""
        # Check provider
        if not self._matches_provider(model_id):
            return False
        
        # Check tier
        if not self._matches_tier(model_info):
            return False
        
        # Check API key requirement
        if not self._matches_api_key_requirement(model_id):
            return False
        
        # Check local/cloud preference
        if not self._matches_scope(model_id):
            return False
        
        return True

    def _matches_provider(self, model_id: str) -> bool:
        if not self.provider:
            return True

        prefixes = _PROVIDER_PREFIXES.get(self.provider, ())
        return any(model_id.startswith(prefix) for prefix in prefixes)

    def _matches_tier(self, model_info: Dict[str, Any]) -> bool:
        if not self.tier:
            return True

        return model_info.get("tier") == self.tier.value

    def _matches_api_key_requirement(self, model_id: str) -> bool:
        if self.requires_api_key is None:
            return True

        has_api_key = self._has_api_key(model_id)
        return has_api_key if self.requires_api_key else not has_api_key

    def _matches_scope(self, model_id: str) -> bool:
        if self.local_only and not model_id.startswith("ollama/"):
            return False
        if self.cloud_only and model_id.startswith("ollama/"):
            return False

        return True
    
    def _has_api_key(self, model_id: str) -> bool:
        """Check if API key is available for model."""
        if model_id.startswith("openai/"):
            return bool(os.getenv("OPENAI_API_KEY"))
        elif model_id.startswith("anthropic/"):
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        elif model_id.startswith("openrouter/"):
            return bool(os.getenv("OPENROUTER_API_KEY"))
        elif model_id.startswith("ollama/"):
            return False  # Local models don't need API keys
        return False


class ModelSelector:
    """Select models based on filters and preferences."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize model selector."""
        from llx.config import LlxConfig
        self.config = LlxConfig.load(config_path or ".")
        self._model_registry = self._build_model_registry()
    
    def _build_model_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build registry of available models with metadata."""
        registry = {}
        
        # Add models from config
        for tier_name, model in self.config.models.items():
            registry[model.model_id] = {
                "tier": tier_name,
                "provider": self._get_provider(model.model_id),
                "cost_per_input": getattr(model, "cost_per_input", None),
                "cost_per_output": getattr(model, "cost_per_output", None),
            }
        
        # Add known free models (only verified working ones)
        free_models = {
            "openrouter/deepseek/deepseek-chat-v3-0324": {
                "tier": "free",
                "provider": "openrouter",
                "cost_per_input": 0.0,
                "cost_per_output": 0.0,
            },
            "openrouter/meta-llama/llama-3.2-3b-instruct:free": {
                "tier": "free",
                "provider": "openrouter",
                "cost_per_input": 0.0,
                "cost_per_output": 0.0,
            },
            "openrouter/mistral/mistral-7b-instruct:free": {
                "tier": "free",
                "provider": "openrouter",
                "cost_per_input": 0.0,
                "cost_per_output": 0.0,
            },
            "ollama/qwen2.5-coder:7b": {
                "tier": "free",
                "provider": "ollama",
                "cost_per_input": 0.0,
                "cost_per_output": 0.0,
            },
            "ollama/llama3.2:3b": {
                "tier": "free",
                "provider": "ollama",
                "cost_per_input": 0.0,
                "cost_per_output": 0.0,
            },
            "ollama/deepseek-coder:6.7b": {
                "tier": "free",
                "provider": "ollama",
                "cost_per_input": 0.0,
                "cost_per_output": 0.0,
            }
        }
        
        registry.update(free_models)
        return registry
    
    def _get_provider(self, model_id: str) -> str:
        """Extract provider from model ID."""
        if "/" in model_id:
            return model_id.split("/")[0]
        return "unknown"
    
    def select_model(self, filter: ModelFilter) -> Optional[str]:
        """Select first model matching the filter."""
        for model_id, model_info in self._model_registry.items():
            if filter.matches(model_id, model_info):
                return model_id
        return None
    
    def list_models(self, filter: Optional[ModelFilter] = None) -> List[Dict[str, Any]]:
        """List all models matching the filter."""
        models = []
        for model_id, model_info in self._model_registry.items():
            if not filter or filter.matches(model_id, model_info):
                models.append({
                    "id": model_id,
                    "provider": model_info["provider"],
                    "tier": model_info["tier"],
                    "cost_per_input": model_info.get("cost_per_input"),
                    "cost_per_output": model_info.get("cost_per_output"),
                    "has_api_key": self._check_api_key(model_id),
                })
        return models
    
    def _check_api_key(self, model_id: str) -> bool:
        """Check if API key is available."""
        if model_id.startswith("openai/"):
            return bool(os.getenv("OPENAI_API_KEY"))
        elif model_id.startswith("anthropic/"):
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        elif model_id.startswith("openrouter/"):
            return bool(os.getenv("OPENROUTER_API_KEY"))
        return False


# Predefined filters
FREE_FILTER = ModelFilter(tier=ModelTier.FREE)
LOCAL_FILTER = ModelFilter(local_only=True)
CLOUD_FREE_FILTER = ModelFilter(tier=ModelTier.FREE, cloud_only=True)
OPENROUTER_FREE_FILTER = ModelFilter(
    provider=ModelProvider.OPENROUTER,
    tier=ModelTier.FREE
)
CHEAP_FILTER = ModelFilter(tier=ModelTier.CHEAP)
BALANCED_FILTER = ModelFilter(tier=ModelTier.BALANCED)
