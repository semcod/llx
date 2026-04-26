"""Task execution, model selection, and prompt building."""

from pathlib import Path
from typing import Any, Optional
import logging
import time


def _map_action_to_task_type(action: str) -> str:
    """Map action string to task type."""
    action_map = {
        "fix": "fix",
        "refactor": "refactor",
        "feature": "feature",
        "test": "test",
        "docs": "docs",
        "chore": "chore",
    }
    return action_map.get(action, "feature")


def _map_priority(priority: int | str) -> str:
    """Map priority to standardized format."""
    if isinstance(priority, int):
        if priority <= 1:
            return "critical"
        elif priority <= 2:
            return "high"
        elif priority <= 3:
            return "medium"
        else:
            return "low"
    return priority if priority in ["critical", "high", "medium", "low"] else "medium"

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage
from llx.planfile.executor.base import BackendType, TaskResult
from llx.planfile.executor.backends import (
    _run_cursor_edit,
    _run_windsurf_edit,
    _run_claude_code_edit,
)
from llx.utils.aider import _run_aider_fix

logger = logging.getLogger(__name__)


def _parse_llm_response(response: str) -> dict:
    """Parse LLM response to extract structured information."""
    response_lower = response.lower()
    
    # Check if LLM claims issue doesn't exist
    not_found_indicators = [
        "issue not found",
        "problem not found",
        "no such issue",
        "cannot find",
        "doesn't exist",
        "does not exist",
        "already fixed",
        "already resolved",
        "no action needed",
        "no changes needed",
        "nothing to fix",
        "not applicable",
    ]
    issue_not_found = any(indicator in response_lower for indicator in not_found_indicators)

    # Check if LLM claims changes were made
    changes_indicators = [
        "i have modified",
        "i have changed",
        "i've updated",
        "here is the modified",
        "changes made",
        "file updated",
        "code changed",
        "i made the following changes",
        "here are the changes",
    ]
    changes_made = any(indicator in response_lower for indicator in changes_indicators)

    # Check if LLM claims problem was fixed
    fixed_indicators = [
        "issue fixed",
        "problem fixed",
        "resolved",
        "corrected",
        "fixed the",
        "has been fixed",
        "successfully fixed",
    ]
    problem_fixed = any(indicator in response_lower for indicator in fixed_indicators)

    # Extract detailed explanation for "issue not found" cases
    detailed_explanation = ""
    if issue_not_found:
        # Try to extract the explanation from the response
        lines = response.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(ind in line_lower for ind in not_found_indicators):
                # Collect this line and the next few lines for context
                context_lines = [line]
                for j in range(i+1, min(i+4, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('```'):
                        context_lines.append(lines[j])
                detailed_explanation = ' '.join(context_lines)
                break
        
        if not detailed_explanation:
            detailed_explanation = "The issue described in the ticket was not found in the codebase."

    # Build summary message with detailed explanation
    if issue_not_found:
        message = f"Task cancelled: {detailed_explanation}"
    elif changes_made and problem_fixed:
        message = "LLM reports changes made and issue fixed"
    elif changes_made:
        message = "LLM reports changes made"
    elif problem_fixed:
        message = "LLM reports issue fixed"
    else:
        message = "LLM response unclear about changes"

    return {
        "changes_made": changes_made,
        "problem_fixed": problem_fixed,
        "issue_not_found": issue_not_found,
        "message": message,
        "detailed_explanation": detailed_explanation
    }


def _select_model(task: dict, config: LlxConfig, metrics: Any) -> str:
    """Select appropriate model based on task and metrics."""
    # Get model hints from task
    model_hints = task.get("model_hints", {})
    preferred_tier = model_hints.get("tier", "balanced")
    
    # Map tier to model
    model_map = {
        "fast": config.models.get("fast"),
        "cheap": config.models.get("cheap"),
        "balanced": config.models.get("balanced"),
        "premium": config.models.get("premium")
    }
    
    model = model_map.get(preferred_tier, model_map.get("balanced"))
    
    if model:
        return model.model_id
    
    # Fallback to default
    default = config.models.get(config.default_tier)
    return default.model_id if default else "openai/gpt-5.4-mini"


def _build_task_prompt(task: dict, metrics: Any) -> str:
    """Build execution prompt with project context."""

    file_path = task.get("file", "")

    prompt = f"""## Task: {task.get('name', 'Unnamed Task')}

Type: {task.get('task_type', 'feature')}
Priority: {task.get('priority', 'medium')}
Target File: {file_path if file_path else 'N/A'}

Description:
{task.get('description', '')}

## Project Context
"""

    # Add metrics if available
    if hasattr(metrics, 'total_files'):
        prompt += f"- Files: {metrics.total_files}\n"
        prompt += f"- Lines of code: {metrics.total_lines:,}\n"
        prompt += f"- Average cyclomatic complexity: {metrics.avg_cc:.1f}\n"
        prompt += f"- Max complexity: {metrics.max_cc}\n"
        prompt += f"- Critical functions (CC > 10): {metrics.critical_count}\n"
    else:
        prompt += "- Metrics not available\n"

    # Add file content if file is specified
    if file_path:
        try:
            from pathlib import Path
            file_full_path = Path(file_path)
            if not file_full_path.is_absolute():
                # Assume relative to current directory
                file_full_path = Path.cwd() / file_path

            if file_full_path.exists():
                with open(file_full_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                prompt += f"""
## Current File Content

```python
{file_content}
```
"""
            else:
                prompt += f"\n## Current File Content\nFile not found: {file_path}\n"
        except Exception as e:
            prompt += f"\n## Current File Content\nError reading file: {e}\n"

    prompt += f"""
## Instructions

CRITICAL: You MUST output the complete modified file content in a code block.

For each file you modify, use this format:
```python:{file_path if file_path else 'path/to/file.py'}
# Complete file content here
```

If modifying multiple files, use separate code blocks with file paths.

Requirements:
1. Read and understand the current file content
2. Apply the necessary changes to fix the issue
3. Output the COMPLETE modified file content (not just snippets)
4. Ensure the code is syntactically correct and complete
5. Do not truncate or omit any parts of the file

If the issue does not exist or cannot be found, explicitly state: "Issue not found" or "No action needed".

Focus on practical, actionable changes that improve the codebase.
"""

    return prompt


def _execute_task(
    task: dict,
    config: LlxConfig,
    metrics: Any,
    model_override: Optional[str] = None,
    dry_run: bool = False,
    backend: str = BackendType.LLM_CHAT,
    project_root: Path = Path("."),
) -> TaskResult:
    """Execute a single task."""
    start_time = time.time()
    task_name = task.get("name", "Unnamed Task")
    target_file = task.get("file")
    
    try:
        # Select model
        model = model_override or _select_model(task, config, metrics)

        if dry_run:
            return TaskResult(
                task_name=task_name,
                status="dry_run",
                model_used=model,
                response="",
                execution_time=time.time() - start_time
            )

        # Build prompt
        prompt = _build_task_prompt(task, metrics)

        # Execute using selected backend
        code_changes_applied = False
        response_content = ""
        
        if backend == BackendType.MCP and target_file:
            # Use MCP for code editing
            try:
                from llx.mcp.client import MCPClient
                mcp_client = MCPClient()
                
                # Build MCP tool call
                tool_result = mcp_client.call_tool(
                    "aider_edit_file",
                    {
                        "file_path": str(target_file),
                        "prompt": prompt,
                        "model": model
                    }
                )
                
                response_content = str(tool_result)
                code_changes_applied = True  # Assume MCP handles changes
                
                if not code_changes_applied:
                    logger.error("MCP editing failed")
            except Exception as e:
                logger.error(f"MCP editing failed: {e}")
                # Fallback to LLM chat
                backend = BackendType.LLM_CHAT
                
        elif backend == BackendType.CURSOR and target_file:
            # Use Cursor for code editing
            cursor_result = _run_cursor_edit(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)]
            )
            
            response_content = cursor_result.get("stdout", "") + "\n" + cursor_result.get("stderr", "")
            code_changes_applied = cursor_result.get("success", False)
            
            if not code_changes_applied:
                logger.error(f"Cursor failed: {cursor_result.get('stderr', 'Unknown error')}")
                
        elif backend == BackendType.WINDSURF and target_file:
            # Use Windsurf for code editing
            windsurf_result = _run_windsurf_edit(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)]
            )
            
            response_content = windsurf_result.get("stdout", "") + "\n" + windsurf_result.get("stderr", "")
            code_changes_applied = windsurf_result.get("success", False)
            
            if not code_changes_applied:
                logger.error(f"Windsurf failed: {windsurf_result.get('stderr', 'Unknown error')}")
                
        elif backend == BackendType.CLAUDE_CODE and target_file:
            # Use Claude Code for code editing
            claude_result = _run_claude_code_edit(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)]
            )
            
            response_content = claude_result.get("stdout", "") + "\n" + claude_result.get("stderr", "")
            code_changes_applied = claude_result.get("success", False)
            
            if not code_changes_applied:
                logger.error(f"Claude Code failed: {claude_result.get('stderr', 'Unknown error')}")
                
        elif backend in [BackendType.LOCAL, BackendType.DOCKER] and target_file:
            # Use aider for code editing
            use_docker = (backend == BackendType.DOCKER)
            aider_result = _run_aider_fix(
                workdir=project_root,
                prompt=prompt,
                model=model,
                files=[str(target_file)] if target_file else None,
                use_docker=use_docker
            )

            response_content = aider_result.get("stdout", "") + "\n" + aider_result.get("stderr", "")
            code_changes_applied = aider_result.get("success", False)

            if not code_changes_applied:
                logger.warning(f"Aider editing failed: {aider_result.get('stderr', 'Unknown error')}")
                # Still continue - aider might have partially succeeded
        
        # Default: use LLM chat
        if not code_changes_applied and backend == BackendType.LLM_CHAT:
            # Use LLM chat for task execution
            client = LlxClient()
            
            messages = [
                ChatMessage(role="system", content="You are a helpful coding assistant."),
                ChatMessage(role="user", content=prompt)
            ]
            
            try:
                response = client.chat(
                    messages=messages,
                    model=model,
                    temperature=0.7
                )
                response_content = response.content
            except Exception as e:
                logger.error(f"LLM chat failed: {e}")
                return TaskResult(
                    task_name=task_name,
                    status="failed",
                    model_used=model,
                    response="",
                    error=str(e),
                    execution_time=time.time() - start_time
                )
        
        # Parse response for validation
        validation = _parse_llm_response(response_content)
        
        # Determine final status based on validation and changes
        if validation["issue_not_found"]:
            status = "cancelled"
        elif validation["changes_made"] or validation["problem_fixed"]:
            status = "success"
        elif code_changes_applied:
            status = "success"
        else:
            status = "failed"
        
        # Build detailed validation message
        if status == "cancelled":
            validation_message = validation["message"]
        else:
            validation_message = validation["message"]
        
        return TaskResult(
            task_name=task_name,
            status=status,
            model_used=model,
            response=response_content,
            execution_time=time.time() - start_time,
            file_changed=code_changes_applied or validation["changes_made"],
            validation_message=validation_message
        )
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return TaskResult(
            task_name=task_name,
            status="failed",
            model_used=model_override or "unknown",
            response="",
            error=str(e),
            execution_time=time.time() - start_time
        )
