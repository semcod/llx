#!/usr/bin/env python3
"""
Test planfile generator using the new llx.planfile module
"""

import sys
import os
sys.path.insert(0, '/home/tom/github/semcod/llx')

import yaml
import re
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from llx.analysis.collector import analyze_project
from llx.config import LlxConfig
from llx.routing.client import LlxClient

console = Console()


def _normalize_strategy_data(data):
    """Normalize strategy data so it matches the expected YAML shape."""
    normalized = {}
    
    # Preserve name and type
    normalized['project_name'] = data.get('project_name', data.get('name', 'My Project'))
    normalized['project_type'] = data.get('project_type', data.get('type', 'Web Service'))
    
    # Normalize complex structures
    normalized['goal'] = _normalize_goal(data)
    normalized['goals'] = data.get('goals', [])
    normalized['sprints'] = _normalize_sprints(data)
    normalized['quality_gates'] = _normalize_quality_gates(data)
    normalized['metadata'] = _normalize_metadata(data)
    
    return normalized


def _normalize_sprints(data):
    """Normalize sprints data."""
    sprints = data.get('sprints')
    if not isinstance(sprints, list):
        # Maybe it's under a different key or just missing
        sprints = data.get('phases', [])
        
    normalized_sprints = []
    task_patterns = data.get('task_patterns', [])
    
    for i, sprint in enumerate(sprints):
        sprint = _normalize_single_sprint(sprint, i, task_patterns)
        normalized_sprints.append(sprint)
    
    return normalized_sprints


def _normalize_single_sprint(sprint, index, task_patterns):
    """Normalize a single sprint."""
    if not isinstance(sprint, dict):
        sprint = {'number': index + 1, 'objectives': [str(sprint)], 'tasks': []}
    else:
        sprint = dict(sprint)
    
    sprint.setdefault('number', index + 1)
    sprint.setdefault('name', f"Sprint {sprint['number']}")
    
    objectives = sprint.get('objectives', [])
    if isinstance(objectives, str):
        sprint['objectives'] = [objectives]
    else:
        sprint['objectives'] = list(objectives) if objectives else []
        
    tasks = sprint.get('tasks', [])
    if not isinstance(tasks, list):
        tasks = [tasks] if tasks else []
    sprint['tasks'] = tasks
    
    if not sprint['tasks'] and task_patterns:
        sprint['tasks'] = _generate_tasks_from_patterns(task_patterns)
    
    return sprint


def _extract_sprint_id(sprint_id, index):
    """Extract numeric sprint ID."""
    if isinstance(sprint_id, int):
        return sprint_id
    if isinstance(sprint_id, str):
        digits = ''.join(ch for ch in sprint_id if ch.isdigit())
        return int(digits) if digits else index + 1
    return index + 1


def _generate_tasks_from_patterns(task_patterns):
    """Generate tasks from pattern definitions."""
    tasks = []
    for task_name in task_patterns:
        task_str = task_name.get('name', str(task_name)) if isinstance(task_name, dict) else str(task_name)
        task_type = 'tech_debt' if 'refactor' in task_str.lower() or 'extract' in task_str.lower() else 'feature'
        model_hints = 'balanced' if 'complex' in task_str.lower() else 'cheap'
        
        tasks.append({
            'name': task_str,
            'description': f"Execute {task_str.lower()}",
            'type': task_type,
            'model_hints': model_hints
        })
    return tasks


def _normalize_quality_gates(data):
    """Normalize quality gates."""
    gates = data.get('quality_gates', [])
    if not isinstance(gates, list):
        gates = [gates] if gates else []
        
    return [_normalize_single_gate(gate, i) for i, gate in enumerate(gates)]


def _normalize_single_gate(gate, index):
    """Normalize a single quality gate."""
    if not isinstance(gate, dict):
        text = str(gate)
        gate = {'gate': text, 'condition': text, 'required': True}
    else:
        gate = dict(gate)
        
    gate.setdefault('gate', gate.get('name', f'Quality gate {index + 1}'))
    gate.setdefault('condition', gate.get('criteria', gate['gate']))
    gate.setdefault('required', True)
    
    return gate


def _normalize_goal(data):
    """Normalize goal data."""
    goal = data.get('goal')
    if not goal:
        goal = {'title': data.get('project_name', 'Project Refactoring'), 
                'description': data.get('goals', ['Improve code quality'])[0]}
    elif isinstance(goal, str):
        goal = {'title': goal, 'description': goal}
    else:
        goal = dict(goal)
        goal.setdefault('title', goal.get('name', 'Project Refactoring'))
        goal.setdefault('description', goal.get('description', 'Improve code quality'))
    return goal


def _normalize_metadata(data):
    """Normalize metadata."""
    metadata = dict(data.get('metadata', {}))
    metadata.setdefault('created_at', datetime.now().isoformat())
    metadata.setdefault('version', '1.0')
    return metadata


def generate_strategy_with_fix(project_path, model="openrouter/nvidia/nemotron-3-super-120b-a12b:free", sprints=8, focus="api", description=None, project_type=None, framework=None):
    """Generate strategy using llx.planfile."""
    _print_generation_info(project_path, model, sprints, focus, description)
    
    # 1. Collect metrics using llx
    metrics = analyze_project(project_path)
    
    # 2. Build prompt
    prompt = _build_strategy_prompt(metrics, sprints, focus, description, project_type, framework)
    
    # 3. Call LLM
    response = _call_llm_for_strategy(prompt, model)
    
    # 4. Parse and fix YAML
    yaml_data = _parse_and_fix_yaml(response.content)
    
    # 5. Normalize data
    yaml_data = _normalize_strategy_data(yaml_data)
    
    return yaml_data


def _print_generation_info(project_path, model, sprints, focus, description=None):
    """Print strategy generation information."""
    console.print(f"[blue]Generating strategy for {project_path}...[/blue]")
    console.print(f"  Model: {model}")
    console.print(f"  Sprints: {sprints}")
    console.print(f"  Focus: {focus}")
    if description:
        console.print(f"  Description: {description}")
    console.print(f"  Using OpenRouter free models")


def _build_strategy_prompt(metrics, sprints, focus, description=None, project_type=None, framework=None):
    """Build the prompt for strategy generation."""
    # Load prompt template from config
    import os
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'planfile_config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Use project_type to select template, fallback to focus, then to api
        template_key = project_type or focus or 'api'
        template = config['strategy']['prompts'].get(template_key, config['strategy']['prompts']['api'])
        
        # Format the template
        prompt = template.format(
            files=metrics.total_files,
            lines=metrics.total_lines,
            complexity=metrics.complexity_score,
            scale=metrics.scale_score,
            focus=focus,
            sprints=sprints,
            description=description or "Generate a refactoring strategy for this project",
            framework=framework or "default"
        )
        
        return prompt
    except Exception as e:
        # Fallback to hardcoded template if config fails
        console.print(f"[yellow]Warning: Could not load config, using default template ({e})[/yellow]")
        return f"""
Generate a project strategy (development or refactoring).
YOU MUST RESPOND WITH VALID YAML ONLY. NO CODE BLOCKS. NO EXPLANATIONS.

Project Metrics:
- Files: {metrics.total_files}
- Lines: {metrics.total_lines}
- Complexity: {metrics.complexity_score:.1f}
- Scale: {metrics.scale_score:.1f}

Focus: {focus}
Number of sprints: {sprints}
Description: {description or "Plan the next steps for this project"}

YAML Structure Required:
project_name: "Name"
project_type: "Type"
goals:
  - "Goal 1"
sprints:
  - number: 1
    objectives:
      - "Objective 1"
    tasks:
      - name: "Task 1"
        description: "Desc"
        type: "feature"
        model_hints: "balanced"
quality_gates:
  - gate: "Gate 1"
    condition: "Condition"

IMPORTANT: Ensure there is EXACTLY ONE space after every colon. Ensure every list item starts on a new line with a dash.
"""


def _call_llm_for_strategy(prompt, model):
    """Call LLM to generate strategy."""
    console.print(f"\n[yellow]Sending prompt to LLM...[/yellow]")
    
    # Suppress LiteLLM Provider List messages
    import logging
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    try:
        import litellm
        litellm.suppress_debug_info = True
        litellm.set_verbose = False
    except ImportError:
        pass
    
    # Load environment
    import os
    from dotenv import load_dotenv
    load_dotenv('/home/tom/github/semcod/llx/.env')
    
    config = LlxConfig()
    client = LlxClient(config)
    
    from llx.routing.client import ChatMessage
    response = client.chat(
        messages=[ChatMessage(role="user", content=prompt)],
        model=model
    )
    
    console.print(f"[green]Got response from LLM[/green]")
    
    # Debug: save full response
    with open("/tmp/llm_response.txt", "w") as f:
        f.write(response.content)
    console.print(f"[dim]Full response saved to /tmp/llm_response.txt[/dim]")
    
    return response


def _parse_and_fix_yaml(content):
    """Parse and fix YAML formatting issues."""
    # Extract YAML from response (more robust)
    yaml_text = content.strip()
    
    # Try reaching for code blocks first
    code_match = re.search(r'```(?:yaml)?\s*(.*?)```', content, re.DOTALL)
    if code_match:
        yaml_text = code_match.group(1).strip()
    else:
        # No code blocks, try to find the first line starting with a known key
        key_match = re.search(r'^([a-zA-Z0-9_-]+:)', content, re.MULTILINE)
        if key_match:
            yaml_text = content[key_match.start():].strip()

    # Save extracted YAML
    try:
        with open("/tmp/extracted_yaml.txt", "w") as f:
            f.write(yaml_text)
        console.print(f"[dim]Extracted YAML saved to /tmp/extracted_yaml.txt[/dim]")
    except Exception:
        pass
    
    # Fix common YAML formatting issues
    yaml_text = _fix_yaml_formatting(yaml_text)
    
    # Parse YAML
    try:
        data = yaml.safe_load(yaml_text)
        if not isinstance(data, dict):
            data = {}
    except yaml.YAMLError as e:
        console.print(f"[red]YAML parsing error: {e}[/red]")
        data = {}
    
    return data


def _fix_yaml_formatting(yaml_text):
    """Fix common YAML formatting issues."""
    # Ensure space after colon (safe for URLs like https:// as they have / after colon)
    yaml_text = re.sub(r'([a-zA-Z0-9_-]+):([^\s\n/])', r'\1: \2', yaml_text)
    
    # Fix multiple list items on same line (e.g. "- item1 - item2")
    # This is a bit tricky, we look for a dash inside a line that isn't at the start
    yaml_text = re.sub(r'(\s+-\s+.+?)\s+-\s+', r'\1\n      - ', yaml_text)
    
    # Fix missing newline before block mapping key if it's on the same line as value
    # e.g. "goal: title: My Project" -> "goal:\n  title: My Project"
    yaml_text = re.sub(r'^(\s*[a-zA-Z0-9_-]+:)\s+([a-zA-Z0-9_-]+:)', r'\1\n  \2', yaml_text, flags=re.MULTILINE)

    # Fix line continuation issues for sprints
    yaml_text = re.sub(r'^(- number:\s+\d+)(\s+)(objectives:)', r'\1\n  \3', yaml_text, flags=re.MULTILINE)
    yaml_text = re.sub(r'^(- number:\s+\d+)(\s+)([a-zA-Z_][a-zA-Z0-9_]*:)', r'\1\n  \3', yaml_text, flags=re.MULTILINE)
    
    # Ensure proper list formatting
    yaml_text = _fix_list_formatting(yaml_text)
    
    # Fix indentation problems
    yaml_text = _fix_indentation(yaml_text)
    
    # Save fixed YAML for debugging
    try:
        with open("/tmp/fixed_yaml.txt", "w") as f:
            f.write(yaml_text)
        console.print(f"[dim]Fixed YAML saved to /tmp/fixed_yaml.txt[/dim]")
    except Exception:
        pass
        
    return yaml_text


def _fix_list_formatting(yaml_text):
    """Fix list formatting issues."""
    lines = yaml_text.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        fixed_lines.append(line)
        # If line ends with a list item without proper dash, add newline
        if line.strip().startswith('- ') and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith('-') and not next_line.startswith(' '):
                # Check if it looks like it should be a new list item
                if any(word in next_line.lower() for word in ['add', 'run', 'enforce', 'introduce', 'apply']):
                    fixed_lines.append('')
    
    return '\n'.join(fixed_lines)


def _fix_indentation(yaml_text):
    """Fix indentation problems."""
    lines = yaml_text.split('\n')
    corrected_lines = []
    
    for line in lines:
        # Fix common indentation issues
        if line.startswith('name:') and not line.startswith('  name:'):
            # Check if we're inside a block
            if corrected_lines and corrected_lines[-1].strip() and not corrected_lines[-1].startswith(' '):
                # This might be a nested property, add proper indentation
                corrected_lines.append('  ' + line)
            else:
                corrected_lines.append(line)
        else:
            corrected_lines.append(line)
    
    return '\n'.join(corrected_lines)


def save_fixed_strategy(data, output_path):
    """Save the fixed strategy to YAML file."""
    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, indent=2)
    console.print(f"[green]✓ Strategy saved to {output_path}[/green]")


def main():
    """Generate a complete strategy using the fixed generator."""
    
    console.print(Panel(
        "[bold cyan]Planfile Strategy Generator[/bold cyan]\n"
        "Generating complete strategy.yaml from project analysis",
        title="Strategy Generator"
    ))
    
    # Use the simple test code as project
    project_path = Path("/home/tom/github/semcod/llx/examples/planfile")
    
    # Generate strategy
    try:
        strategy_data = generate_strategy_with_fix(
            project_path,
            model="openrouter/nvidia/nemotron-3-super-120b-a12b:free",
            sprints=2,
            focus="complexity"
        )
        
        # Save strategy
        output_path = project_path / "generated_strategy.yaml"
        save_fixed_strategy(strategy_data, output_path)
        
        # Show summary
        console.print("\n[bold]Generated Strategy Summary:[/bold]")
        console.print(f"  Name: {strategy_data.get('name')}")
        console.print(f"  Project Type: {strategy_data.get('project_type')}")
        console.print(f"  Domain: {strategy_data.get('domain')}")
        console.print(f"  Goal: {strategy_data.get('goal')}")
        console.print(f"  Sprints: {len(strategy_data.get('sprints', []))}")
        console.print(f"  Quality Gates: {len(strategy_data.get('quality_gates', []))}")
        
        # Show sprint details
        if strategy_data.get('sprints'):
            console.print("\n[bold]Sprints:[/bold]")
            for sprint in strategy_data['sprints']:
                console.print(f"  - Sprint {sprint.get('id')}: {sprint.get('name')}")
                if sprint.get('objectives'):
                    for obj in sprint['objectives']:
                        console.print(f"    • {obj}")
        
        console.print("\n[green]✓ Strategy generation complete![/green]")
        console.print(f"\n[yellow]Next steps:[/yellow]")
        console.print(f"1. Review the generated strategy: {output_path}")
        console.print(f"2. Apply with: llx plan apply {output_path} . --dry-run")
        console.print(f"3. If satisfied, apply without --dry-run")
        
    except Exception as e:
        console.print(f"[red]✗ Error generating strategy: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")


if __name__ == "__main__":
    main()
