from __future__ import annotations

import logging
from typing import Any, Callable

from llx.prellm._nfo_compat import log_call
from llx.prellm.llm_provider import LLMProvider
from llx.prellm.pipeline.algo_handlers import AlgoHandlersMixin
from llx.prellm.pipeline.config import PipelineConfig, PipelineResult, StepExecutionResult
from llx.prellm.prompt_registry import PromptRegistry

logger = logging.getLogger("prellm.pipeline")


class PromptPipeline(AlgoHandlersMixin):
    """Generic pipeline — executes a sequence of LLM + algorithmic steps."""

    def __init__(
        self,
        config: PipelineConfig,
        registry: PromptRegistry,
        small_llm: LLMProvider,
        validators: dict[str, Callable[..., Any]] | None = None,
    ):
        self.config = config
        self.registry = registry
        self.small_llm = small_llm
        self._algo_handlers = self._build_algo_handlers(validators)

    @classmethod
    def from_yaml(
        cls,
        pipelines_path,
        pipeline_name: str,
        registry: PromptRegistry | None = None,
        small_llm: LLMProvider | None = None,
        validators: dict[str, Callable[..., Any]] | None = None,
    ) -> PromptPipeline:
        from llx.prellm.pipeline.loader import build_pipeline, load_pipeline_config

        config = load_pipeline_config(pipelines_path, pipeline_name)
        return build_pipeline(config, registry, small_llm, validators, cls)

    @log_call
    async def execute(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> PipelineResult:
        state: dict[str, Any] = {"query": query, "context": context or {}}
        steps_executed: list[StepExecutionResult] = []

        for step in self.config.steps:
            step_result = StepExecutionResult(step_name=step.name, output_key=step.output)

            if step.condition and not self._evaluate_condition(step.condition, state):
                step_result.skipped = True
                steps_executed.append(step_result)
                logger.debug(f"Step '{step.name}' skipped (condition not met)")
                continue

            try:
                if step.prompt:
                    step_result.step_type = "llm"
                    result = await self._execute_llm_step(step, state)
                elif step.type:
                    step_result.step_type = "algo"
                    result = self._execute_algo_step(step, state)
                else:
                    logger.warning(f"Step '{step.name}' has neither prompt nor type — skipping")
                    step_result.skipped = True
                    steps_executed.append(step_result)
                    continue

                if step.output:
                    state[step.output] = result
                step_result.output_value = result

            except Exception as e:
                step_result.error = str(e)
                step_result.skipped = True
                steps_executed.append(step_result)
                return PipelineResult(
                    state=state,
                    steps_executed=steps_executed,
                    pipeline_name=self.config.name,
                    success=False,
                    error=str(e),
                )

            steps_executed.append(step_result)

        return PipelineResult(
            state=state,
            steps_executed=steps_executed,
            pipeline_name=self.config.name,
            success=True,
        )

    def _evaluate_condition(self, condition: str, state: dict[str, Any]) -> bool:
        return bool(state.get(condition))

    async def _execute_llm_step(self, step: Any, state: dict[str, Any]) -> Any:
        prompt = self.registry.get(step.prompt)
        return await self.small_llm.generate(prompt, state)
