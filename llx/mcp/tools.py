"""MCP tool definitions for llx.

Each tool wraps one CLI command or external tool invocation.
Tools return JSON-serializable dicts — the MCP server wraps them as TextContent.
"""

from dataclasses import dataclass
from typing import Any, Callable, Coroutine
from pathlib import Path

from mcp.types import Tool


@dataclass
class McpTool:
    definition: Tool
    handler: Callable[[dict], Coroutine[Any, Any, dict]]


# ─── llx_analyze ─────────────────────────────────────────────

async def _handle_llx_analyze(args: dict) -> dict:
    """Analyze project and recommend model."""
    from llx.analysis.collector import analyze_project
    from llx.routing.selector import select_with_context_check
    from llx.config import LlxConfig

    path = args.get("path", ".")
    toon_dir = args.get("toon_dir")
    task_hint = args.get("task")

    config = LlxConfig.load(path)
    metrics = analyze_project(path, toon_dir=toon_dir)
    result = select_with_context_check(metrics, config, task_hint=task_hint)

    return {
        "metrics": {
            "total_files": metrics.total_files,
            "total_lines": metrics.total_lines,
            "total_functions": metrics.total_functions,
            "avg_cc": metrics.avg_cc,
            "max_cc": metrics.max_cc,
            "critical_count": metrics.critical_count,
            "god_modules": metrics.god_modules,
            "max_fan_out": metrics.max_fan_out,
            "dependency_cycles": metrics.dependency_cycles,
            "task_scope": metrics.task_scope,
        },
        "selection": {
            "tier": result.tier.value,
            "model_id": result.model_id,
            "reasons": result.reasons,
        },
    }

tool_llx_analyze = McpTool(
    definition=Tool(
        name="llx_analyze",
        description="Analyze a project and recommend the optimal LLM model based on code metrics (files, complexity, coupling, duplication).",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path to analyze", "default": "."},
                "toon_dir": {"type": "string", "description": "Directory with .toon analysis files (optional)"},
                "task": {"type": "string", "enum": ["refactor", "explain", "quick_fix", "review"], "description": "Task hint for model selection"},
            },
        },
    ),
    handler=_handle_llx_analyze,
)


# ─── llx_select ──────────────────────────────────────────────

async def _handle_llx_select(args: dict) -> dict:
    """Quick model selection."""
    from llx.analysis.collector import analyze_project
    from llx.routing.selector import select_model
    from llx.config import LlxConfig

    path = args.get("path", ".")
    config = LlxConfig.load(path)
    metrics = analyze_project(path, toon_dir=args.get("toon_dir"))
    result = select_model(metrics, config, task_hint=args.get("task"))
    return {"tier": result.tier.value, "model_id": result.model_id, "reasons": result.reasons}

tool_llx_select = McpTool(
    definition=Tool(
        name="llx_select",
        description="Quick model selection from existing analysis files. Returns tier and model_id.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "toon_dir": {"type": "string"},
                "task": {"type": "string", "enum": ["refactor", "explain", "quick_fix", "review"]},
            },
        },
    ),
    handler=_handle_llx_select,
)


# ─── llx_chat ────────────────────────────────────────────────

async def _handle_llx_chat(args: dict) -> dict:
    """Analyze + select model + send prompt."""
    from llx.analysis.collector import analyze_project
    from llx.routing.selector import select_with_context_check
    from llx.routing.client import LlxClient, ChatMessage
    from llx.integrations.context_builder import build_context
    from llx.config import LlxConfig

    path = args.get("path", ".")
    prompt = args["prompt"]
    config = LlxConfig.load(path)
    metrics = analyze_project(path, toon_dir=args.get("toon_dir"))
    result = select_with_context_check(metrics, config, task_hint=args.get("task"))
    model_id = args.get("model") or result.model_id
    context = build_context(Path(path), metrics, result.tier)

    with LlxClient(config) as client:
        response = client.chat_with_context(prompt, context, model=model_id)

    return {
        "model": model_id,
        "tier": result.tier.value,
        "response": response.content,
        "usage": response.usage,
    }

tool_llx_chat = McpTool(
    definition=Tool(
        name="llx_chat",
        description="Analyze project, auto-select the best model, and send a prompt with project context.",
        inputSchema={
            "type": "object",
            "required": ["prompt"],
            "properties": {
                "prompt": {"type": "string", "description": "The prompt to send to the LLM"},
                "path": {"type": "string", "default": "."},
                "toon_dir": {"type": "string"},
                "task": {"type": "string", "enum": ["refactor", "explain", "quick_fix", "review"]},
                "model": {"type": "string", "description": "Override model selection"},
            },
        },
    ),
    handler=_handle_llx_chat,
)


# ─── code2llm_analyze ────────────────────────────────────────

async def _handle_code2llm_analyze(args: dict) -> dict:
    """Run code2llm analysis on a project."""
    from llx.analysis.runner import run_code2llm
    path = Path(args.get("path", "."))
    output_dir = Path(args.get("output_dir", str(path / ".llx" / "code2llm")))
    fmt = args.get("format", "toon")
    result = run_code2llm(path, output_dir, fmt=fmt)
    return {"success": result.success, "output_dir": str(result.output_dir), "error": result.error}

tool_code2llm_analyze = McpTool(
    definition=Tool(
        name="code2llm_analyze",
        description="Run code2llm static analysis on a project. Generates .toon files with health diagnostics, complexity metrics, and refactoring recommendations.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path to analyze", "default": "."},
                "output_dir": {"type": "string", "description": "Where to write .toon output files"},
                "format": {"type": "string", "enum": ["toon", "all", "context", "evolution"], "default": "toon"},
            },
        },
    ),
    handler=_handle_code2llm_analyze,
)


# ─── redup_scan ───────────────────────────────────────────────

async def _handle_redup_scan(args: dict) -> dict:
    """Run redup duplication scan."""
    from llx.analysis.runner import run_redup
    path = Path(args.get("path", "."))
    output_dir = Path(args.get("output_dir", str(path / ".llx" / "redup")))
    fmt = args.get("format", "json")
    result = run_redup(path, output_dir, fmt=fmt)
    return {"success": result.success, "output_dir": str(result.output_dir), "error": result.error}

tool_redup_scan = McpTool(
    definition=Tool(
        name="redup_scan",
        description="Run redup duplication analysis. Finds duplicate functions, blocks, and structural clones. Generates prioritized refactoring map.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "output_dir": {"type": "string"},
                "format": {"type": "string", "enum": ["json", "yaml", "toon"], "default": "json"},
            },
        },
    ),
    handler=_handle_redup_scan,
)


# ─── vallm_validate ──────────────────────────────────────────

async def _handle_vallm_validate(args: dict) -> dict:
    """Run vallm validation on code or project."""
    if "code" in args:
        # Single-file validation via Python API
        try:
            from vallm import Proposal, validate
            proposal = Proposal(code=args["code"], language=args.get("language", "python"))
            result = validate(proposal)
            return {
                "verdict": result.verdict.value,
                "score": result.weighted_score,
                "issues": [{"message": i.message, "severity": i.severity} for i in result.issues],
            }
        except ImportError:
            return {"error": "vallm package not installed. pip install llx[vallm]"}
    else:
        # Batch project validation via CLI
        from llx.analysis.runner import run_vallm
        path = Path(args.get("path", "."))
        output_dir = Path(args.get("output_dir", str(path / ".llx" / "vallm")))
        result = run_vallm(path, output_dir)
        return {"success": result.success, "output_dir": str(result.output_dir), "error": result.error}

tool_vallm_validate = McpTool(
    definition=Tool(
        name="vallm_validate",
        description="Validate code quality. Either pass 'code' for single-file validation (syntax, imports, complexity, security) or 'path' for batch project validation.",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code to validate (single-file mode)"},
                "language": {"type": "string", "default": "python"},
                "path": {"type": "string", "description": "Project path for batch validation"},
                "output_dir": {"type": "string"},
            },
        },
    ),
    handler=_handle_vallm_validate,
)


# ─── llx_preprocess ──────────────────────────────────────────

async def _handle_llx_preprocess(args: dict) -> dict:
    """Preprocess a query using preLLM's small→large LLM pipeline."""
    from llx.prellm.core import preprocess_and_execute

    query = args["query"]
    small_llm = args.get("small_llm", "ollama/qwen2.5:3b")
    large_llm = args.get("large_llm", "gpt-4o-mini")
    strategy = args.get("strategy", "auto")
    execute = args.get("execute", False)

    result = await preprocess_and_execute(
        query=query,
        small_llm=small_llm,
        large_llm=large_llm,
        strategy=strategy,
        skip_execution=not execute,
    )

    output = {
        "content": result.content,
        "model_used": result.model_used,
        "small_model_used": result.small_model_used,
    }
    if result.decomposition:
        output["decomposition"] = {
            "strategy": result.decomposition.strategy.value,
            "composed_prompt": result.decomposition.composed_prompt,
            "sub_queries": result.decomposition.sub_queries,
            "matched_rule": result.decomposition.matched_rule,
        }
        if result.decomposition.classification:
            output["decomposition"]["classification"] = {
                "intent": result.decomposition.classification.intent,
                "confidence": result.decomposition.classification.confidence,
                "domain": result.decomposition.classification.domain,
            }
    return output

tool_llx_preprocess = McpTool(
    definition=Tool(
        name="llx_preprocess",
        description="Preprocess a query using preLLM's two-agent pipeline: small LLM classifies/decomposes the query, optionally large LLM executes it. Returns decomposition details and optional response.",
        inputSchema={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "description": "The query to preprocess"},
                "small_llm": {"type": "string", "description": "Small LLM model (default: ollama/qwen2.5:3b)"},
                "large_llm": {"type": "string", "description": "Large LLM model (default: gpt-4o-mini)"},
                "strategy": {"type": "string", "enum": ["auto", "classify", "structure", "split", "enrich", "passthrough"], "default": "auto"},
                "execute": {"type": "boolean", "description": "Also execute with large LLM (default: false, decompose only)", "default": False},
            },
        },
    ),
    handler=_handle_llx_preprocess,
)


# ─── llx_context ────────────────────────────────────────────

async def _handle_llx_context(args: dict) -> dict:
    """Gather preLLM context for a project (shell, codebase, sensitive filter)."""
    from llx.prellm.context.shell_collector import ShellContextCollector
    from llx.prellm.context.sensitive_filter import SensitiveDataFilter

    sections = {}

    # Shell context
    collector = ShellContextCollector()
    shell_ctx = collector.collect_all()
    sections["shell"] = {
        "env_vars_count": len(shell_ctx.env_vars),
        "pid": shell_ctx.process.pid,
        "cwd": shell_ctx.process.cwd,
        "shell": shell_ctx.shell.name if shell_ctx.shell else "unknown",
    }

    # Codebase compression (if path provided)
    path = args.get("path")
    if path:
        try:
            from llx.prellm.context.folder_compressor import FolderCompressor
            compressor = FolderCompressor()
            compressed = compressor.compress(path)
            sections["codebase"] = {
                "total_files": compressed.total_files,
                "total_lines": compressed.total_lines,
                "estimated_tokens": compressed.estimated_tokens,
                "languages": compressed.languages,
            }
        except Exception as e:
            sections["codebase"] = {"error": str(e)}

    # Sensitive data scan
    sf = SensitiveDataFilter()
    report = sf.scan_environment()
    sections["sensitive"] = {
        "masked_keys": report.masked_keys,
        "blocked_keys": report.blocked_keys,
    }

    return sections

tool_llx_context = McpTool(
    definition=Tool(
        name="llx_context",
        description="Gather runtime context: shell environment, codebase structure, and sensitive data scan. Useful for understanding what context is available for LLM queries.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project path for codebase analysis (optional)"},
            },
        },
    ),
    handler=_handle_llx_context,
)


# ─── llx_proxy_status ────────────────────────────────────────

async def _handle_llx_proxy_status(args: dict) -> dict:
    """Check LiteLLM proxy status."""
    from llx.integrations.proxy import check_proxy
    from llx.config import LlxConfig
    config = LlxConfig.load(args.get("path", "."))
    url = args.get("url", config.litellm_base_url)
    running = check_proxy(url)
    return {"running": running, "url": url}

tool_llx_proxy_status = McpTool(
    definition=Tool(
        name="llx_proxy_status",
        description="Check if the LiteLLM proxy is running and accessible.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "url": {"type": "string", "description": "Proxy URL to check"},
            },
        },
    ),
    handler=_handle_llx_proxy_status,
)


# ─── llx_proxym_status ──────────────────────────────────────

async def _handle_llx_proxym_status(args: dict) -> dict:
    """Get detailed proxym proxy status."""
    from llx.integrations.proxym import ProxymClient
    from llx.config import LlxConfig
    config = LlxConfig.load(args.get("path", "."))
    url = args.get("url", config.litellm_base_url)
    client = ProxymClient(config, base_url=url)
    try:
        status = client.status()
        result = {
            "available": status.available,
            "url": status.url,
        }
        if status.available:
            result["version"] = status.version
            result["models_count"] = status.models_count
            if status.providers:
                result["providers"] = status.providers
            if status.daily_remaining is not None:
                result["daily_remaining_usd"] = status.daily_remaining
            if status.monthly_remaining is not None:
                result["monthly_remaining_usd"] = status.monthly_remaining
        else:
            result["error"] = status.error
        return result
    finally:
        client.close()

tool_llx_proxym_status = McpTool(
    definition=Tool(
        name="llx_proxym_status",
        description="Get detailed status of proxym intelligent AI proxy: availability, version, model count, providers, and budget remaining.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "url": {"type": "string", "description": "Proxym URL to check"},
            },
        },
    ),
    handler=_handle_llx_proxym_status,
)


# ─── llx_proxym_chat ────────────────────────────────────────

async def _handle_llx_proxym_chat(args: dict) -> dict:
    """Analyze project + route through proxym with metrics headers."""
    from llx.integrations.proxym import ProxymClient

    path = args.get("path", ".")
    prompt = args["prompt"]

    client = ProxymClient()
    try:
        response = client.chat_with_analysis(
            prompt,
            project_path=path,
            toon_dir=args.get("toon_dir"),
            task_hint=args.get("task"),
            model=args.get("model"),
        )
        return {
            "model": response.model,
            "content": response.content,
            "usage": response.usage,
        }
    finally:
        client.close()

tool_llx_proxym_chat = McpTool(
    definition=Tool(
        name="llx_proxym_chat",
        description="Analyze project metrics, select optimal tier, and route through proxym with code-metrics-aware headers for intelligent model selection.",
        inputSchema={
            "type": "object",
            "required": ["prompt"],
            "properties": {
                "prompt": {"type": "string", "description": "The prompt to send"},
                "path": {"type": "string", "default": "."},
                "toon_dir": {"type": "string"},
                "task": {"type": "string", "enum": ["refactor", "explain", "quick_fix", "review"]},
                "model": {"type": "string", "description": "Override model selection"},
            },
        },
    ),
    handler=_handle_llx_proxym_chat,
)


# ─── aider ────────────────────────────────────────────────
async def _handle_aider(args: dict) -> dict:
    """Run aider AI pair programming tool."""
    import subprocess
    import json
    from pathlib import Path
    
    path = Path(args.get("path", "."))
    prompt = args.get("prompt", "")
    model = args.get("model", "ollama/qwen2.5-coder:7b")
    files = args.get("files", [])
    
    # Build aider command
    cmd = ["aider", "--model", model, "--message", prompt]
    
    # Add specific files if provided
    if files:
        cmd.extend(files)
    
    # Run aider in project directory
    try:
        result = subprocess.run(
            cmd,
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd),
            "path": str(path)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Aider command timed out after 5 minutes",
            "command": " ".join(cmd)
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Aider not found. Install with: pip install aider-chat",
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": " ".join(cmd)
        }

tool_aider = McpTool(
    definition=Tool(
        name="aider",
        description="Run aider AI pair programming tool for code editing and refactoring. Works with local Ollama models.",
        inputSchema={
            "type": "object",
            "required": ["prompt"],
            "properties": {
                "prompt": {"type": "string", "description": "The prompt/instruction for aider"},
                "path": {"type": "string", "default": ".", "description": "Project directory path"},
                "model": {"type": "string", "default": "ollama/qwen2.5-coder:7b", "description": "Model to use (Ollama format)"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Specific files to edit (optional)"},
            },
        },
    ),
    handler=_handle_aider,
)


# ─── planfile_generate ───────────────────────────────────────────

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


# ─── planfile_apply ───────────────────────────────────────────────

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
            strategy_path,
            project_path,
            sprint_filter=sprint,
            dry_run=dry_run
        )
        
        return {
            "success": True,
            "results": [
                {
                    "task_name": r.task_name,
                    "status": r.status,
                    "model_used": r.model_used,
                    "validated": r.validated,
                    "validation_score": r.validation_score,
                    "error": r.error
                }
                for r in results
            ],
            "total_tasks": len(results),
            "successful": sum(1 for r in results if r.status == "success"),
            "dry_run": dry_run
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

tool_planfile_apply = McpTool(
    definition=Tool(
        name="planfile_apply",
        description="Apply strategy.yaml — execute each task with optimal model selection.",
        inputSchema={
            "type": "object",
            "required": ["strategy_path"],
            "properties": {
                "strategy_path": {"type": "string", "description": "Path to strategy.yaml file"},
                "project_path": {"type": "string", "default": ".", "description": "Project path"},
                "sprint": {"type": "string", "description": "Specific sprint ID to execute"},
                "dry_run": {"type": "boolean", "default": False, "description": "Simulate execution without making changes"},
            },
        },
    ),
    handler=_handle_planfile_apply,
)
