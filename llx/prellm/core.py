"""Core preLLM — main entry points for prompt decomposition, enrichment, and LLM calls.

v0.3 architecture (two-agent):
    User Query
      → PreprocessorAgent (small LLM ≤24B, PromptPipeline)
      → ExecutorAgent (large LLM >24B)
      → PreLLMResponse

v0.2 architecture (backward compat):
    User Query
      → ContextEngine (env/git/system)
      → Small LLM ≤3B (classify → structure → compose)
      → Large LLM (GPT-4/Claude/Llama)
      → PreLLMResponse

The old `prellm` class is kept for backward compatibility with v0.1 code.

Refactored v0.4: context_ops, pipeline_ops, extractors modules extracted.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from llx.prellm._nfo_compat import catch, log_call

from llx.prellm.analyzers.context_engine import ContextEngine
from llx.prellm.llm_provider import LLMProvider
from llx.prellm.models import (
    AuditEntry,
    DecompositionPrompts,
    DecompositionResult,
    DecompositionStrategy,
    DomainRule,
    LLMProviderConfig,
    Policy,
    PreLLMConfig,
    PreLLMResponse,
)
from llx.prellm.query_decomposer import QueryDecomposer
from llx.prellm.agents.executor import ExecutorAgent
from llx.prellm.agents.preprocessor import PreprocessorAgent
from llx.prellm.pipeline import PromptPipeline
from llx.prellm.prompt_registry import PromptRegistry
from llx.prellm.validators import ResponseValidator
from llx.prellm.trace import get_current_trace

# Import new modules for delegation (v0.4 refactor)
from llx.prellm import extractors, context_ops, pipeline_ops

logger = logging.getLogger("prellm")


def _resolve_pipeline_name(strategy: str | DecompositionStrategy, pipeline: str | None) -> str:
    if pipeline:
        return pipeline
    if isinstance(strategy, DecompositionStrategy):
        return strategy.value
    return strategy


def _apply_config_overrides(
    small_llm: str,
    large_llm: str,
    domain_rules: list[dict[str, Any]] | None,
    config_path: str | Path | None,
    kwargs: dict[str, Any],
) -> tuple[str, str, list[dict[str, Any]] | None]:
    if not config_path:
        return small_llm, large_llm, domain_rules

    config = PreLLM._load_config(Path(config_path))

    if small_llm == "ollama/qwen2.5:3b":
        small_llm = config.small_model.model
    if large_llm == "anthropic/claude-sonnet-4-20250514":
        large_llm = config.large_model.model
        kwargs.setdefault("max_tokens", config.large_model.max_tokens)
    if config.domain_rules and not domain_rules:
        domain_rules = [r.model_dump() for r in config.domain_rules]

    return small_llm, large_llm, domain_rules


def _trace_preprocess_configuration(
    trace: Any,
    small_llm: str,
    large_llm: str,
    pipeline_name: str,
    config_path: str | Path | None,
    user_context: str | dict[str, str] | None,
) -> None:
    if not trace:
        return

    trace.step(
        name="Configuration",
        step_type="config",
        description="Resolved models, strategy, and pipeline parameters.",
        outputs={
            "small_llm": small_llm,
            "large_llm": large_llm,
            "strategy": pipeline_name,
            "config_path": str(config_path) if config_path else None,
            "user_context": user_context,
        },
    )


# ============================================================
# 1-function API — like litellm.completion() but with preprocessing
# ============================================================

@catch
async def preprocess_and_execute(
    query: str,
    small_llm: str = "ollama/qwen2.5:3b",
    large_llm: str = "anthropic/claude-sonnet-4-20250514",
    strategy: str | DecompositionStrategy = "auto",
    user_context: str | dict[str, str] | None = None,
    config_path: str | Path | None = None,
    domain_rules: list[dict[str, Any]] | None = None,
    pipeline: str | None = None,
    prompts_path: str | Path | None = None,
    pipelines_path: str | Path | None = None,
    schemas_path: str | Path | None = None,
    memory_path: str | Path | None = None,
    codebase_path: str | Path | None = None,
    collect_env: bool = False,
    collect_runtime: bool = True,
    session_path: str | Path | None = None,
    compress_folder: bool = False,
    sanitize: bool = True,
    sensitive_rules: str | Path | None = None,
    **kwargs: Any,
) -> PreLLMResponse:
    """One function to preprocess and execute — like litellm.completion() but with small LLM decomposition.

    v0.4: automatic persistent context layer for small LLMs. Collects env, compresses codebase,
    persists session, and injects everything into the small-LLM without manual pre-prompts.
    Sensitive data never reaches the large-LLM.

    Args:
        query: The raw user query / prompt.
        small_llm: Model string for the small preprocessing LLM (e.g. "ollama/qwen2.5:3b").
        large_llm: Model string for the large executor LLM (e.g. "anthropic/claude-sonnet-4-20250514").
        strategy: Decomposition strategy — "auto" (default), "classify", "structure", "split", "enrich", "passthrough".
        user_context: Extra context as a string tag (e.g. "gdansk_embedded_python") or dict.
        config_path: Optional YAML config file for domain rules, prompts, etc.
        domain_rules: Optional inline domain rules as list of dicts.
        pipeline: Pipeline name from pipelines.yaml (e.g. "dual_agent_full"). Overrides strategy.
        prompts_path: Path to prompts.yaml.
        pipelines_path: Path to pipelines.yaml.
        schemas_path: Path to response_schemas.yaml.
        memory_path: Path to UserMemory database.
        codebase_path: Folder to compress for context injection.
        collect_env: Collect env vars (legacy, use collect_runtime instead).
        collect_runtime: Collect full runtime context (env, process, locale, network, git, system).
        session_path: Path to session persistence SQLite DB.
        compress_folder: Compress codebase folder into .toon representation.
        sanitize: Filter sensitive data before large-LLM (default: True).
        sensitive_rules: Custom YAML rules for sensitive data classification.
        **kwargs: Extra kwargs passed to the large LLM call (max_tokens, temperature, etc.).

    Returns:
        PreLLMResponse with content, decomposition details, model info.

    Usage:
        # Zero-config with auto strategy:
        result = await preprocess_and_execute("Refaktoryzuj kod")

        # Bielik with full persistent context:
        result = await preprocess_and_execute(
            "Zoptymalizuj monitoring ESP32",
            small_llm="ollama/bielik:7b",
            large_llm="openrouter/google/gemini-3-flash-preview",
            session_path=".prellm/sessions.db",
            codebase_path=".",
        )
    """
    pipeline_name = _resolve_pipeline_name(strategy, pipeline)
    small_llm, large_llm, domain_rules = _apply_config_overrides(
        small_llm,
        large_llm,
        domain_rules,
        config_path,
        kwargs,
    )

    logger.info(f"preLLM pipeline: {small_llm} \u2192 {large_llm} | strategy={pipeline_name}")

    # Record trace config
    trace = get_current_trace()
    _trace_preprocess_configuration(
        trace,
        small_llm,
        large_llm,
        pipeline_name,
        config_path,
        user_context,
    )

    # Delegate to pipeline_ops module (v0.4 refactor)
    return await pipeline_ops.execute_v3_pipeline(
        query=query,
        small_llm=small_llm,
        large_llm=large_llm,
        pipeline=pipeline_name,
        user_context=user_context,
        domain_rules=domain_rules,
        prompts_path=prompts_path,
        pipelines_path=pipelines_path,
        schemas_path=schemas_path,
        memory_path=memory_path or (str(session_path) if session_path else None),
        codebase_path=codebase_path,
        collect_env=collect_env or collect_runtime,
        compress_folder=compress_folder or bool(codebase_path),
        sanitize=sanitize,
        sensitive_rules=sensitive_rules,
        **kwargs,
    )


# Sync wrapper for non-async code
def preprocess_and_execute_sync(
    query: str,
    small_llm: str = "ollama/qwen2.5:3b",
    large_llm: str = "anthropic/claude-sonnet-4-20250514",
    strategy: str | DecompositionStrategy = "classify",
    user_context: str | dict[str, str] | None = None,
    config_path: str | Path | None = None,
    domain_rules: list[dict[str, Any]] | None = None,
    pipeline: str | None = None,
    prompts_path: str | Path | None = None,
    pipelines_path: str | Path | None = None,
    schemas_path: str | Path | None = None,
    **kwargs: Any,
) -> PreLLMResponse:
    """Synchronous version of preprocess_and_execute() — runs the async function in an event loop.

    Usage:
        from llx.prellm import preprocess_and_execute_sync
        result = preprocess_and_execute_sync("Deploy app", large_llm="gpt-4o-mini")
    """
    import asyncio
    return asyncio.run(preprocess_and_execute(
        query=query,
        small_llm=small_llm,
        large_llm=large_llm,
        strategy=strategy,
        user_context=user_context,
        config_path=config_path,
        domain_rules=domain_rules,
        pipeline=pipeline,
        prompts_path=prompts_path,
        pipelines_path=pipelines_path,
        schemas_path=schemas_path,
        **kwargs,
    ))


# Backward-compatible alias
preprocess_and_execute_v3 = preprocess_and_execute


# ============================================================
# v0.2 — PreLLM (class-based architecture, backward compat)
# ============================================================

class PreLLM:
    """preLLM v0.2/v0.3 — small LLM decomposition before large LLM routing.

    Usage:
        engine = PreLLM("prellm_config.yaml")
        result = await engine("Zdeployuj apkę na prod")

    Or with inline config:
        engine = PreLLM(config=PreLLMConfig(...))
        result = await engine("Deploy the app", strategy=DecompositionStrategy.STRUCTURE)

    v0.3 two-agent mode:
        engine = PreLLM(config=config, use_agents=True)
        result = await engine("Deploy the app", pipeline="dual_agent_full")
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        config: PreLLMConfig | None = None,
    ):
        if config:
            self.config = config
        elif config_path:
            self.config = self._load_config(Path(config_path))
        else:
            self.config = PreLLMConfig()

        self.small_llm = LLMProvider(self.config.small_model)
        self.large_llm = LLMProvider(self.config.large_model)
        self.decomposer = QueryDecomposer(
            small_llm=self.small_llm,
            prompts=self.config.prompts,
            domain_rules=self.config.domain_rules,
        )
        self.context_engine = ContextEngine(self.config.context_sources)
        self.audit_log: list[AuditEntry] = []

    async def __call__(
        self,
        query: str,
        strategy: DecompositionStrategy | None = None,
        extra_context: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> PreLLMResponse:
        """Full pipeline: context → decompose (small LLM) → large LLM → response.

        Args:
            query: The raw user query.
            strategy: Override the default decomposition strategy.
            extra_context: Additional key-value context to inject.
            **kwargs: Extra kwargs passed to the large LLM call.

        Returns:
            PreLLMResponse with decomposition details and large LLM output.
        """
        active_strategy = strategy or self.config.default_strategy

        # Step 1: Gather context
        ctx = self.context_engine.gather()
        if extra_context:
            ctx.update(extra_context)

        # Step 2: Decompose with small LLM
        decomposition = await self.decomposer.decompose(
            query=query,
            strategy=active_strategy,
            context=ctx,
        )

        # Step 3: Call large LLM with composed prompt
        prompt_for_large = decomposition.composed_prompt or query
        retries = 0

        try:
            content = await self.large_llm.complete(
                user_message=prompt_for_large,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Large LLM call failed: {e}")
            content = "No response from any model."
            retries += 1

        # Step 4: Build response
        result = PreLLMResponse(
            content=content,
            decomposition=decomposition,
            model_used=self.config.large_model.model,
            small_model_used=self.config.small_model.model,
            retries=retries,
            clarified=bool(decomposition.missing_fields),
            needs_more_context=bool(decomposition.missing_fields) and content == "No response from any model.",
        )

        # Audit
        self._audit("query", query, result)

        return result

    async def decompose_only(
        self,
        query: str,
        strategy: DecompositionStrategy | None = None,
        extra_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Run decomposition without calling the large LLM — useful for dry-run / testing."""
        active_strategy = strategy or self.config.default_strategy

        ctx = self.context_engine.gather()
        if extra_context:
            ctx.update(extra_context)

        decomposition = await self.decomposer.decompose(
            query=query,
            strategy=active_strategy,
            context=ctx,
        )

        return {
            "strategy": decomposition.strategy.value,
            "original_query": decomposition.original_query,
            "classification": decomposition.classification.model_dump() if decomposition.classification else None,
            "structure": decomposition.structure.model_dump() if decomposition.structure else None,
            "sub_queries": decomposition.sub_queries,
            "missing_fields": decomposition.missing_fields,
            "matched_rule": decomposition.matched_rule,
            "composed_prompt": decomposition.composed_prompt,
        }

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return audit log as list of dicts."""
        return [entry.model_dump() for entry in self.audit_log]

    def _audit(self, action: str, query: str, response: PreLLMResponse) -> None:
        entry = AuditEntry(
            action=action,
            query=query,
            response_summary=response.content[:200] if response.content else "",
            model=response.model_used,
            policy=self.config.policy,
            metadata={
                "small_model": response.small_model_used,
                "strategy": response.decomposition.strategy.value if response.decomposition else "unknown",
            },
        )
        self.audit_log.append(entry)

    @staticmethod
    def _load_config(path: Path) -> PreLLMConfig:
        """Load preLLM v0.2 config from YAML file."""
        with open(path) as f:
            raw = yaml.safe_load(f) or {}

        # Parse small_model
        small_raw = raw.get("small_model", {})
        small_model = LLMProviderConfig(**small_raw) if isinstance(small_raw, dict) and small_raw else LLMProviderConfig(
            model="phi3:mini", max_tokens=512, temperature=0.0
        )

        # Parse large_model
        large_raw = raw.get("large_model", {})
        large_model = LLMProviderConfig(**large_raw) if isinstance(large_raw, dict) and large_raw else LLMProviderConfig(
            model="gpt-4o-mini", max_tokens=2048
        )

        # Parse domain_rules
        domain_rules = []
        for r in raw.get("domain_rules", []):
            if isinstance(r, dict):
                domain_rules.append(DomainRule(**r))

        # Parse prompts
        prompts_raw = raw.get("prompts", {})
        prompts = DecompositionPrompts(**prompts_raw) if isinstance(prompts_raw, dict) and prompts_raw else DecompositionPrompts()

        # Parse default_strategy
        strategy_str = raw.get("default_strategy", "classify")
        default_strategy = DecompositionStrategy(strategy_str)

        return PreLLMConfig(
            small_model=small_model,
            large_model=large_model,
            domain_rules=domain_rules,
            prompts=prompts,
            default_strategy=default_strategy,
            context_sources=raw.get("context_sources", []),
            max_retries=raw.get("max_retries", 3),
            policy=Policy(raw.get("policy", "strict")),
        )
