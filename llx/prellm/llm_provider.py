"""LLMProvider — LiteLLM wrapper with retry/fallback for preLLM.

Wraps LiteLLM completion calls with:
- Retry logic with exponential backoff
- Fallback to backup models on failure
- JSON response parsing
- Timeout handling
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from llx.prellm.models import LLMProviderConfig

logger = logging.getLogger("prellm.llm_provider")

# LiteLLM is optional - fail gracefully if not installed
try:
    import litellm
    from litellm import acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    litellm = None
    acompletion = None


class LLMProvider:
    """LiteLLM wrapper with retry and fallback support.

    Usage:
        provider = LLMProvider(LLMProviderConfig(model="gpt-4o-mini"))
        text = await provider.complete("Hello", system_prompt="Be helpful")
        data = await provider.complete_json("Extract: {...}")
    """

    def __init__(self, config: LLMProviderConfig | None = None):
        self.config = config or LLMProviderConfig()

    async def complete(
        self,
        user_message: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """Complete a prompt with retry and fallback.

        Args:
            user_message: The user message to send.
            system_prompt: Optional system prompt.
            **kwargs: Additional arguments for the completion call.

        Returns:
            The response content as a string.

        Raises:
            RuntimeError: If LiteLLM is not available or all retries fail.
        """
        if not LITELLM_AVAILABLE:
            raise RuntimeError("LiteLLM not installed. Install with: pip install litellm")

        models_to_try = [self.config.model] + list(self.config.fallback)
        last_error = None

        for attempt, model in enumerate(models_to_try):
            for retry in range(self.config.max_retries):
                try:
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": user_message})

                    response = await asyncio.wait_for(
                        acompletion(
                            model=model,
                            messages=messages,
                            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                            temperature=kwargs.get("temperature", self.config.temperature),
                            **{k: v for k, v in kwargs.items() if k not in ("max_tokens", "temperature")},
                        ),
                        timeout=self.config.timeout,
                    )

                    # Extract content from response
                    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        return content

                except asyncio.TimeoutError:
                    last_error = f"Timeout after {self.config.timeout}s for model {model}"
                    logger.warning(f"Attempt {retry + 1}/{self.config.max_retries} timeout for {model}")
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Attempt {retry + 1}/{self.config.max_retries} failed for {model}: {e}")

                # Wait before retry with exponential backoff
                if retry < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** retry)

        # All models and retries exhausted
        raise RuntimeError(f"All LLM attempts failed. Last error: {last_error}")

    async def complete_json(
        self,
        user_message: str,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Complete a prompt and parse the result as JSON.

        Args:
            user_message: The user message to send.
            system_prompt: Optional system prompt.
            **kwargs: Additional arguments for the completion call.

        Returns:
            The parsed JSON as a dictionary.

        Raises:
            RuntimeError: If LiteLLM is not available or parsing fails.
        """
        content = await self.complete(user_message, system_prompt, **kwargs)

        # Try to extract JSON from the response
        content = content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove opening fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}. Content: {content[:200]}...")
            # Return empty dict on parse failure - caller should handle
            return {}

    def __repr__(self) -> str:
        return f"LLMProvider(model={self.config.model}, max_retries={self.config.max_retries})"
