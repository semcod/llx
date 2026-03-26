"""Configuration management for llx.

Loads from (priority order):
1. Environment variables (LLX_*)
2. llx.toml in project root
3. pyproject.toml [tool.llx]
4. Built-in defaults

Lesson from preLLM: configuration was embedded in core.py (893L god module).
Here it's a clean standalone module with typed dataclasses.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[import]
    except ImportError:
        # pip install tomli for Python < 3.11
        import tomli as tomllib  # type: ignore[import,no-redef]

import yaml

from .litellm_config import LiteLLMConfig


@dataclass
class ModelConfig:
    """Configuration for a single model tier."""

    name: str
    provider: str  # anthropic, openai, ollama, openrouter, vllm, litellm, google
    model_id: str  # e.g. "claude-opus-4-20250514", "ollama/qwen2.5-coder:7b"
    max_context: int = 200_000
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    tags: list[str] = field(default_factory=list)  # Model capabilities: FREE, FAST, PROGRAMMING, etc.


@dataclass
class TierThresholds:
    """Thresholds that determine which model tier to use.

    Based on real project metrics from code2llm analysis.
    Not abstract quality scores — concrete numbers.
    """

    # File count
    files_premium: int = 50
    files_balanced: int = 10
    files_cheap: int = 3

    # Total lines
    lines_premium: int = 20_000
    lines_balanced: int = 5_000
    lines_cheap: int = 500

    # Cyclomatic complexity average
    cc_premium: float = 6.0
    cc_balanced: float = 4.0
    cc_cheap: float = 2.0

    # Coupling / fan-out
    coupling_premium: int = 30
    coupling_balanced: int = 10

    # Duplication groups (from redup)
    dup_groups_premium: int = 15
    dup_groups_balanced: int = 5

    # Max single-function CC
    max_cc_premium: int = 25
    max_cc_balanced: int = 15


DEFAULT_MODELS: dict[str, ModelConfig] = {
    "premium": ModelConfig(
        name="premium", provider="anthropic",
        model_id="claude-opus-4-20250514",
        max_context=200_000, cost_per_1k_input=0.015, cost_per_1k_output=0.075,
        tags=["EXPENSIVE", "HIGH_QUALITY", "REFACTORING", "ARCHITECTURE", "COMPLEX_REASONING", "SLOW"]
    ),
    "balanced": ModelConfig(
        name="balanced", provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        max_context=200_000, cost_per_1k_input=0.003, cost_per_1k_output=0.015,
        tags=["PROGRAMMING", "GENERATING", "ANALYSIS", "DEBUGGING", "FAST", "RELIABLE"]
    ),
    "cheap": ModelConfig(
        name="cheap", provider="anthropic",
        model_id="claude-haiku-4-5-20251001",
        max_context=200_000, cost_per_1k_input=0.0008, cost_per_1k_output=0.004,
        tags=["FAST", "CHEAP", "PROGRAMMING", "QUICK_TASKS", "DOCUMENTATION", "CODE_COMPLETION"]
    ),
    "free": ModelConfig(
        name="free", provider="google",
        model_id="gemini/gemini-2.5-pro",
        max_context=1_000_000, cost_per_1k_input=0.0, cost_per_1k_output=0.0,
        tags=["FREE", "LARGE_CONTEXT", "GENERAL_PURPOSE", "FAST", "COST_EFFECTIVE"]
    ),
    "local": ModelConfig(
        name="local", provider="ollama",
        model_id="ollama/qwen2.5-coder:7b",
        max_context=32_000, cost_per_1k_input=0.0, cost_per_1k_output=0.0,
        tags=["FREE", "OFFLINE", "PRIVATE", "PROGRAMMING", "CODE_SPECIALIZED", "FAST"]
    ),
    "openrouter": ModelConfig(
        name="openrouter", provider="openrouter",
        model_id="openrouter/deepseek/deepseek-chat-v3-0324",
        max_context=128_000, cost_per_1k_input=0.0005, cost_per_1k_output=0.002,
        tags=["CHEAP", "FAST", "PROGRAMMING", "REASONING", "COST_EFFECTIVE", "BACKUP_OPTION"]
    ),
}


@dataclass
class ProxyConfig:
    """LiteLLM proxy settings."""

    host: str = "0.0.0.0"
    port: int = 4000
    master_key: str = "sk-proxy-local-dev"
    redis_url: str | None = None
    enable_cache: bool = True
    budget_limit: float | None = None


@dataclass
class LlxConfig:
    """Root configuration for llx."""

    models: dict[str, ModelConfig] = field(default_factory=lambda: dict(DEFAULT_MODELS))
    thresholds: TierThresholds = field(default_factory=TierThresholds)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    litellm_base_url: str = "http://localhost:4000"
    default_tier: str = "balanced"
    enable_code2llm: bool = True
    enable_redup: bool = True
    enable_vallm: bool = True
    verbose: bool = False
    litellm_config: LiteLLMConfig = field(default_factory=LiteLLMConfig._default_config)

    @classmethod
    def load(cls, project_path: str | Path = ".") -> LlxConfig:
        """Load configuration from llx.yaml, llx.toml, or pyproject.toml."""
        root = Path(project_path).resolve()
        config = cls()

        # Load LiteLLM configuration
        config.litellm_config = LiteLLMConfig.load(project_path)

        # Try llx.yaml first (new standard)
        yaml_path = root / "llx.yaml"
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                config = _apply_yaml(config, data)
                # Update models from LiteLLM config if available
                if config.litellm_config.model_list:
                    litellm_models = config.litellm_config.to_llx_models()
                    config.models.update(litellm_models)
                return _apply_env(config)

        # Try llx.toml (legacy)
        for name in ("llx.toml", ".llx.toml"):
            toml_path = root / name
            if toml_path.exists():
                with open(toml_path, "rb") as f:
                    data = tomllib.load(f)
                config = _apply_toml(config, data)
                return _apply_env(config)

        # Fallback to pyproject.toml [tool.llx]
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            tool_llx = data.get("tool", {}).get("llx", {})
            if tool_llx:
                config = _apply_toml(config, tool_llx)

        return _apply_env(config)


def _apply_toml(config: LlxConfig, data: dict[str, Any]) -> LlxConfig:
    """Apply TOML data to config."""
    for key in ("litellm_base_url", "default_tier", "verbose"):
        if key in data:
            setattr(config, key, data[key])

    for key, val in data.get("thresholds", {}).items():
        if hasattr(config.thresholds, key):
            setattr(config.thresholds, key, val)

    for tier_name, mdata in data.get("models", {}).items():
        if isinstance(mdata, dict):
            config.models[tier_name] = ModelConfig(
                name=tier_name,
                provider=mdata.get("provider", "litellm"),
                model_id=mdata.get("model_id", mdata.get("model", "")),
                max_context=mdata.get("max_context", 200_000),
                cost_per_1k_input=mdata.get("cost_per_1k_input", 0.0),
                cost_per_1k_output=mdata.get("cost_per_1k_output", 0.0),
            )

    proxy = data.get("proxy", {})
    for key in ("port", "redis_url", "budget_limit", "host"):
        if key in proxy:
            setattr(config.proxy, key, proxy[key])

    return config


def _apply_yaml_thresholds(config: LlxConfig, thresholds: dict) -> None:
    """Apply threshold overrides from YAML."""
    if "files" in thresholds:
        files = thresholds["files"]
        config.thresholds.files_premium = files.get("premium", config.thresholds.files_premium)
        config.thresholds.files_balanced = files.get("balanced", config.thresholds.files_balanced)
        config.thresholds.files_cheap = files.get("cheap", config.thresholds.files_cheap)
    if "lines" in thresholds:
        lines = thresholds["lines"]
        config.thresholds.lines_premium = lines.get("premium", config.thresholds.lines_premium)
        config.thresholds.lines_balanced = lines.get("balanced", config.thresholds.lines_balanced)
        config.thresholds.lines_cheap = lines.get("cheap", config.thresholds.lines_cheap)
    if "complexity" in thresholds:
        complexity = thresholds["complexity"]
        config.thresholds.cc_premium = complexity.get("premium", config.thresholds.cc_premium)
        config.thresholds.cc_balanced = complexity.get("balanced", config.thresholds.cc_balanced)
        config.thresholds.cc_cheap = complexity.get("cheap", config.thresholds.cc_cheap)


def _apply_yaml_models(config: LlxConfig, models: dict) -> None:
    """Apply model definitions from YAML."""
    for tier_name, mdata in models.items():
        if isinstance(mdata, dict):
            config.models[tier_name] = ModelConfig(
                name=tier_name,
                provider=mdata.get("provider", "litellm"),
                model_id=mdata.get("model_id", mdata.get("model", "")),
                max_context=mdata.get("max_context", 200_000),
                cost_per_1k_input=mdata.get("cost_per_1k_input", 0.0),
                cost_per_1k_output=mdata.get("cost_per_1k_output", 0.0),
            )


def _apply_yaml_proxy(config: LlxConfig, proxy: dict) -> None:
    """Apply proxy settings from YAML."""
    if "server" in proxy:
        server = proxy["server"]
        config.proxy.host = server.get("host", config.proxy.host)
        config.proxy.port = server.get("port", config.proxy.port)
    if "auth" in proxy:
        auth = proxy["auth"]
        config.proxy.master_key = auth.get("master_key", config.proxy.master_key)
    if "cache" in proxy:
        cache = proxy["cache"]
        config.proxy.redis_url = cache.get("redis_url", config.proxy.redis_url)


def _apply_yaml(config: LlxConfig, data: dict[str, Any]) -> LlxConfig:
    """Apply YAML data to config."""
    # Apply basic settings
    if "selection" in data:
        selection = data["selection"]
        if "default_tier" in selection:
            config.default_tier = selection["default_tier"]
        if "context" in selection:
            context = selection["context"]
            config.litellm_base_url = context.get("base_url", config.litellm_base_url)
    
    # Apply proxy settings
    if "proxy" in data:
        _apply_yaml_proxy(config, data["proxy"])
    
    # Apply analysis settings
    if "analysis" in data:
        analysis = data["analysis"]
        if "thresholds" in analysis:
            _apply_yaml_thresholds(config, analysis["thresholds"])
    
    # Apply budget settings
    if "budget" in data:
        budget = data["budget"]
        if "limits" in budget:
            limits = budget["limits"]
            config.proxy.budget_limit = limits.get("monthly", config.proxy.budget_limit)
    
    # Apply logging settings
    if "logging" in data:
        logging = data["logging"]
        if "level" in logging:
            config.verbose = logging["level"].upper() == "DEBUG"
    
    # Apply development settings
    if "development" in data:
        dev = data["development"]
        if "debug" in dev:
            config.verbose = dev["debug"]
    
    return config


def _apply_env(config: LlxConfig) -> LlxConfig:
    """Apply LLX_* environment variable overrides."""
    if url := os.environ.get("LLX_LITELLM_URL"):
        config.litellm_base_url = url
    if tier := os.environ.get("LLX_DEFAULT_TIER"):
        config.default_tier = tier
    if host := os.environ.get("LLX_PROXY_HOST"):
        config.proxy.host = host
    if port := os.environ.get("LLX_PROXY_PORT"):
        config.proxy.port = int(port)
    if master_key := os.environ.get("LLX_PROXY_MASTER_KEY"):
        config.proxy.master_key = master_key
    if os.environ.get("LLX_VERBOSE", "").lower() in ("1", "true", "yes"):
        config.verbose = True
    return config
