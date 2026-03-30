"""Convenience synchronous LLM helpers for simple completion and fix workflows.

This module mirrors the historical ``pyqual.llm`` API so callers can migrate
without changing their import paths all at once.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

DEFAULT_MAX_TOKENS = 2000
DEFAULT_MODEL = "openrouter/qwen/qwen3-coder-next"

try:
    from litellm import completion
except ImportError:  # pragma: no cover - optional dependency
    completion = None


def _load_dotenv_fallback(env_path: Path) -> None:
    """Load a minimal ``.env`` file without requiring python-dotenv."""
    try:
        lines = env_path.read_text().splitlines()
    except OSError:
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _ensure_dotenv_loaded() -> None:
    """Load ``.env`` from the current working directory if present."""
    env_path = Path(".env")
    if not env_path.exists():
        return

    if load_dotenv is not None:
        load_dotenv(env_path)
    else:
        _load_dotenv_fallback(env_path)


def get_llm_model() -> str:
    """Get the default LLM model from environment or fallback settings."""
    _ensure_dotenv_loaded()
    model = os.getenv("LLM_MODEL") or os.getenv("PFIX_MODEL")
    if model:
        logger.debug("LLM_MODEL from .env: %s", model)
        return model
    logger.info(
        "LLM_MODEL not set in .env — using config default: %s",
        DEFAULT_MODEL,
    )
    return DEFAULT_MODEL


def get_api_key() -> str | None:
    """Get the OpenRouter API key from environment."""
    _ensure_dotenv_loaded()
    return os.getenv("OPENROUTER_API_KEY")


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    model: str
    usage: dict[str, Any] | None = None
    cost: float | None = None


class LLM:
    """Synchronous LiteLLM wrapper with .env configuration."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or get_llm_model()
        self.api_key = api_key or get_api_key()

        if completion is None:
            raise ImportError("litellm is required. Install with: pip install llx[litellm]")

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a completion request to the configured LLM."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = completion(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
            **kwargs,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage.dict() if response.usage else None
        cost = response._hidden_params.get("response_cost") if hasattr(response, "_hidden_params") else None

        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            cost=cost,
        )

    def fix_code(
        self,
        code: str,
        error: str | None = None,
        context: str | None = None,
    ) -> LLMResponse:
        """Generate a code fix using the configured LLM."""
        system = "You are a helpful coding assistant. Provide fixed code only, no explanations."

        prompt_parts = ["Fix the following code:"]
        if error:
            prompt_parts.append(f"\nError: {error}")
        if context:
            prompt_parts.append(f"\nContext: {context}")
        prompt_parts.append(f"\n\n```\n{code}\n```\n\nProvide the fixed code:")

        prompt = "\n".join(prompt_parts)
        return self.complete(prompt, system=system, temperature=0.3)


def get_llm(model: str | None = None) -> LLM:
    """Get a configured LLM instance."""
    return LLM(model=model)


__all__ = [
    "DEFAULT_MAX_TOKENS",
    "LLM",
    "LLMResponse",
    "get_api_key",
    "get_llm",
    "get_llm_model",
]
