import os, re, yaml, logging, typer
from pathlib import Path
from typing import Optional
from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage
from llx.planfile.model_selector import ModelSelector, FREE_FILTER, CHEAP_FILTER, BALANCED_FILTER, LOCAL_FILTER

def _plan_code_impl(strategy: str, out: Path, model: Optional[str], profile: Optional[str]) -> None:
    from llx.cli.app import console
    if profile is None: profile = os.getenv("LLX_DEFAULT_PROFILE", "cheap")
    out.mkdir(parents=True, exist_ok=True)
    with open(strategy, encoding="utf-8") as f: strat = yaml.safe_load(f)
    project_name = strat.get("project_name") or strat.get("name", "My Project")
    description = strat.get("description") or strat.get("goal", {}).get("description", "")
    selector = ModelSelector(".")
    selected_model = model or selector.select_model({"free": FREE_FILTER, "cheap": CHEAP_FILTER, "balanced": BALANCED_FILTER, "local": LOCAL_FILTER}.get(profile or "free", FREE_FILTER))
    if not selected_model:
        console.print("[red]No model available.[/red]"); raise typer.Exit(1)
    config = LlxConfig.load(".")
    if config.code_tool == "aider": return
    logging.getLogger("litellm").setLevel(logging.WARNING)
    with LlxClient(config) as client:
        for sprint in strat.get("sprints", []):
            # ... (logic for generation) ...
            pass