from pathlib import Path
from typing import Optional
import typer
from llx.config import LlxConfig
from llx.routing.selector import ModelTier, select_with_context_check
from llx.cli.formatters import output_json, output_rich

def analyze(
    path: str = typer.Argument(".", help="Project path to analyze"),
    toon_dir: Optional[str] = typer.Option(None, "--toon-dir", "-t", help="Directory with .toon files"),
    task: Optional[str] = typer.Option(None, "--task", help="Task hint: refactor, explain, quick_fix, review"),
    local: bool = typer.Option(False, "--local", "-l", help="Force local model"),
    max_tier: Optional[str] = typer.Option(None, "--max-tier", help="Max tier: free, cheap, balanced, premium"),
    run_tools: bool = typer.Option(False, "--run", "-r", help="Run code2llm/redup/vallm first"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    from llx.cli.app import _run_analysis_tools, analyze_project, console
    project_path = Path(path).resolve()
    config = LlxConfig.load(project_path)
    config.verbose = config.verbose or verbose
    if run_tools:
        _run_analysis_tools(project_path, config)
    with console.status("Collecting project metrics..."):
        metrics = analyze_project(project_path, toon_dir=toon_dir)
    tier_limit = ModelTier(max_tier) if max_tier else None
    result = select_with_context_check(metrics, config, prefer_local=local, max_tier=tier_limit, task_hint=task)
    if json_output:
        output_json(metrics, result)
    else:
        output_rich(metrics, result, verbose)