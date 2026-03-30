"""MCP fix/refactor workflow orchestration for llx.

Upstreamed from pyqual — provides LlxMcpRunResult and the async
run_llx_fix_workflow / run_llx_refactor_workflow functions that drive
the analyze → prompt → aider pipeline via the MCP client.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from llx.mcp.client import LlxMcpClient
from llx.utils.issues import (
    build_fix_prompt,
    resolve_issue_source,
    task_prompt_label,
)

DEFAULT_ISSUES_PATH = ".pyqual/errors.json"
DEFAULT_OUTPUT_PATH = ".pyqual/llx_mcp.json"


@dataclass
class LlxMcpRunResult:
    """Result of an llx MCP fix/refactor workflow."""

    success: bool
    endpoint: str
    project_path: str
    issues_path: str
    prompt: str
    tool_calls: int
    analysis: dict[str, Any] | None = None
    aider: dict[str, Any] | None = None
    issues: dict[str, Any] | list[dict[str, Any]] | None = None
    model: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for JSON output."""
        return asdict(self)


async def run_llx_fix_workflow(
    workdir: Path,
    project_path: str,
    issues_path: Path,
    output_path: Path,
    endpoint_url: str | None = None,
    model: str | None = None,
    files: list[str] | None = None,
    use_docker: bool = False,
    docker_args: list[str] | None = None,
    task: str = "quick_fix",
) -> LlxMcpRunResult:
    """Run the analysis + fix/refactor workflow and save a JSON report."""
    client = LlxMcpClient(endpoint_url=endpoint_url)
    resolved_issues_path, issues = resolve_issue_source(workdir, issues_path)

    try:
        analysis_response = await client.analyze(project_path, task=task)
        analysis_data = analysis_response.get("data")
        if not isinstance(analysis_data, dict):
            analysis_data = {"raw": analysis_response.get("text", "")}

        prompt = build_fix_prompt(
            Path(project_path),
            issues,
            analysis_data,
            action_label=task_prompt_label(task),
        )
        selected_model = model
        if not selected_model:
            selection = analysis_data.get("selection") if isinstance(analysis_data, dict) else None
            if isinstance(selection, dict):
                selected_model = selection.get("model_id")

        aider_response = await client.fix_with_aider(
            project_path=project_path,
            prompt=prompt,
            model=selected_model,
            files=files or [],
            use_docker=use_docker,
            docker_args=docker_args,
        )
        aider_data = aider_response.get("data")
        if not isinstance(aider_data, dict):
            aider_data = {"raw": aider_response.get("text", "")}

        success = bool(aider_data.get("success"))
        result = LlxMcpRunResult(
            success=success,
            endpoint=client.endpoint_url,
            project_path=project_path,
            issues_path=str(resolved_issues_path),
            prompt=prompt,
            tool_calls=2,
            analysis=analysis_data,
            aider=aider_data,
            issues=issues,
            model=selected_model,
        )
    except Exception as exc:
        result = LlxMcpRunResult(
            success=False,
            endpoint=client.endpoint_url,
            project_path=project_path,
            issues_path=str(resolved_issues_path),
            prompt="",
            tool_calls=0,
            issues=issues,
            error=str(exc),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return result


async def run_llx_refactor_workflow(
    workdir: Path,
    project_path: str,
    issues_path: Path,
    output_path: Path,
    endpoint_url: str | None = None,
    model: str | None = None,
    files: list[str] | None = None,
    use_docker: bool = False,
    docker_args: list[str] | None = None,
) -> LlxMcpRunResult:
    """Run the llx refactor workflow and save a JSON report."""
    return await run_llx_fix_workflow(
        workdir=workdir,
        project_path=project_path,
        issues_path=issues_path,
        output_path=output_path,
        endpoint_url=endpoint_url,
        model=model,
        files=files,
        use_docker=use_docker,
        docker_args=docker_args,
        task="refactor",
    )
