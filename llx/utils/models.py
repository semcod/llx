"""Model selection utilities."""

from __future__ import annotations

from llx.config import LlxConfig


def _select_small_model(config: LlxConfig) -> str:
    """Select a small/fast model for preLLM preprocessing.
    
    Args:
        config: LLX configuration with model definitions.
    
    Returns:
        Model ID string for a small/cheap model.
    """
    # Try models in order of preference for small/fast tasks
    preferred_order = ["cheap", "local", "free", "balanced"]
    
    for tier in preferred_order:
        if tier in config.models:
            return config.models[tier].model_id
    
    # Fallback: return the first available model
    if config.models:
        return next(iter(config.models.values())).model_id
    
    # Last resort fallback
    return "ollama/qwen2.5-coder:7b"
