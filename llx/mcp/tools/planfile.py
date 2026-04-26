"""Planfile MCP tools: strategy generation and application."""

from pathlib import Path
from mcp.types import Tool

from llx.mcp.tools.base import McpTool


async def _handle_planfile_generate(args: dict) -> dict:
    """Generate a strategy.yaml refactoring plan using LLM + project metrics."""
    try:
        from planfile.llm.generator import generate_strategy
        from planfile.loaders.yaml_loader import save_strategy_yaml

        project_path = args.get("project_path", ".")
        model = args.get("model")
        sprints = args.get("sprints", 3)
        focus = args.get("focus")

        strategy = generate_strategy(project_path, model=model, sprints=sprints, focus=focus)

        # Save to temporary file if no output specified
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            save_strategy_yaml(strategy, f.name)

        return {
            "success": True,
            "strategy_file": f.name,
            "sprints": len(strategy.get("sprints", [])),
            "focus": focus,
            "model": model
        }
    except ImportError:
        return {
            "success": False,
            "error": "planfile not installed. Install with: pip install planfile"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


tool_planfile_generate = McpTool(
    definition=Tool(
        name="planfile_generate",
        description="Generate a strategy.yaml refactoring plan using LLM + project metrics.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "default": ".", "description": "Project path to analyze"},
                "model": {"type": "string", "description": "LLM model to use for generation"},
                "sprints": {"type": "integer", "default": 3, "description": "Number of sprints to plan"},
                "focus": {"type": "string", "enum": ["complexity", "duplication", "tests", "docs"], "description": "Focus area for refactoring"},
            },
        },
    ),
    handler=_handle_planfile_generate,
)


async def _handle_planfile_apply(args: dict) -> dict:
    """Apply strategy.yaml — execute each task with optimal model selection."""
    try:
        from llx.planfile.executor import execute_strategy

        strategy_path = args.get("strategy_path")
        project_path = args.get("project_path", ".")
        sprint = args.get("sprint")
        dry_run = args.get("dry_run", False)

        if not strategy_path:
            return {
                "success": False,
                "error": "strategy_path is required"
            }

        results = execute_strategy(
            strategy_path=strategy_path,
            project_path=project_path,
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
            "results": [
                {
                    "task": r.task_name,
                    "status": r.status,
                    "model": r.model_used,
                    "error": r.error,
                }
                for r in results
            ]
        }
    except ImportError as e:
        return {
            "success": False,
            "error": f"planfile not installed: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


tool_planfile_apply = McpTool(
    definition=Tool(
        name="planfile_apply",
        description="Execute strategy.yaml plan — each task with automatic model selection based on complexity and context.",
        inputSchema={
            "type": "object",
            "required": ["strategy_path"],
            "properties": {
                "strategy_path": {"type": "string", "description": "Path to strategy.yaml file"},
                "project_path": {"type": "string", "default": ".", "description": "Project root path"},
                "sprint": {"type": "integer", "description": "Execute only specific sprint (optional)"},
                "dry_run": {"type": "boolean", "default": False, "description": "Preview without execution"},
            },
        },
    ),
    handler=_handle_planfile_apply,
)
