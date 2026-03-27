"""env_config — Environment configuration for preLLM.

Loads configuration from environment variables and .env files.
Provides defaults for small and large model configurations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from llx.prellm.models import LLMProviderConfig, PreLLMConfig


def _load_dotenv(env_path: Path | None = None) -> None:
    """Load environment variables from .env file if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        if env_path is None:
            env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass  # dotenv is optional


def get_env_config(
    env_path: Path | None = None,
    small_model: str | None = None,
    large_model: str | None = None,
) -> PreLLMConfig:
    """Load preLLM configuration from environment.
    
    Args:
        env_path: Path to .env file (optional).
        small_model: Override small model name (optional).
        large_model: Override large model name (optional).
    
    Returns:
        PreLLMConfig with settings from environment.
    """
    # Load .env file if available
    _load_dotenv(env_path)
    
    # Small model config
    small_model_name = small_model or os.getenv("PRELLM_SMALL_MODEL", "ollama/qwen2.5:3b")
    small_max_tokens = int(os.getenv("PRELLM_SMALL_MAX_TOKENS", "512"))
    small_temperature = float(os.getenv("PRELLM_SMALL_TEMPERATURE", "0.0"))
    
    small_config = LLMProviderConfig(
        model=small_model_name,
        max_tokens=small_max_tokens,
        temperature=small_temperature,
        max_retries=int(os.getenv("PRELLM_SMALL_MAX_RETRIES", "3")),
        timeout=int(os.getenv("PRELLM_SMALL_TIMEOUT", "30")),
    )
    
    # Large model config
    large_model_name = large_model or os.getenv("PRELLM_LARGE_MODEL", "gpt-4o-mini")
    large_max_tokens = int(os.getenv("PRELLM_LARGE_MAX_TOKENS", "2048"))
    large_temperature = float(os.getenv("PRELLM_LARGE_TEMPERATURE", "0.7"))
    
    large_config = LLMProviderConfig(
        model=large_model_name,
        max_tokens=large_max_tokens,
        temperature=large_temperature,
        max_retries=int(os.getenv("PRELLM_LARGE_MAX_RETRIES", "3")),
        timeout=int(os.getenv("PRELLM_LARGE_TIMEOUT", "60")),
    )
    
    return PreLLMConfig(
        small_model=small_config,
        large_model=large_config,
        max_retries=int(os.getenv("PRELLM_MAX_RETRIES", "3")),
    )


# Legacy alias for compatibility
EnvConfig = PreLLMConfig
