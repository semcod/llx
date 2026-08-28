"""Planfile MCP tools: strategy generation and application."""

from mcp.types import Tool

from llx.mcp.tools.approval import approval_response, file_sha256, resolve_workspace_path
from llx.mcp.tools.base import McpTool


async def _handle_planfile_generate(args: dict) -> dict:
    """Generate a strategy.yaml refactoring plan using LLM + project metrics."""
    try:
        from planfile.llm.generator import generate_strategy
        from planfile.loaders.yaml_loader import save_strategy_yaml

        project_path = args.get("project_path", ".")
        model = args.get("model")
        sprints = max(1, min(int(args.get("sprints", 3)), 100))
        focus = args.get("focus")

        strategy = generate_strategy(project_path, model=model, sprints=sprints, focus=focus)

        # Save to temporary file if no output specified
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            save_strategy_yaml(strategy, f.name)

        return {
            "success": True,
            "strategy_file": f.name,
            "sprints": len(strategy.get("sprints", [])),
            "focus": focus,
            "model": model,
        }
    except ImportError:
        return {
            "success": False,
            "error": "planfile not installed. Install with: pip install planfile",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


tool_planfile_generate = McpTool(
    definition=Tool(
        name="planfile_generate",
        description="Generate a strategy.yaml refactoring plan using LLM + project metrics.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "default": ".",
                    "description": "Project path to analyze",
                },
                "model": {"type": "string", "description": "LLM model to use for generation"},
                "sprints": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 3,
                    "description": "Number of sprints to plan",
                },
                "focus": {
                    "type": "string",
                    "enum": ["complexity", "duplication", "tests", "docs"],
                    "description": "Focus area for refactoring",
                },
            },
        },
    ),
    handler=_handle_planfile_generate,
)


async def _handle_planfile_apply(args: dict) -> dict:
    """Preview a strategy by default; applying it requires operator approval."""
    try:
        from llx.planfile.executor import execute_strategy

        strategy_path = args.get("strategy_path")
        project_path = str(args.get("project_path", "."))
        sprint = args.get("sprint")
        dry_run = bool(args.get("dry_run", True))
        actor = str(args.get("actor") or "")
        supplied_hash = str(args.get("approval_hash") or "")

        if not strategy_path:
            return {"success": False, "error": "strategy_path is required"}
        project = resolve_workspace_path(".", project_path, must_exist=True)
        strategy = resolve_workspace_path(str(strategy_path), str(project), must_exist=True)
        if not strategy.is_file():
            return {"success": False, "error": f"strategy_path is not a file: {strategy}"}

        approval = approval_response(
            "planfile_apply",
            {
                "project_path": str(project),
                "strategy_path": str(strategy),
                "strategy_sha256": file_sha256(strategy),
                "sprint": sprint,
            },
            actor=actor,
            supplied_hash=supplied_hash,
        )
        if not dry_run and approval["requires_approval"]:
            return {
                "success": False,
                "status": "approval_required",
                **approval,
                "message": (
                    "Enable LLX_MCP_ALLOW_WRITE=1 and repeat with actor plus the exact "
                    "approval_hash."
                ),
            }

        results = execute_strategy(
            strategy_path=str(strategy),
            project_path=str(project),
            sprint_filter=sprint,
            dry_run=dry_run,
        )

        # Summarize results
        total = len(results)
        success = sum(1 for r in results if r.status == "success")
        failed = sum(1 for r in results if r.status == "failed")

        return {
            "success": True,
            "total_tasks": total,
            "successful": success,
            "failed": failed,
            "dry_run": dry_run,
            **approval,
            "results": [
                {
                    "task": r.task_name,
                    "status": r.status,
                    "model": r.model_used,
                    "error": r.error,
                }
                for r in results
            ],
        }
    except ImportError as e:
        return {"success": False, "error": f"planfile not installed: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


tool_planfile_apply = McpTool(
    definition=Tool(
        name="planfile_apply",
        description=(
            "Preview strategy.yaml by default. Live execution requires operator capability and "
            "actor-bound approval of the exact strategy file."
        ),
        inputSchema={
            "type": "object",
            "required": ["strategy_path"],
            "properties": {
                "strategy_path": {"type": "string", "description": "Path to strategy.yaml file"},
                "project_path": {
                    "type": "string",
                    "default": ".",
                    "description": "Project root path",
                },
                "sprint": {
                    "type": "integer",
                    "description": "Execute only specific sprint (optional)",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Preview without execution",
                },
                "actor": {"type": "string", "description": "Approver identity"},
                "approval_hash": {
                    "type": "string",
                    "description": "Hash returned by the preceding preview or approval response",
                },
            },
        },
    ),
    handler=_handle_planfile_apply,
)
