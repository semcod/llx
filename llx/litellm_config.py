"""LiteLLM Configuration Management

Loads model configurations from litellm-config.yaml
and provides them to the LiteLLM proxy server.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class LiteLLMModelConfig:
    """Configuration for a single LiteLLM model."""
    model_name: str
    litellm_params: Dict[str, Any]
    tags: List[str]
    tier: str
    provider: str
    context_window: int
    pricing: Dict[str, float]


@dataclass
class LiteLLMConfig:
    """Complete LiteLLM configuration."""
    model_list: List[LiteLLMModelConfig]
    model_aliases: Dict[str, str]
    general_settings: Dict[str, Any]
    budget_limits: Dict[str, Any]
    quality_thresholds: Dict[str, Any]
    fallback_order: List[Dict[str, Any]]

    @classmethod
    def load(cls, project_path: str | Path = ".") -> "LiteLLMConfig":
        """Load LiteLLM configuration from litellm-config.yaml."""
        root = Path(project_path).resolve()
        config_path = root / "litellm-config.yaml"
        
        if not config_path.exists():
            # Return default configuration if file doesn't exist
            return cls._default_config()
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            return cls._default_config()
        
        # Parse model list
        model_list = []
        for model_data in data.get("model_list", []):
            model = LiteLLMModelConfig(
                model_name=model_data["model_name"],
                litellm_params=model_data["litellm_params"],
                tags=model_data.get("tags", []),
                tier=model_data.get("tier", "balanced"),
                provider=model_data.get("provider", "unknown"),
                context_window=model_data.get("context_window", 200000),
                pricing=model_data.get("pricing", {"input_per_token": 0.0, "output_per_token": 0.0}),
            )
            model_list.append(model)
        
        return cls(
            model_list=model_list,
            model_aliases=data.get("model_aliases", {}),
            general_settings=data.get("general_settings", {}),
            budget_limits=data.get("budget_limits", {}),
            quality_thresholds=data.get("quality_thresholds", {}),
            fallback_order=data.get("fallback_order", []),
        )
    
    @classmethod
    def _default_config(cls) -> "LiteLLMConfig":
        """Return default configuration when no config file is found."""
        return cls(
            model_list=[],
            model_aliases={},
            general_settings={},
            budget_limits={},
            quality_thresholds={},
            fallback_order=[],
        )
    
    def get_model_config(self, model_name: str) -> Optional[LiteLLMModelConfig]:
        """Get configuration for a specific model."""
        for model in self.model_list:
            if model.model_name == model_name:
                return model
        return None
    
    def get_models_by_tag(self, tag: str) -> List[LiteLLMModelConfig]:
        """Get all models with a specific tag."""
        return [model for model in self.model_list if tag in model.tags]
    
    def get_models_by_provider(self, provider: str) -> List[LiteLLMModelConfig]:
        """Get all models from a specific provider."""
        return [model for model in self.model_list if model.provider == provider]
    
    def get_models_by_tier(self, tier: str) -> List[LiteLLMModelConfig]:
        """Get all models in a specific tier."""
        return [model for model in self.model_list if model.tier == tier]
    
    def resolve_alias(self, alias: str) -> Optional[str]:
        """Resolve model alias to actual model name."""
        return self.model_aliases.get(alias)
    
    def to_llx_models(self) -> Dict[str, Any]:
        """Convert LiteLLM models to llx ModelConfig format."""
        # Import here to avoid circular import
        from .config import ModelConfig
        
        models = {}
        
        for model in self.model_list:
            llx_model = ModelConfig(
                name=model.tier,
                provider=model.provider,
                model_id=model.model_name,
                max_context=model.context_window,
                cost_per_1k_input=model.pricing.get("input_per_token", 0.0) * 1000,
                cost_per_1k_output=model.pricing.get("output_per_token", 0.0) * 1000,
                tags=model.tags,
            )
            models[model.tier] = llx_model
        
        return models
    
    def get_proxy_config(self) -> Dict[str, Any]:
        """Get configuration for LiteLLM proxy server."""
        return {
            "model_list": [
                {
                    "model_name": model.model_name,
                    "litellm_params": model.litellm_params,
                }
                for model in self.model_list
            ],
            "model_aliases": self.model_aliases,
            "general_settings": self.general_settings,
            "budget_limits": self.budget_limits,
        }


def load_litellm_config(project_path: str | Path = ".") -> LiteLLMConfig:
    """Convenience function to load LiteLLM configuration."""
    return LiteLLMConfig.load(project_path)
