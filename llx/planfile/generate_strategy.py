#!/usr/bin/env python3
"""
Test planfile generator using the new llx.planfile module
"""

import sys
import os
sys.path.insert(0, '/home/tom/github/semcod/llx')

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import yaml

console = Console()


def _normalize_strategy_data(data):
    """Normalize strategy data so it matches the expected YAML shape."""
    data['sprints'] = _normalize_sprints(data)
    data['quality_gates'] = _normalize_quality_gates(data)
    data['goal'] = _normalize_goal(data)
    data['metadata'] = _normalize_metadata(data)
    return data


def _normalize_sprints(data):
    """Normalize sprints data."""
    sprints = data.get('sprints') if isinstance(data.get('sprints'), list) else []
    normalized_sprints = []
    task_patterns = data.get('task_patterns') if isinstance(data.get('task_patterns'), list) else []
    
    for i, sprint in enumerate(sprints):
        sprint = _normalize_single_sprint(sprint, i, task_patterns)
        normalized_sprints.append(sprint)
    
    return normalized_sprints


def _normalize_single_sprint(sprint, index, task_patterns):
    """Normalize a single sprint."""
    if not isinstance(sprint, dict):
        sprint = {'id': index + 1, 'name': str(sprint), 'objectives': [], 'tasks': []}
    else:
        sprint = dict(sprint)
    
    sprint['id'] = _extract_sprint_id(sprint.get('id', index + 1), index)
    sprint.setdefault('name', f"Sprint {sprint['id']}")
    
    objectives = sprint.get('objectives')
    sprint['objectives'] = objectives if isinstance(objectives, list) else ([objectives] if objectives else [])
    
    tasks = sprint.get('tasks')
    sprint['tasks'] = tasks if isinstance(tasks, list) else ([tasks] if tasks else [])
    
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
    """Normalize quality gates data."""
    quality_gates = data.get('quality_gates') if isinstance(data.get('quality_gates'), list) else []
    normalized_gates = []
    
    for i, gate in enumerate(quality_gates):
        gate = _normalize_single_gate(gate, i)
        normalized_gates.append(gate)
    
    return normalized_gates


def _normalize_single_gate(gate, index):
    """Normalize a single quality gate."""
    if not isinstance(gate, dict):
        text = str(gate)
        gate = {'name': text, 'description': text, 'criteria': [text], 'required': True}
    else:
        gate = dict(gate)
        criteria = gate.get('criteria')
        if isinstance(criteria, str):
            gate['criteria'] = [criteria]
        elif not isinstance(criteria, list):
            gate['criteria'] = [gate.get('description') or gate.get('name') or f'Quality gate {index + 1}']
        gate.setdefault('name', gate.get('description') or f'Quality gate {index + 1}')
        gate.setdefault('description', gate['name'])
        gate.setdefault('required', True)
    return gate


def _normalize_goal(data):
    """Normalize goal data."""
    goal = data.get('goal')
    if not goal:
        goal = {'title': data.get('title', 'Project Refactoring'), 'description': data.get('description', 'Improve code quality')}
    elif isinstance(goal, str):
        goal = {'title': goal, 'description': goal}
    else:
        goal = dict(goal)
        goal.setdefault('title', goal.get('name', 'Project Refactoring'))
        goal.setdefault('description', goal.get('description', 'Improve code quality'))
    return goal


def _normalize_metadata(data):
    """Normalize metadata."""
    metadata = data.get('metadata', {})
    if not metadata:
        metadata = {'created_at': datetime.now().isoformat(), 'version': '1.0'}
    else:
        metadata = dict(metadata)
        metadata.setdefault('created_at', datetime.now().isoformat())
        metadata.setdefault('version', '1.0')
    return metadata


def generate_strategy_with_fix(project_path, model="openrouter/nvidia/nemotron-3-super-120b-a12b:free", sprints=2, focus="complexity"):
    """Generate strategy using llx.planfile."""
    _print_generation_info(project_path, model, sprints, focus)
    
    # 1. Collect metrics using llx
    metrics = analyze_project(project_path)
    
    # 2. Build prompt
    prompt = _build_strategy_prompt(metrics, sprints, focus)
    
    # 3. Call LLM
    response = _call_llm_for_strategy(prompt, model)
    
    # 4. Parse and fix YAML
    yaml_data = _parse_and_fix_yaml(response.content)
    
    # 5. Normalize data
    yaml_data = _normalize_strategy_data(yaml_data)
    
    return yaml_data


def _print_generation_info(project_path, model, sprints, focus):
    """Print strategy generation information."""
    console.print(f"[blue]Generating strategy for {project_path}...[/blue]")
    console.print(f"  Model: {model}")
    console.print(f"  Sprints: {sprints}")
    console.print(f"  Focus: {focus}")
    console.print(f"  Using OpenRouter free models")


def _build_strategy_prompt(metrics, sprints, focus):
    """Build the prompt for strategy generation."""
    return f"""
Generate a refactoring strategy for this project:

Project Metrics:
- Files: {metrics.total_files}
- Lines: {metrics.total_lines}
- Complexity: {metrics.complexity_score:.1f}
- Scale: {metrics.scale_score:.1f}

Focus: {focus}
Number of sprints: {sprints}

Please generate a YAML strategy with:
1. Project name and type
2. Clear goals
3. {sprints} sprints with specific objectives
4. Task patterns for common work
5. Quality gates

Return only valid YAML without code blocks.
"""


def _call_llm_for_strategy(prompt, model):
    """Call LLM to generate strategy."""
    console.print(f"\n[yellow]Sending prompt to LLM...[/yellow]")
    
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
    # Extract YAML from response
    yaml_text = content
    if "```yaml" in content:
        yaml_text = content.split("```yaml")[1].split("```")[0]
    elif "```" in content:
        yaml_text = content.split("```")[1].split("```")[0]
    
    # Save extracted YAML
    with open("/tmp/extracted_yaml.txt", "w") as f:
        f.write(yaml_text)
    console.print(f"[dim]Extracted YAML saved to /tmp/extracted_yaml.txt[/dim]")
    
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
    # Fix common issues
    replacements = [
        ("-id:", "- id:"),
        ("-name:", "- name:"),
        ("-task_type:", "- task_type:"),
        ("-description:", "- description:"),
        ("-priority:", "- priority:"),
        ("-model_hints:", "- model_hints:"),
        ("-planning:", "- planning:"),
        ("-implementation:", "- implementation:"),
        ("-review:", "- review:")
    ]
    
    for old, new in replacements:
        yaml_text = yaml_text.replace(old, new)
    
    # Fix line continuation issues
    import re
    yaml_text = re.sub(r'^(- number:\s+\d+)(\s+)(objectives:)', r'\1\n  \3', yaml_text, flags=re.MULTILINE)
    yaml_text = re.sub(r'^(- number:\s+\d+)(\s+)([a-zA-Z_][a-zA-Z0-9_]*:)', r'\1\n  \3', yaml_text, flags=re.MULTILINE)
    
    # Ensure proper list formatting
    yaml_text = _fix_list_formatting(yaml_text)
    
    # Fix indentation problems
    yaml_text = _fix_indentation(yaml_text)
    
    # Save fixed YAML for debugging
    with open("/tmp/fixed_yaml.txt", "w") as f:
        f.write(yaml_text)
    console.print(f"[dim]Fixed YAML saved to /tmp/fixed_yaml.txt[/dim]")
    
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
