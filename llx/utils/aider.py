"""Aider utility functions for the fix command."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _extract_issue_files(issues: list | dict | None) -> list[str]:
    """Extract file paths from issues data.
    
    Args:
        issues: Issues data - can be a list of issues or a dict with 'issues' key,
               or None.
    
    Returns:
        List of file paths extracted from issues.
    """
    if issues is None:
        return []
    
    files = set()
    
    # Handle dict with 'issues' key
    if isinstance(issues, dict):
        issues_list = issues.get("issues", [])
    else:
        issues_list = issues
    
    if not isinstance(issues_list, list):
        return []
    
    for issue in issues_list:
        if isinstance(issue, dict):
            # Try common file path keys
            for key in ["file", "path", "filename", "filepath"]:
                if key in issue and issue[key]:
                    files.add(str(issue[key]))
                    break
    
    return sorted(files)


def _run_aider_fix(
    workdir: Path,
    prompt: str,
    model: str,
    files: list[str] | None = None,
    use_docker: bool = False,
) -> dict[str, Any]:
    """Run aider to fix code issues.
    
    Args:
        workdir: Working directory path
        prompt: The prompt/instruction for aider
        model: Model to use (e.g., "ollama/qwen2.5-coder:7b")
        files: Specific files to edit (optional)
        use_docker: Whether to use Docker to run aider
    
    Returns:
        Dict with success status, stdout, stderr, command, path, and method.
    """
    files = files or []
    
    # Try Docker first if requested
    if use_docker:
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{workdir}:/app",
            "-w", "/app",
            "-e", "OLLAMA_API_BASE=http://172.17.0.1:11434",
            "paulgauthier/aider",
            "--model", model.replace("ollama/", "ollama_chat/"),
            "--message", prompt
        ]
        
        # Add specific files if provided
        if files:
            docker_cmd.extend(files)
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
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
                "stdout": "",
                "stderr": "Aider Docker command timed out after 5 minutes",
                "command": " ".join(docker_cmd),
                "path": str(workdir),
                "method": "docker",
            }
        except FileNotFoundError:
            # Docker not available, fall through to local
            pass
    
    # Build aider command for local execution
    cmd = ["aider", "--model", model, "--message", prompt]
    
    # Add specific files if provided
    if files:
        cmd.extend(files)
    
    # Run aider in project directory
    try:
        result = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
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
            "stdout": "",
            "stderr": "Aider command timed out after 5 minutes",
            "command": " ".join(cmd),
            "path": str(workdir),
            "method": "local",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Aider not found. Install with: pip install aider-chat, or use Docker with use_docker=true",
            "command": " ".join(cmd),
            "path": str(workdir),
            "method": "local",
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error running aider: {str(e)}",
            "command": " ".join(cmd),
            "path": str(workdir),
            "method": "local",
        }


def _format_aider_result(result: dict[str, Any]) -> str:
    """Format aider result for display.
    
    Args:
        result: Result dict from _run_aider_fix.
    
    Returns:
        Formatted string for display.
    """
    lines = []
    
    if result.get("success"):
        lines.append("[green]✓[/green] Aider completed successfully")
    else:
        lines.append("[red]✗[/red] Aider failed")
    
    lines.append(f"Method: {result.get('method', 'unknown')}")
    lines.append(f"Command: {result.get('command', 'N/A')}")
    
    if result.get("stdout"):
        lines.append("\n[bold]Output:[/bold]")
        lines.append(result["stdout"])
    
    if result.get("stderr"):
        lines.append("\n[bold red]Errors:[/bold red]")
        lines.append(result["stderr"])
    
    return "\n".join(lines)
