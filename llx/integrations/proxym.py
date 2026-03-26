"""Proxym integration — connect llx analysis to proxym intelligent routing.

Proxym is the intelligent AI proxy (wronai/proxy) that provides:
- OpenAI-compatible /v1/chat/completions with content-based routing
- Multi-provider model registry with cost/capability metadata
- Budget enforcement (daily/monthly)
- Delta context buffer for code analysis

llx enriches proxym routing by providing static code metrics
(from code2llm/redup/vallm) via X-Task-Tier and X-Llx-* headers.
This gives proxym better information for model selection.

Usage:
    from llx.integrations.proxym import ProxymClient

    client = ProxymClient()
    if client.is_available():
        response = client.chat("Explain this code", metrics=metrics)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from llx.analysis.collector import ProjectMetrics
from llx.config import LlxConfig
from llx.routing.selector import ModelTier, select_model


@dataclass
class ProxymStatus:
    """Status of the proxym proxy server."""

    available: bool
    url: str
    version: str | None = None
    models_count: int = 0
    providers: list[str] | None = None
    daily_remaining: float | None = None
    monthly_remaining: float | None = None
    error: str | None = None


@dataclass
class ProxymResponse:
    """Response from proxym chat completion."""

    content: str
    model: str
    provider: str | None = None
    usage: dict[str, int] | None = None
    cost_usd: float | None = None
    routing_reason: str | None = None
    raw: dict[str, Any] | None = None

    @property
    def prompt_tokens(self) -> int:
        return (self.usage or {}).get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return (self.usage or {}).get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return (self.usage or {}).get("total_tokens", 0)


def _tier_to_proxym(tier: ModelTier) -> str:
    """Map llx ModelTier to proxym TaskTier header value.

    llx tiers:    free, local, cheap, balanced, premium
    proxym tiers: trivial, operational, standard, complex, deep
    """
    return {
        ModelTier.FREE: "trivial",
        ModelTier.LOCAL: "operational",
        ModelTier.CHEAP: "operational",
        ModelTier.BALANCED: "standard",
        ModelTier.PREMIUM: "complex",
    }.get(tier, "standard")


def _build_llx_headers(metrics: ProjectMetrics | None, tier: ModelTier | None) -> dict[str, str]:
    """Build X-Llx-* headers to pass code metrics to proxym."""
    headers: dict[str, str] = {}
    if tier:
        headers["X-Task-Tier"] = _tier_to_proxym(tier)
    if metrics:
        headers["X-Llx-Files"] = str(metrics.total_files)
        headers["X-Llx-Lines"] = str(metrics.total_lines)
        headers["X-Llx-Avg-Cc"] = f"{metrics.avg_cc:.1f}"
        headers["X-Llx-Max-Cc"] = str(metrics.max_cc)
        headers["X-Llx-Complexity"] = f"{metrics.complexity_score:.0f}"
        headers["X-Llx-Scale"] = f"{metrics.scale_score:.0f}"
        if metrics.god_modules:
            headers["X-Llx-God-Modules"] = str(metrics.god_modules)
        if metrics.dependency_cycles:
            headers["X-Llx-Dep-Cycles"] = str(metrics.dependency_cycles)
    return headers


class ProxymClient:
    """Client for proxym intelligent AI proxy.

    Combines llx's static code analysis with proxym's runtime content
    analysis for optimal model selection.

    Usage:
        client = ProxymClient()
        status = client.status()
        if status.available:
            response = client.chat("Refactor this module", metrics=metrics)
    """

    def __init__(
        self,
        config: LlxConfig | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
    ):
        self.config = config or LlxConfig()
        self.base_url = base_url or self.config.litellm_base_url
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    def is_available(self) -> bool:
        """Quick check if proxym is running."""
        try:
            resp = self._http.get("/health", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def status(self) -> ProxymStatus:
        """Get detailed proxym status including budget and model info."""
        try:
            resp = self._http.get("/health", timeout=5.0)
            if resp.status_code != 200:
                return ProxymStatus(available=False, url=self.base_url, error=f"HTTP {resp.status_code}")

            data = resp.json()

            # Try to get models count
            models_count = 0
            try:
                models_resp = self._http.get("/v1/models", timeout=5.0)
                if models_resp.status_code == 200:
                    models_data = models_resp.json()
                    models_count = len(models_data.get("data", []))
            except Exception:
                pass

            # Try to get budget info
            daily_remaining = None
            monthly_remaining = None
            try:
                budget_resp = self._http.get("/v1/budget", timeout=5.0)
                if budget_resp.status_code == 200:
                    budget = budget_resp.json()
                    daily_remaining = budget.get("daily_remaining")
                    monthly_remaining = budget.get("monthly_remaining")
            except Exception:
                pass

            return ProxymStatus(
                available=True,
                url=self.base_url,
                version=data.get("version"),
                models_count=models_count,
                providers=data.get("providers"),
                daily_remaining=daily_remaining,
                monthly_remaining=monthly_remaining,
            )
        except httpx.ConnectError:
            return ProxymStatus(available=False, url=self.base_url, error="Connection refused")
        except Exception as e:
            return ProxymStatus(available=False, url=self.base_url, error=str(e))

    def chat(
        self,
        prompt: str,
        *,
        metrics: ProjectMetrics | None = None,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        task_hint: str | None = None,
        context: str | None = None,
    ) -> ProxymResponse:
        """Send a chat completion through proxym with llx metrics context.

        Args:
            prompt: User prompt.
            metrics: Project metrics for tier-aware routing.
            model: Explicit model override (bypasses routing).
            system: System prompt.
            temperature: Sampling temperature.
            max_tokens: Max response tokens.
            task_hint: Task hint for llx tier selection.
            context: Additional code context to prepend.

        Returns:
            ProxymResponse with content, model used, and usage stats.
        """
        # Compute llx tier from metrics
        tier = None
        if metrics:
            result = select_model(metrics, self.config, task_hint=task_hint)
            tier = result.tier

        headers = _build_llx_headers(metrics, tier)

        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        content = prompt
        if context:
            content = f"## Project Context\n\n{context}\n\n## Task\n\n{prompt}"
        messages.append({"role": "user", "content": content})

        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if model:
            payload["model"] = model
        elif tier:
            # Pass llx tier as model alias — proxym understands these
            payload["model"] = tier.value

        try:
            resp = self._http.post(
                "/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return self._parse_response(data)
        except httpx.ConnectError:
            raise RuntimeError(
                f"Proxym not running at {self.base_url}. "
                "Start with: proxym-server"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Proxym error {e.response.status_code}: {e.response.text[:300]}"
            ) from e

    def chat_with_analysis(
        self,
        prompt: str,
        project_path: str = ".",
        *,
        toon_dir: str | None = None,
        task_hint: str | None = None,
        model: str | None = None,
    ) -> ProxymResponse:
        """Analyze project, build context, and send to proxym.

        Convenience method that runs the full llx pipeline:
        1. Collect project metrics
        2. Select model tier
        3. Build context from .toon files
        4. Send to proxym with metrics headers
        """
        from llx.analysis.collector import analyze_project
        from llx.integrations.context_builder import build_context
        from llx.routing.selector import select_with_context_check
        from pathlib import Path

        project = Path(project_path).resolve()
        config = LlxConfig.load(project)
        metrics = analyze_project(project, toon_dir=toon_dir)
        result = select_with_context_check(metrics, config, task_hint=task_hint)
        context = build_context(project, metrics, result.tier)

        return self.chat(
            prompt,
            metrics=metrics,
            model=model,
            task_hint=task_hint,
            context=context,
            system="You are an expert code analyst. Use the project metrics and structure provided to give precise, actionable recommendations.",
        )

    def list_models(self) -> list[dict[str, Any]]:
        """List available models from proxym."""
        try:
            resp = self._http.get("/v1/models", timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception:
            return []

    def _parse_response(self, data: dict[str, Any]) -> ProxymResponse:
        choices = data.get("choices", [])
        content = choices[0]["message"]["content"] if choices else ""
        usage = data.get("usage", {})

        return ProxymResponse(
            content=content,
            model=data.get("model", "unknown"),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            raw=data,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
