"""LLX fix command for pyqual integration."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from llx.analysis.collector import ProjectMetrics, analyze_project
from llx.config import LlxConfig
from llx.routing.selector import SelectionResult, select_model
from llx.utils.issues import load_issue_source, build_fix_prompt
from llx.commands._patch_apply import (
    _apply_unified_diff,
    _extract_json_from_content,
    _find_hunk_position,
    _parse_unified_hunks,
)

# Import preLLM if available
try:
    from llx.prellm.core import preprocess_and_execute_sync
    PRELLM_AVAILABLE = True
except ImportError:
    preprocess_and_execute_sync = None
    PRELLM_AVAILABLE = False

app = typer.Typer(help="LLX fix command for pyqual integration")
console = Console()


@app.command()
def fix(
    workdir: str = typer.Argument(".", help="Working directory"),
    errors: str = typer.Option(None, "--errors", "-e", help="Path to errors JSON file"),
    apply: bool = typer.Option(False, "--apply", help="Apply fixes automatically"),
    model: str = typer.Option(None, "--model", "-m", help="Force specific model"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Fix code issues using LLX-driven model selection."""
    workdir_path = Path(workdir).resolve()

    # Load errors if provided
    errors_data = None
    if errors:
        errors_path = Path(errors)
        if errors_path.exists():
            errors_data = load_issue_source(errors_path)
            if isinstance(errors_data, list):
                console.print(f"[green]✓[/green] Loaded {len(errors_data)} errors from {errors}")
            else:
                console.print(f"[green]✓[/green] Loaded errors from {errors}")
        else:
            console.print(f"[red]✗[/red] Errors file not found: {errors}")
            raise typer.Exit(1)

    # Analyze project metrics
    if verbose:
        console.print("\n[bold]Analyzing project metrics...[/bold]")

    metrics = analyze_project(workdir_path)
    config = LlxConfig.load(workdir_path)

    # Select model: --model flag > LLM_MODEL env var > metric-based routing
    env_model = os.environ.get("LLM_MODEL")
    if model:
        selected_model_id = model
        selection: SelectionResult | None = None
    elif env_model:
        selected_model_id = env_model
        selection = None
    else:
        selection = select_model(metrics, config)
        selected_model_id = selection.model_id

    console.print("\n[bold]Model Selection:[/bold]")
    console.print(Panel(_format_selection(selection, selected_model_id), border_style="green"))

    console.print(Panel(_format_metrics(metrics), title="Project Metrics", border_style="blue"))

    # Prepare fix prompt
    issues_for_prompt = errors_data if errors_data is not None else []
    analysis = {
        "selection": {
            "model_id": selected_model_id,
            "tier": selection.tier.value if selection else "forced",
        }
    } if selected_model_id else None
    prompt = build_fix_prompt(workdir_path, issues_for_prompt, analysis=analysis)

    if dry_run:
        console.print("\n[bold]Dry run - would execute:[/bold]")
        console.print(Panel(prompt, title="Fix Prompt", border_style="blue"))
        return

    if config.code_tool == "aider":
        if verbose:
            console.print("\n[bold]Generating fixes with Aider...[/bold]")

        aider_files = _extract_issue_files(issues_for_prompt)
        if verbose and aider_files:
            console.print(f"[dim]Target files:[/dim] {', '.join(aider_files)}")

        aider_result = _run_aider_fix(
            workdir=workdir_path,
            prompt=prompt,
            model=selected_model_id,
            files=aider_files,
            use_docker=config.run_env == "docker",
        )

        console.print("\n[bold]Aider result:[/bold]")
        console.print(
            Panel(
                _format_aider_result(aider_result),
                title="Aider Output",
                border_style="green" if aider_result.get("success") else "red",
            )
        )

        if not aider_result.get("success"):
            raise typer.Exit(1)

        if apply:
            console.print("\n[green]✓[/green] Aider applied changes directly.")
        return

    # Execute fix using preLLM if available
    if not PRELLM_AVAILABLE:
        console.print("[red]✗[/red] preLLM not available. Install with: pip install llx[prellm]")
        raise typer.Exit(1)

    if verbose:
        console.print("\n[bold]Generating fixes...[/bold]")

    try:
        # Use preLLM's two-agent pipeline
        result = preprocess_and_execute_sync(
            query=prompt,
            small_llm=_select_small_model(config),
            large_llm=selected_model_id,
            strategy="auto",
            codebase_path=str(workdir_path),
            collect_runtime=True,
            sanitize=True,
        )

        console.print("\n[bold]Generated fixes:[/bold]")
        console.print(Panel(result.content, title="LLM Response", border_style="green"))

        if apply and result.content:
            changes, files = apply_code_changes(workdir_path, result.content)
            if changes > 0:
                console.print(f"\n[green]✓[/green] Applied {changes} changes to {len(files)} files: {', '.join(files)}")
            else:
                console.print("\n[yellow]![/yellow] No code changes could be auto-applied. Manual review needed.")

    except Exception as e:
        console.print(f"[red]✗[/red] Error generating fixes: {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def apply_code_changes(workdir: Path, content: str) -> tuple[int, list[str]]:
    """Parse LLM response and apply changes to files.

    Supports four response formats (tried in order):
    1. JSON array of ``{"file": "...", "patch": "..."}`` objects
       (patches are unified diffs or full-file replacements)
    2. OpenAI ``*** Begin Patch`` / ``*** End Patch`` format
    3. Markdown code blocks with file paths in the header
    4. Code blocks with ``# File:`` / ``// File:`` comments

    Returns:
        Tuple of (number of changes applied, list of modified files)
    """
    changes_applied, modified_files = _apply_json_patch_strategy(workdir, content)
    if changes_applied > 0:
        return changes_applied, modified_files

    oa_changes, oa_files = _apply_openai_patch_strategy(workdir, content)
    if oa_changes > 0:
        return oa_changes, oa_files

    return _apply_markdown_code_block_strategy(workdir, content)


def _apply_json_patch_strategy(workdir: Path, content: str) -> tuple[int, list[str]]:
    """Apply JSON-formatted patch arrays."""
    import json as _json

    changes_applied = 0
    modified_files: list[str] = []

    json_str = _extract_json_from_content(content)
    if not json_str:
        return changes_applied, modified_files

    try:
        patches = _json.loads(json_str)
        if isinstance(patches, list):
            for entry in patches:
                if not isinstance(entry, dict):
                    continue
                file_rel = entry.get("file")
                patch_text = entry.get("patch") or entry.get("diff") or entry.get("content")
                if not file_rel or not patch_text:
                    continue
                file_path = workdir / file_rel
                if not file_path.exists():
                    continue
                applied = _apply_unified_diff(file_path, patch_text)
                if applied:
                    modified_files.append(file_rel)
                    changes_applied += 1
    except (_json.JSONDecodeError, TypeError, ValueError):
        pass

    return changes_applied, modified_files


def _apply_openai_patch_strategy(workdir: Path, content: str) -> tuple[int, list[str]]:
    """Apply OpenAI patch blocks when present."""
    if '*** Begin Patch' not in content:
        return 0, []
    return _apply_openai_patch(workdir, content)


def _apply_markdown_code_block_strategy(workdir: Path, content: str) -> tuple[int, list[str]]:
    """Apply markdown code blocks with file headers."""
    changes_applied = 0
    modified_files: list[str] = []
    lines = content.split('\n')
    current_file: str | None = None
    current_code: list[str] = []
    in_code_block = False

    for line in lines:
        if line.startswith('```'):
            if in_code_block and current_file and current_code:
                file_path = workdir / current_file
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text('\n'.join(current_code))
                    modified_files.append(str(current_file))
                    changes_applied += 1
                except Exception:
                    pass
                current_file = None
                current_code = []
            in_code_block = not in_code_block
            if in_code_block:
                header = line.replace('```', '').strip()
                # Skip lang-only headers like ```json, ```python
                if header and header not in ('json', 'python', 'typescript',
                                              'javascript', 'bash', 'sh',
                                              'yaml', 'yml', 'toml', 'diff'):
                    parts = header.split()
                    candidate = parts[1] if len(parts) > 1 else parts[0]
                    if '.' in candidate or '/' in candidate:
                        current_file = candidate
        elif in_code_block:
            if line.strip().startswith('# File:') or line.strip().startswith('// File:'):
                file_comment = line.strip().replace('# File:', '').replace('// File:', '').strip()
                if file_comment:
                    current_file = file_comment
            elif not current_file and line.strip().startswith('#') and ('.' in line and '/' in line):
                potential_file = line.strip().lstrip('#').strip()
                if not potential_file.startswith(' '):
                    current_file = potential_file
            else:
                current_code.append(line)

    return changes_applied, modified_files


def _apply_openai_patch(workdir: Path, content: str) -> tuple[int, list[str]]:
    """Apply patches in OpenAI ``*** Begin Patch`` format.

    Format::

        *** Begin Patch
        *** Update File: path/to/file.py
        @@
         context line
        -old line
        +new line
        *** End Patch

    Returns (changes_applied, list_of_modified_files).
    """
    changes = 0
    files: list[str] = []

    in_patch = False
    current_file: str | None = None
    hunks: list[tuple[list[str], list[str]]] = []  # (removed, added) per hunk
    cur_removed: list[str] = []
    cur_added: list[str] = []
    cur_context: list[str] = []

    def _flush_hunk():
        nonlocal cur_removed, cur_added, cur_context
        if cur_removed or cur_added:
            hunks.append((
                cur_context + cur_removed,  # lines to find (context + removed)
                cur_context + cur_added,    # lines to replace with (context + added)
            ))
        cur_removed = []
        cur_added = []
        cur_context = []

    def _apply_file_hunks(file_rel: str) -> bool:
        nonlocal changes
        _flush_hunk()
        if not hunks:
            return False
        file_path = workdir / file_rel
        if not file_path.exists():
            return False
        original = file_path.read_text()
        result = original
        for old_lines, new_lines in hunks:
            old_block = '\n'.join(old_lines)
            new_block = '\n'.join(new_lines)
            if old_block in result:
                result = result.replace(old_block, new_block, 1)
        if result != original:
            file_path.write_text(result)
            files.append(file_rel)
            changes += 1
            return True
        return False

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        if line.strip() == '*** Begin Patch':
            in_patch = True
            continue
        if line.strip() == '*** End Patch':
            if current_file:
                _apply_file_hunks(current_file)
            in_patch = False
            current_file = None
            hunks = []
            continue
        if not in_patch:
            continue
        if line.startswith('*** Update File:') or line.startswith('*** Add File:'):
            if current_file:
                _apply_file_hunks(current_file)
                hunks = []
            current_file = line.split(':', 1)[1].strip()
            cur_removed = []
            cur_added = []
            cur_context = []
            continue
        if line.startswith('*** Delete File:'):
            if current_file:
                _apply_file_hunks(current_file)
                hunks = []
            # Skip deletion for safety
            current_file = None
            continue
        if line == '@@':
            _flush_hunk()
            continue
        if not current_file:
            continue
        if line.startswith('-'):
            cur_removed.append(line[1:])
        elif line.startswith('+'):
            cur_added.append(line[1:])
        elif line.startswith(' '):
            # context line — if we have pending changes, flush first
            if cur_removed or cur_added:
                _flush_hunk()
            cur_context.append(line[1:])
        # Lines without prefix are also context
        elif not line.startswith('***'):
            if cur_removed or cur_added:
                _flush_hunk()
            cur_context.append(line)

    return changes, files


def _extract_issue_files(issues: dict[str, Any] | list[dict[str, Any]] | list[Any]) -> list[str]:
    """Return the unique file paths referenced by issues."""
    if isinstance(issues, dict):
        issue_items: list[Any] = [issues]
    else:
        issue_items = list(issues)

    files: list[str] = []
    seen: set[str] = set()
    for issue in issue_items:
        if not isinstance(issue, dict):
            continue
        location = issue.get("file") or issue.get("path")
        if not location:
            continue
        path = str(location)
        if path in seen:
            continue
        seen.add(path)
        files.append(path)
    return files


def _run_aider_fix(
    workdir: Path,
    prompt: str,
    model: str,
    files: list[str] | None = None,
    use_docker: bool = False,
    docker_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run aider directly, mirroring the MCP tool behaviour."""
    docker_args = docker_args or []

    if use_docker:
        docker_cmd = ["docker", "run", "--rm", "-v", f"{workdir.absolute()}:/workspace"]

        if docker_args:
            docker_cmd.extend(docker_args)

        if "--network" not in " ".join(docker_args):
            docker_cmd.extend(["--network", "host"])

        docker_cmd.extend([
            "-e",
            "OLLAMA_API_BASE=http://172.17.0.1:11434",
            "paulgauthier/aider",
            "--model",
            model.replace("ollama/", "ollama_chat/"),
            "--message",
            prompt,
        ])

        if files:
            docker_cmd.extend([f"/workspace/{f}" for f in files])

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(docker_cmd),
                "path": str(workdir),
                "method": "docker",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Aider Docker command timed out after 5 minutes",
                "command": " ".join(docker_cmd),
            }
        except FileNotFoundError:
            pass
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "command": " ".join(docker_cmd),
            }

    cmd = ["aider", "--model", model, "--message", prompt]

    if files:
        cmd.extend(files)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd),
            "path": str(workdir),
            "method": "local",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Aider command timed out after 5 minutes",
            "command": " ".join(cmd),
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Aider not found. Install with: pip install aider-chat, or use Docker with use_docker=true",
            "command": " ".join(cmd),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "command": " ".join(cmd),
        }


def _format_aider_result(result: dict[str, Any]) -> str:
    """Render aider output for the console."""
    lines = [
        f"Success: {result.get('success')}",
        f"Method: {result.get('method', 'unknown')}",
    ]

    command = result.get("command")
    if command:
        lines.append(f"Command: {command}")

    stdout = (result.get("stdout") or "").strip()
    if stdout:
        lines.extend(["", "STDOUT:", stdout])

    stderr = (result.get("stderr") or "").strip()
    if stderr:
        lines.extend(["", "STDERR:", stderr])

    error = (result.get("error") or "").strip()
    if error:
        lines.extend(["", "ERROR:", error])

    path = result.get("path")
    if path:
        lines.extend(["", f"Path: {path}"])

    return "\n".join(lines).strip()


def _select_small_model(config: LlxConfig) -> str:
    """Choose a smaller model for the preLLM preprocessing step."""
    for tier_name in ("cheap", "free", config.default_tier):
        model = config.models.get(tier_name)
        if model:
            return model.model_id
    return next(iter(config.models.values())).model_id


def _format_selection(selection: SelectionResult | None, selected_model_id: str) -> str:
    """Render a short selection summary."""
    if selection is None:
        return f"Forced model: [bold]{selected_model_id}[/bold]"
    return selection.explain()


def _format_metrics(metrics: ProjectMetrics) -> str:
    """Render the most useful project metrics for the operator."""
    lines = [
        f"Files: {metrics.total_files}",
        f"Lines: {metrics.total_lines:,}",
        f"Functions: {metrics.total_functions}",
        f"Classes: {metrics.total_classes}",
        f"Modules: {metrics.total_modules}",
        f"CC̄: {metrics.avg_cc:.1f}",
        f"Max CC: {metrics.max_cc}",
        f"Critical: {metrics.critical_count}",
        f"Fan-out: {metrics.max_fan_out}",
        f"Fan-in: {metrics.max_fan_in}",
        f"Cycles: {metrics.dependency_cycles}",
        f"Dup groups: {metrics.dup_groups}",
        f"Dup saved lines: {metrics.dup_saved_lines}",
        f"Scope: {metrics.task_scope}",
        f"Est. tokens: ~{metrics.estimated_context_tokens:,}",
    ]
    return "\n".join(lines)



if __name__ == "__main__":
    app()
