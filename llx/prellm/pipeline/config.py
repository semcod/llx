from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PipelineStep(BaseModel):
    """Configuration for a single pipeline step."""

    name: str
    prompt: str | None = None
    type: str | None = None
    input: str | list[str] = "query"
    output: str = ""
    condition: str | None = None
    parallel: bool = False
    config: dict[str, Any] = Field(default_factory=dict)
    output_schema: str | None = None


class PipelineConfig(BaseModel):
    """Configuration for a complete pipeline."""

    name: str
    description: str = ""
    steps: list[PipelineStep] = Field(default_factory=list)


class StepExecutionResult(BaseModel):
    """Result of executing a single pipeline step."""

    step_name: str
    step_type: str = "llm"
    output_key: str = ""
    output_value: Any = None
    skipped: bool = False
    error: str | None = None


class PipelineResult(BaseModel):
    """Result of executing a full pipeline."""

    state: dict[str, Any] = Field(default_factory=dict)
    steps_executed: list[StepExecutionResult] = Field(default_factory=list)
    pipeline_name: str = ""
    success: bool = True
    error: str | None = None
