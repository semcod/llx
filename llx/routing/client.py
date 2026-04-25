"""LiteLLM client wrapper for codr.

Supports two modes:
1. Proxy mode: Route through LiteLLM proxy at localhost:4000
2. Direct mode: Use litellm.completion() directly

Both modes support the OpenAI-compatible API format.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Iterator

import httpx

from llx.config import LlxConfig, ModelConfig
from llx.config import normalize_litellm_base_url
from llx.analysis.collector import ProjectMetrics


try:
    from llx.privacy import Anonymizer, AnonymizationResult
    PRIVACY_AVAILABLE = True
except ImportError:
    PRIVACY_AVAILABLE = False
    Anonymizer = None  # type: ignore
    AnonymizationResult = None  # type: ignore


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str  # system, user, assistant
    content: str
    _anonymized: bool = field(default=False, repr=False)
    _anonymization_mapping: dict[str, str] = field(default_factory=dict, repr=False)


@dataclass
class ChatResponse:
    """Response from LLM completion."""

    content: str
    model: str
    usage: dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    raw: dict[str, Any] | None = None
    _anonymization_mapping: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)

    def deanonymize(self) -> "ChatResponse":
        """Return response with original values restored."""
        if not self._anonymization_mapping:
            return self
        
        if not PRIVACY_AVAILABLE:
            return self
            
        restored_content = Anonymizer().deanonymize(
            self.content, self._anonymization_mapping
        )
        return ChatResponse(
            content=restored_content,
            model=self.model,
            usage=self.usage,
            raw=self.raw,
            _anonymization_mapping=self._anonymization_mapping,
        )


class LlxClient:
    """LLM client that routes through LiteLLM proxy or calls directly.

    Usage:
        client = LlxClient(config)
        response = client.chat(
            model="anthropic/claude-sonnet-4-20250514",
            messages=[ChatMessage(role="user", content="Explain this code")],
        )
    
    With anonymization:
        client = LlxClient(config, anonymize=True)
        response = client.chat_with_context(prompt, context)
        restored = response.deanonymize()  # Restore sensitive data
    """

    def __init__(self, config: LlxConfig | None = None, *, anonymize: bool = False):
        self.config = config or LlxConfig()
        self.config.litellm_base_url = normalize_litellm_base_url(self.config.litellm_base_url)

        # Initialize anonymizer if requested and available
        self._anonymize = anonymize and PRIVACY_AVAILABLE
        self._anonymizer: Anonymizer | None = None
        if self._anonymize:
            self._anonymizer = Anonymizer()

        headers = {"Content-Type": "application/json"}
        
        # Determine if we are hitting OpenRouter directly or a proxy
        self.is_localhost = "localhost" in self.config.litellm_base_url or "127.0.0.1" in self.config.litellm_base_url
        is_openrouter = "openrouter.ai" in self.config.litellm_base_url
        
        # Add auth header for OpenRouter direct API calls (highest priority if hitting OpenRouter)
        if is_openrouter:
            openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            if openrouter_key:
                headers["Authorization"] = f"Bearer {openrouter_key}"
            else:
                headers["HTTP-Referer"] = "https://github.com/wronai/llx"
                headers["X-Title"] = "LLX"
        # Add auth header for local proxy
        elif self.is_localhost and self.config.proxy.master_key:
            headers["Authorization"] = f"Bearer {self.config.proxy.master_key}"

        self._http = httpx.Client(
            base_url=self.config.litellm_base_url,
            timeout=120.0,
            headers=headers,
        )
        self._last_anonymization_mapping: dict[str, str] = {}

    def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        system: str | None = None,
        metrics: ProjectMetrics | None = None,
        anonymize: bool | None = None,
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
            anonymize: Override default anonymization setting for this request.

        Returns:
            ChatResponse with content and usage stats.
        """
        if model is None:
            default = self.config.models.get(self.config.default_tier)
            model = default.model_id if default else "anthropic/claude-sonnet-4-20250514"

        # Determine if we should anonymize for this request
        should_anonymize = self._anonymize if anonymize is None else (anonymize and PRIVACY_AVAILABLE)

        # Anonymize messages if enabled
        processed_messages = messages
        anonymization_mapping: dict[str, str] = {}
        if should_anonymize and self._anonymizer:
            processed_messages = []
            for msg in messages:
                result = self._anonymizer.anonymize(msg.content, context=f"msg_{msg.role}")
                processed_messages.append(
                    ChatMessage(
                        role=msg.role,
                        content=result.text,
                        _anonymized=True,
                        _anonymization_mapping=result.mapping,
                    )
                )
                anonymization_mapping.update(result.mapping)
            self._last_anonymization_mapping = anonymization_mapping

        payload = self._build_payload(processed_messages, model, temperature, max_tokens, system)
        extra_headers = self._metrics_headers(metrics) if metrics else {}

        try:
            response = self._http.post("/v1/chat/completions", json=payload, headers=extra_headers)
            
            # Special case: if localhost returns 404, it might be another service (like Express)
            # instead of LiteLLM proxy. Fallback to direct call.
            if response.status_code == 404 and self.is_localhost:
                if model.startswith("openrouter/"):
                    return self._direct_openrouter_call(payload, anonymization_mapping)
                return self._fallback_direct(payload, model, anonymization_mapping)
                
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data, model, anonymization_mapping)
        except httpx.ConnectError:
            # Proxy not running — try direct OpenRouter if applicable, else litellm direct
            if model.startswith("openrouter/"):
                try:
                    return self._direct_openrouter_call(payload, anonymization_mapping)
                except Exception:
                    pass
            return self._fallback_direct(payload, model, anonymization_mapping)
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
        # Strip 'openrouter/' prefix if hitting OpenRouter directly or via proxy
        # OpenRouter itself doesn't want the prefix in the model ID
        if model.startswith("openrouter/"):
            model = model[len("openrouter/"):]

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

    def _direct_openrouter_call(self, payload: dict[str, Any], anonymization_mapping: dict[str, str] | None = None) -> ChatResponse:
        """Call OpenRouter API directly using httpx."""
        key = os.environ.get("OPENROUTER_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/wronai/llx",
            "X-Title": "LLX",
        }
        if key:
            headers["Authorization"] = f"Bearer {key}"
        
        # OpenRouter direct API doesn't need the 'openrouter/' prefix
        direct_model = payload["model"]
        if direct_model.startswith("openrouter/"):
            direct_model = direct_model[len("openrouter/"):]
        
        payload = payload.copy()
        payload["model"] = direct_model
        
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            return self._parse_response(resp.json(), payload["model"], anonymization_mapping)

    def _parse_response(self, data: dict[str, Any], model: str, anonymization_mapping: dict[str, str] | None = None) -> ChatResponse:
        """Parse API response with optional anonymization mapping."""
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
            _anonymization_mapping=anonymization_mapping or {},
        )

    def _fallback_direct(self, payload: dict[str, Any], model: str, anonymization_mapping: dict[str, str] | None = None) -> ChatResponse:
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
                _anonymization_mapping=anonymization_mapping or {},
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
