"""LiteLLM client wrapper for codr.

Supports two modes:
1. Proxy mode: Route through LiteLLM proxy at localhost:4000
2. Direct mode: Use litellm.completion() directly

Both modes support the OpenAI-compatible API format.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterator

import httpx

from llx.config import LlxConfig, ModelConfig
from llx.analysis.collector import ProjectMetrics


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str  # system, user, assistant
    content: str


@dataclass
class ChatResponse:
    """Response from LLM completion."""

    content: str
    model: str
    usage: dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    raw: dict[str, Any] | None = None

    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)


class LlxClient:
    """LLM client that routes through LiteLLM proxy or calls directly.

    Usage:
        client = LlxClient(config)
        response = client.chat(
            model="anthropic/claude-sonnet-4-20250514",
            messages=[ChatMessage(role="user", content="Explain this code")],
        )
    """

    def __init__(self, config: LlxConfig | None = None):
        self.config = config or LlxConfig()
        headers = {"Content-Type": "application/json"}
        # Add auth header for proxy
        if self.config.proxy.master_key:
            headers["Authorization"] = f"Bearer {self.config.proxy.master_key}"
        
        self._http = httpx.Client(
            base_url=self.config.litellm_base_url,
            timeout=120.0,
            headers=headers,
        )

    def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        system: str | None = None,
        metrics: ProjectMetrics | None = None,
    ) -> ChatResponse:
        """Send a chat completion request.

        Args:
            messages: Chat messages.
            model: Model identifier (e.g. "anthropic/claude-sonnet-4-20250514").
                   If None, uses config default.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
            system: System prompt (prepended as system message).
            metrics: Project metrics for proxym-aware routing (X-Task-Tier header).

        Returns:
            ChatResponse with content and usage stats.
        """
        if model is None:
            default = self.config.models.get(self.config.default_tier)
            model = default.model_id if default else "anthropic/claude-sonnet-4-20250514"

        payload = self._build_payload(messages, model, temperature, max_tokens, system)
        extra_headers = self._metrics_headers(metrics) if metrics else {}

        try:
            response = self._http.post("/v1/chat/completions", json=payload, headers=extra_headers)
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data, model)
        except httpx.ConnectError:
            # Proxy not running — try litellm direct if available
            return self._fallback_direct(payload, model)
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"LiteLLM proxy error {e.response.status_code}: {e.response.text[:300]}"
            ) from e

    def chat_with_context(
        self,
        prompt: str,
        context: str,
        model: str | None = None,
        *,
        system: str | None = None,
    ) -> ChatResponse:
        """Convenience method: send prompt with code context.

        Args:
            prompt: The user's question or instruction.
            context: Code analysis context (from code2llm .toon files).
            model: Model to use.
            system: Optional system prompt.
        """
        combined = f"## Project Analysis Context\n\n{context}\n\n## Task\n\n{prompt}"
        return self.chat(
            messages=[ChatMessage(role="user", content=combined)],
            model=model,
            system=system or "You are an expert code analyst. Use the project metrics and structure provided to give precise, actionable recommendations.",
        )

    def _build_payload(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int,
        system: str | None,
    ) -> dict[str, Any]:
        msg_list = []
        if system:
            msg_list.append({"role": "system", "content": system})
        msg_list.extend({"role": m.role, "content": m.content} for m in messages)

        return {
            "model": model,
            "messages": msg_list,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _parse_response(self, data: dict[str, Any], model: str) -> ChatResponse:
        choices = data.get("choices", [])
        content = choices[0]["message"]["content"] if choices else ""
        usage = data.get("usage", {})

        return ChatResponse(
            content=content,
            model=data.get("model", model),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            raw=data,
        )

    def _fallback_direct(self, payload: dict[str, Any], model: str) -> ChatResponse:
        """Fallback to direct litellm call when proxy is not running."""
        try:
            import litellm
            response = litellm.completion(**payload)
            return ChatResponse(
                content=response.choices[0].message.content,
                model=model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )
        except ImportError:
            raise RuntimeError(
                "LiteLLM proxy not running at "
                f"{self.config.litellm_base_url} and litellm package not installed. "
                "Install with: pip install codr[litellm]"
            )

    @staticmethod
    def _metrics_headers(metrics: ProjectMetrics) -> dict[str, str]:
        """Build X-Llx-* headers for proxym metrics-aware routing."""
        from llx.integrations.proxym import _build_llx_headers, _tier_to_proxym
        from llx.routing.selector import select_model, ModelTier
        result = select_model(metrics)
        return _build_llx_headers(metrics, result.tier)

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
