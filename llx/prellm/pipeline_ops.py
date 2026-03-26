"""Pipeline operations for preLLM - extracted from core.py to reduce CC.

This module contains pipeline execution, preprocessing, and runtime operations
that were previously in core.py.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from llx.prellm._nfo_compat import log_call
from llx.prellm.agents.executor import ExecutorAgent
from llx.prellm.agents.preprocessor import PreprocessorAgent
from llx.prellm.analyzers.context_engine import ContextEngine
from llx.prellm.llm_provider import LLMProvider
from llx.prellm.models import LLMProviderConfig
from llx.prellm.pipeline import PromptPipeline
from llx.prellm.prompt_registry import PromptRegistry
from llx.prellm.trace import get_current_trace
from llx.prellm.validators import ResponseValidator

logger = logging.getLogger("prellm.pipeline_ops")


@log_call
async def execute_v3_pipeline(
    query: str,
    small_llm: str,
    large_llm: str,
    pipeline: str,
    user_context: str | dict[str, str] | None = None,
    domain_rules: list[dict[str, Any]] | None = None,
    prompts_path: str | None = None,
    pipelines_path: str | None = None,
    schemas_path: str | None = None,
    memory_path: str | None = None,
    codebase_path: str | None = None,
    collect_env: bool = False,
    compress_folder: bool = False,
    sanitize: bool = False,
    sensitive_rules: str | None = None,
    **kwargs: Any,
) -> Any:
    """Two-agent execution path — PreprocessorAgent + ExecutorAgent + PromptPipeline.

    v0.4 refactor: uses context_ops and pipeline_ops modules to reduce complexity.
    """
    from llx.prellm.context_ops import prepare_context, build_pipeline_context
    from llx.prellm.extractors import build_decomposition_result
    from llx.prellm.models import PreLLMResponse
    
    max_tokens = kwargs.pop("max_tokens", 2048)
    temperature = kwargs.pop("temperature", 0.7)

    # Build LLM providers
    small_llm_config = LLMProviderConfig(model=small_llm, max_tokens=512, temperature=0.0)
    large_llm_config = LLMProviderConfig(model=large_llm, max_tokens=max_tokens, temperature=temperature)

    small_provider = LLMProvider(small_llm_config)
    large_provider = LLMProvider(large_llm_config)

    # Build registry and pipeline
    registry = PromptRegistry(prompts_path=prompts_path)
    prompt_pipeline = PromptPipeline.from_yaml(
        pipelines_path=pipelines_path,
        pipeline_name=pipeline,
        registry=registry,
        small_llm=small_provider,
    )

    # 1. Prepare context (env, codebase, memory, sensitive filter)
    extra_context, sensitive_filter, user_memory, codebase_indexer = prepare_context(
        user_context=user_context,
        domain_rules=domain_rules,
        collect_env=collect_env,
        compress_folder=compress_folder,
        codebase_path=codebase_path,
        sanitize=sanitize,
        sensitive_rules=sensitive_rules,
        memory_path=memory_path,
    )

    # Build agents
    preprocessor = PreprocessorAgent(
        small_llm=small_provider,
        registry=registry,
        pipeline=prompt_pipeline,
        context_engine=ContextEngine(),
        user_memory=user_memory,
        codebase_indexer=codebase_indexer,
        codebase_path=str(codebase_path) if codebase_path else None,
    )
    executor = ExecutorAgent(
        large_llm=large_provider,
        response_validator=ResponseValidator(schemas_path=schemas_path) if schemas_path else None,
        sensitive_filter=sensitive_filter,
    )

    # 2. Build compact pipeline context for small LLM (no raw blobs)
    pipeline_context = build_pipeline_context(extra_context)

    # 2b. Run preprocessing (small LLM) with compact context only
    prep_result, prep_duration_ms = await run_preprocessing(
        preprocessor, query, pipeline_context, pipeline
    )

    # 3. Build system_prompt from preprocessing + FULL context for the large LLM
    from llx.prellm.extractors import build_executor_system_prompt
    system_prompt = build_executor_system_prompt(prep_result, extra_context)

    # 4. Run execution with sanitization (large LLM)
    exec_result, exec_duration_ms = await run_execution(
        executor, prep_result.executor_input, system_prompt=system_prompt, **kwargs
    )

    # 5. Persist session if memory available
    await persist_session(user_memory, query, exec_result)

    # 6. Build response
    trace = get_current_trace()
    record_trace(trace, pipeline, small_llm, large_llm, query, pipeline_context,
                 prep_result, exec_result, prep_duration_ms, exec_duration_ms)

    decomposition_result = build_decomposition_result(query, pipeline, prep_result)

    response = PreLLMResponse(
        content=exec_result.content or "No response from any model.",
        decomposition=decomposition_result,
        model_used=exec_result.model_used,
        small_model_used=small_llm,
        retries=exec_result.retries,
        clarified=bool(decomposition_result and decomposition_result.missing_fields),
        needs_more_context=bool(decomposition_result and decomposition_result.missing_fields) and not exec_result.content,
    )

    if trace:
        trace.set_result(
            content=response.content,
            model_used=response.model_used,
            small_model_used=response.small_model_used,
            retries=response.retries,
            strategy=pipeline,
            classification=(
                decomposition_result.classification.model_dump()
                if decomposition_result and decomposition_result.classification
                else None
            ),
        )

    return response


async def run_preprocessing(
    preprocessor: PreprocessorAgent,
    query: str,
    extra_context: dict[str, Any],
    pipeline: str,
) -> tuple[Any, float]:
    """Run the small-LLM preprocessing step. Returns (prep_result, duration_ms)."""
    _t0 = time.time()
    prep_result = await preprocessor.preprocess(
        query=query,
        user_context=extra_context or None,
        pipeline_name=pipeline,
    )
    duration_ms = (time.time() - _t0) * 1000
    return prep_result, duration_ms


async def run_execution(
    executor: ExecutorAgent,
    executor_input: str,
    system_prompt: str = "",
    **kwargs: Any,
) -> tuple[Any, float]:
    """Run the large-LLM execution step. Returns (exec_result, duration_ms)."""
    _t0 = time.time()
    exec_result = await executor.execute(
        executor_input=executor_input,
        system_prompt=system_prompt,
        **kwargs,
    )
    duration_ms = (time.time() - _t0) * 1000
    return exec_result, duration_ms


async def persist_session(
    user_memory: Any,
    query: str,
    exec_result: Any,
) -> None:
    """Persist interaction to UserMemory if available."""
    if not user_memory:
        return
    try:
        content = exec_result.content or ""
        await user_memory.add_interaction(
            query=query,
            response_summary=content[:500],
            metadata={"model": exec_result.model_used},
        )
        # Auto-learn preferences from interaction
        await user_memory.learn_preference_from_interaction(query, content)
    except Exception as e:
        logger.warning(f"Session persistence failed: {e}")


def record_trace(
    trace: Any,
    pipeline: str,
    small_llm: str,
    large_llm: str,
    query: str,
    extra_context: dict[str, Any],
    prep_result: Any,
    exec_result: Any,
    prep_duration_ms: float,
    exec_duration_ms: float,
) -> None:
    """Record preprocessing and execution steps to trace."""
    if not trace:
        return

    # Record individual pipeline steps from preprocessor
    if prep_result.decomposition and prep_result.decomposition.steps_executed:
        for ps in prep_result.decomposition.steps_executed:
            step_type = "context_collection" if ps.step_type == "algo" and ps.step_name in (
                "collect_runtime", "inject_session", "sanitize"
            ) else ("pipeline_step" if ps.step_type == "algo" else "llm_call")
            trace.step(
                name=f"Pipeline: {ps.step_name}",
                step_type=step_type,
                description=f"{ps.step_type} step in '{pipeline}' pipeline",
                outputs={ps.output_key: ps.output_value} if ps.output_key else {},
                status="skipped" if ps.skipped else ("error" if ps.error else "ok"),
                error=ps.error,
            )
    trace.step(
        name="PreprocessorAgent.preprocess()",
        step_type="agent",
        description=f"Small LLM ({small_llm}) preprocessed query using '{pipeline}' strategy.",
        inputs={"query": query, "pipeline": pipeline, "user_context": extra_context},
        outputs={"executor_input": prep_result.executor_input},
        duration_ms=prep_duration_ms,
    )

    trace.step(
        name="ExecutorAgent.execute()",
        step_type="llm_call",
        description=f"Large LLM ({large_llm}) generated final response.",
        inputs={"executor_input": prep_result.executor_input},
        outputs={"content_preview": exec_result.content or "", "model": exec_result.model_used},
        duration_ms=exec_duration_ms,
        metadata={"retries": exec_result.retries},
    )
