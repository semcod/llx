from __future__ import annotations

from pathlib import Path
from typing import Callable, Any

import yaml

from llx.prellm.llm_provider import LLMProvider
from llx.prellm.pipeline.config import PipelineConfig, PipelineStep
from llx.prellm.prompt_registry import PromptRegistry

_DEFAULT_PIPELINES_PATH = Path(__file__).resolve().parent.parent / "configs" / "pipelines.yaml"


def load_pipeline_config(pipelines_path: Path | str | None, pipeline_name: str) -> PipelineConfig:
    path = Path(pipelines_path) if pipelines_path else _DEFAULT_PIPELINES_PATH

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    pipelines_raw = raw.get("pipelines", {})
    if pipeline_name not in pipelines_raw:
        available = sorted(pipelines_raw.keys())
        raise KeyError(f"Pipeline '{pipeline_name}' not found. Available: {available}")

    pipe_data = pipelines_raw[pipeline_name]
    steps: list[PipelineStep] = []
    for step_raw in pipe_data.get("steps", []):
        input_val = step_raw.get("input", "query")
        steps.append(
            PipelineStep(
                name=step_raw["name"],
                prompt=step_raw.get("prompt"),
                type=step_raw.get("type"),
                input=input_val,
                output=step_raw.get("output", ""),
                condition=step_raw.get("condition"),
                parallel=step_raw.get("parallel", False),
                config=step_raw.get("config", {}),
                output_schema=step_raw.get("schema"),
            )
        )

    return PipelineConfig(
        name=pipeline_name,
        description=pipe_data.get("description", ""),
        steps=steps,
    )


def build_pipeline(
    config: PipelineConfig,
    registry: PromptRegistry | None,
    small_llm: LLMProvider | None,
    validators: dict[str, Callable[..., Any]] | None,
    pipeline_cls: type,
):
    return pipeline_cls(
        config=config,
        registry=registry or PromptRegistry(),
        small_llm=small_llm,  # type: ignore[arg-type]
        validators=validators,
    )
