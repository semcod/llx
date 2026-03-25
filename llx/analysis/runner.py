"""Run external analysis tools and collect fresh output.

Lesson from preLLM: query() function (CC=27) mixed tool invocation
with result processing. Here each tool is a separate function.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class ToolResult:
    tool: str
    success: bool
    output_dir: Path | None = None
    error: str | None = None


def check_tool(name: str) -> bool:
    """Check if a CLI tool is available on PATH."""
    return shutil.which(name) is not None


def _run_tool(
    tool: str, cmd: list[str], output_dir: Path, timeout: int = 120,
) -> ToolResult:
    """Generic tool runner with timeout and error handling."""
    if not check_tool(tool):
        return ToolResult(tool=tool, success=False, error=f"{tool} not found on PATH")
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return ToolResult(tool=tool, success=True, output_dir=output_dir)
        return ToolResult(tool=tool, success=False, error=result.stderr[:500])
    except subprocess.TimeoutExpired:
        return ToolResult(tool=tool, success=False, error=f"Timed out after {timeout}s")
    except Exception as e:
        return ToolResult(tool=tool, success=False, error=str(e))


def run_code2llm(project_path: Path, output_dir: Path, fmt: str = "toon") -> ToolResult:
    return _run_tool("code2llm", [
        "code2llm", str(project_path), "-f", fmt, "-o", str(output_dir),
    ], output_dir)


def run_redup(project_path: Path, output_dir: Path, fmt: str = "json") -> ToolResult:
    return _run_tool("redup", [
        "redup", "scan", str(project_path), "--format", fmt, "--output", str(output_dir),
    ], output_dir)


def run_vallm(project_path: Path, output_dir: Path) -> ToolResult:
    return _run_tool("vallm", [
        "vallm", "batch", str(project_path), "--recursive",
        "--no-imports", "--no-complexity", "--format", "json",
    ], output_dir)


def run_all_tools(
    project_path: Path,
    output_dir: Path | None = None,
    on_progress: Callable[[str, str], None] | None = None,
) -> dict[str, ToolResult]:
    out = output_dir or (project_path / ".llx")
    results: dict[str, ToolResult] = {}
    for name, runner in [("code2llm", run_code2llm), ("redup", run_redup), ("vallm", run_vallm)]:
        if on_progress:
            on_progress(name, "starting")
        results[name] = runner(project_path, out / name)
        if on_progress:
            status = "done" if results[name].success else f"failed: {results[name].error}"
            on_progress(name, status)
    return results
