"""
LLM request executors — standalone functions for each provider type.
Extracted from LLMOrchestrator._execute_* methods.
"""

from typing import Dict, List, Any

import requests

from .models import LLMProvider, LLMModel, LLMRequest, LLMResponse, LLMProviderType


def execute_request(
    request: LLMRequest,
    provider: LLMProvider,
    model: LLMModel,
) -> LLMResponse:
    """Execute LLM request, dispatching to the correct provider executor."""
    if provider.provider_type == LLMProviderType.OLLAMA:
        return execute_ollama(request, provider, model)
    elif provider.provider_type == LLMProviderType.OPENAI:
        return execute_openai(request, provider, model)
    elif provider.provider_type == LLMProviderType.ANTHROPIC:
        return execute_anthropic(request, provider, model)
    else:
        return execute_openai(request, provider, model)  # generic fallback


def execute_ollama(
    request: LLMRequest,
    provider: LLMProvider,
    model: LLMModel,
) -> LLMResponse:
    """Execute Ollama request."""
    api_base = provider.api_base or "http://localhost:11434"
    url = f"{api_base}/api/generate"

    payload = {
        "model": model.name,
        "prompt": messages_to_prompt(request.messages),
        "stream": request.stream,
        "options": {
            "temperature": request.temperature,
            "top_p": request.top_p,
            "num_predict": request.max_tokens,
        },
    }

    response = requests.post(url, json=payload, timeout=request.timeout_seconds)

    if response.status_code != 200:
        return _failed(request, f"HTTP {response.status_code}: {response.text}")

    data = response.json()

    # Calculate tokens (approximate)
    prompt_tokens = len(payload["prompt"].split()) * 1.3
    completion_tokens = len(data.get("response", "").split()) * 1.3
    total_tokens = int(prompt_tokens + completion_tokens)

    cost = (
        prompt_tokens / 1000 * model.cost_per_1k_input
        + completion_tokens / 1000 * model.cost_per_1k_output
    )

    return LLMResponse(
        request_id=request.request_id,
        provider=provider.provider_id,
        model=model.model_id,
        content=data.get("response", ""),
        finish_reason=data.get("done_reason", "stop"),
        prompt_tokens=int(prompt_tokens),
        completion_tokens=int(completion_tokens),
        total_tokens=total_tokens,
        latency_ms=0,  # Set by caller
        cost=cost,
        success=True,
    )


def execute_openai(
    request: LLMRequest,
    provider: LLMProvider,
    model: LLMModel,
) -> LLMResponse:
    """Execute OpenAI-compatible request."""
    api_base = provider.api_base or "https://api.openai.com/v1"
    url = f"{api_base}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider.auth_config.get('api_key')}",
    }

    payload = {
        "model": model.name,
        "messages": request.messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "top_p": request.top_p,
        "frequency_penalty": request.frequency_penalty,
        "presence_penalty": request.presence_penalty,
        "stream": request.stream,
    }

    response = requests.post(
        url, json=payload, headers=headers, timeout=request.timeout_seconds
    )

    if response.status_code != 200:
        return _failed(request, f"HTTP {response.status_code}: {response.text}")

    data = response.json()
    choice = data["choices"][0]
    usage = data.get("usage", {})

    cost = (
        usage.get("prompt_tokens", 0) / 1000 * model.cost_per_1k_input
        + usage.get("completion_tokens", 0) / 1000 * model.cost_per_1k_output
    )

    return LLMResponse(
        request_id=request.request_id,
        provider=provider.provider_id,
        model=model.model_id,
        content=choice.get("message", {}).get("content", ""),
        finish_reason=choice.get("finish_reason", "stop"),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        latency_ms=0,  # Set by caller
        cost=cost,
        success=True,
    )


def execute_anthropic(
    request: LLMRequest,
    provider: LLMProvider,
    model: LLMModel,
) -> LLMResponse:
    """Execute Anthropic request."""
    api_base = provider.api_base or "https://api.anthropic.com/v1"
    url = f"{api_base}/messages"

    headers = {
        "Content-Type": "application/json",
        "x-api-key": provider.auth_config.get("api_key"),
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model": model.name,
        "messages": request.messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "top_p": request.top_p,
    }

    response = requests.post(
        url, json=payload, headers=headers, timeout=request.timeout_seconds
    )

    if response.status_code != 200:
        return _failed(request, f"HTTP {response.status_code}: {response.text}")

    data = response.json()
    usage = data.get("usage", {})

    cost = (
        usage.get("input_tokens", 0) / 1000 * model.cost_per_1k_input
        + usage.get("output_tokens", 0) / 1000 * model.cost_per_1k_output
    )

    return LLMResponse(
        request_id=request.request_id,
        provider=provider.provider_id,
        model=model.model_id,
        content=data.get("content", [{}])[0].get("text", ""),
        finish_reason=data.get("stop_reason", "stop"),
        prompt_tokens=usage.get("input_tokens", 0),
        completion_tokens=usage.get("output_tokens", 0),
        total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        latency_ms=0,  # Set by caller
        cost=cost,
        success=True,
    )


def messages_to_prompt(messages: List[Dict[str, Any]]) -> str:
    """Convert messages to prompt for non-chat models."""
    prompt_parts = []

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"Human: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")

    return "\n\n".join(prompt_parts)


def _failed(request: LLMRequest, error: str) -> LLMResponse:
    """Create a failed response."""
    return LLMResponse(
        request_id=request.request_id,
        provider="",
        model="",
        content="",
        finish_reason="error",
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        latency_ms=0,
        cost=0.0,
        success=False,
        error=error,
    )
