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
    sprints = data.get('sprints') if isinstance(data.get('sprints'), list) else []
    normalized_sprints = []
    for i, sprint in enumerate(sprints):
        if not isinstance(sprint, dict):
            sprint = {'id': i + 1, 'name': str(sprint), 'objectives': [], 'tasks': []}
        else:
            sprint = dict(sprint)

        sprint_id = sprint.get('id', i + 1)
        if isinstance(sprint_id, str):
            digits = ''.join(ch for ch in sprint_id if ch.isdigit())
            sprint_id = int(digits) if digits else i + 1
        sprint['id'] = sprint_id if isinstance(sprint_id, int) else i + 1
        sprint.setdefault('name', f"Sprint {sprint['id']}")

        objectives = sprint.get('objectives')
        sprint['objectives'] = objectives if isinstance(objectives, list) else ([objectives] if objectives else [])

        tasks = sprint.get('tasks')
        sprint['tasks'] = tasks if isinstance(tasks, list) else ([tasks] if tasks else [])

        if not sprint['tasks']:
            source_patterns = sprint.get('task_patterns')
            if not isinstance(source_patterns, list):
                source_patterns = data.get('task_patterns') if isinstance(data.get('task_patterns'), list) else []

            if source_patterns:
                sprint['tasks'] = []
                for task_name in source_patterns:
                    task_str = task_name.get('name', str(task_name)) if isinstance(task_name, dict) else str(task_name)
                    sprint['tasks'].append({
                        'name': task_str,
                        'description': f"Execute {task_str.lower()}",
                        'type': 'tech_debt' if 'refactor' in task_str.lower() or 'extract' in task_str.lower() else 'feature',
                        'model_hints': 'balanced' if 'complex' in task_str.lower() else 'cheap'
                    })

        normalized_sprints.append(sprint)

    data['sprints'] = normalized_sprints

    quality_gates = data.get('quality_gates') if isinstance(data.get('quality_gates'), list) else []
    normalized_gates = []
    for i, gate in enumerate(quality_gates):
        if not isinstance(gate, dict):
            text = str(gate)
            gate = {'name': text, 'description': text, 'criteria': [text], 'required': True}
        else:
            gate = dict(gate)
            criteria = gate.get('criteria')
            if isinstance(criteria, str):
                gate['criteria'] = [criteria]
            elif not isinstance(criteria, list):
                gate['criteria'] = [gate.get('description') or gate.get('name') or f'Quality gate {i + 1}']
            gate.setdefault('name', gate.get('description') or f'Quality gate {i + 1}')
            gate.setdefault('description', gate['name'])
            gate.setdefault('required', True)
        normalized_gates.append(gate)

    data['quality_gates'] = normalized_gates
    return data


def generate_strategy_with_fix(project_path, model="openrouter/nvidia/nemotron-3-super-120b-a12b:free", sprints=2, focus="complexity"):
    """Generate strategy using llx.planfile."""
    
    # Import llx.planfile modules
    from llx.planfile import Strategy, Goal, Sprint, TaskPattern, TaskType, ModelHints
    from llx.routing.client import LlxClient
    from llx.config import LlxConfig
    from llx import analyze_project
    
    console.print(f"[blue]Generating strategy for {project_path}...[/blue]")
    console.print(f"  Model: {model}")
    console.print(f"  Sprints: {sprints}")
    console.print(f"  Focus: {focus}")
    console.print(f"  Using OpenRouter free models")
    
    # 1. Collect metrics using llx
    metrics = analyze_project(project_path)
    
    # 2. Build prompt manually for now
    prompt = f"""
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
    
    console.print(f"\n[yellow]Sending prompt to LLM...[/yellow]")
    
    # 3. Call LLM using llx client
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
    
    # 4. Parse with fixes
    yaml_text = response.content
    if "```yaml" in response.content:
        yaml_text = response.content.split("```yaml")[1].split("```")[0]
    elif "```" in response.content:
        yaml_text = response.content.split("```")[1].split("```")[0]
    
    # Save extracted YAML
    with open("/tmp/extracted_yaml.txt", "w") as f:
        f.write(yaml_text)
    console.print(f"[dim]Extracted YAML saved to /tmp/extracted_yaml.txt[/dim]")
    
    # Fix common YAML formatting issues
    yaml_text = yaml_text.replace("-id:", "- id:")
    yaml_text = yaml_text.replace("-name:", "- name:")
    yaml_text = yaml_text.replace("-task_type:", "- task_type:")
    yaml_text = yaml_text.replace("-description:", "- description:")
    yaml_text = yaml_text.replace("-priority:", "- priority:")
    yaml_text = yaml_text.replace("-model_hints:", "- model_hints:")
    yaml_text = yaml_text.replace("-planning:", "- planning:")
    yaml_text = yaml_text.replace("-implementation:", "- implementation:")
    yaml_text = yaml_text.replace("-review:", "- review:")
    
    # Fix line continuation issues - targeted fixes only
    import re
    # Fix pattern: "- number: X    field:" -> "- number: X\n    field:" (only for objectives)
    yaml_text = re.sub(r'^(- number:\s+\d+)(\s+)(objectives:)', r'\1\n  \3', yaml_text, flags=re.MULTILINE)
    # Fix pattern: "- number: X    field:" -> "- number: X\n    field:" (for other fields)
    yaml_text = re.sub(r'^(- number:\s+\d+)(\s+)([a-zA-Z_][a-zA-Z0-9_]*:)', r'\1\n  \3', yaml_text, flags=re.MULTILINE)
    
    # Ensure proper list formatting
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
    
    # Save fixed YAML
    yaml_text = '\n'.join(fixed_lines)
    
    # Additional fixes for common YAML issues
    # Fix indentation problems
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
    
    yaml_text = '\n'.join(corrected_lines)
    
    with open("/tmp/fixed_yaml.txt", "w") as f:
        f.write(yaml_text)
    console.print(f"[dim]Fixed YAML saved to /tmp/fixed_yaml.txt[/dim]")
    
    console.print(f"\n[yellow]Parsing YAML response...[/yellow]")
    
    # Parse YAML with fallback
    try:
        data = yaml.safe_load(yaml_text)
        if not isinstance(data, dict):
            raise yaml.YAMLError("YAML root must be a mapping")
    except yaml.YAMLError as e:
        console.print(f"[red]✗ YAML parsing failed: {e}[/red]")
        console.print("[yellow]Creating fallback strategy...[/yellow]")
        # Create a simple fallback strategy
        data = {
            'name': 'Refactoring Strategy',
            'project_type': 'python',
            'domain': 'software',
            'goal': {
                'short': f"Improve {focus or 'codebase'}",
                'quality': ['Reduce complexity', 'Improve maintainability'],
                'delivery': ['Complete in sprints', 'Review changes'],
                'metrics': ['Complexity reduction', 'Test coverage']
            },
            'sprints': [
                {
                    'id': 1,
                    'name': 'Sprint 1',
                    'objectives': ['Reduce complexity', 'Add tests'],
                    'tasks': [
                        {
                            'name': 'Analyze Complexity',
                            'description': 'Analyze code complexity',
                            'type': 'feature',
                            'model_hints': 'balanced'
                        },
                        {
                            'name': 'Add Tests',
                            'description': 'Add unit tests',
                            'type': 'test',
                            'model_hints': 'cheap'
                        }
                    ]
                }
            ],
            'quality_gates': [
                'Average CC < 5',
                'Test coverage >= 80%'
            ]
        }
    
    # Fix the data to match expected schema
    data = _normalize_strategy_data(data)
    
    # Ensure required fields
    if 'name' not in data:
        data['name'] = f"Refactoring Strategy"
    if 'project_type' not in data:
        data['project_type'] = 'python'
    if 'domain' not in data:
        data['domain'] = 'software'
    
    # Fix goal to be a proper Goal object
    if 'goal' not in data or isinstance(data.get('goal'), str):
        goal_str = data.get('goal', focus or 'improvement')
        data['goal'] = {
            'short': f"Improve {goal_str}" if goal_str else "Improve codebase",
            'quality': ['Reduce complexity', 'Improve maintainability'],
            'delivery': ['Complete in sprints', 'Review changes'],
            'metrics': ['Complexity reduction', 'Test coverage']
        }
    elif isinstance(data.get('goal'), dict):
        # Ensure all required fields exist
        goal = data['goal']
        goal.setdefault('short', f"Improve {focus or 'codebase'}")
        goal.setdefault('quality', ['Reduce complexity', 'Improve maintainability'])
        goal.setdefault('delivery', ['Complete in sprints', 'Review changes'])
        goal.setdefault('metrics', ['Complexity reduction', 'Test coverage'])
    
    console.print(f"[green]✓ Strategy parsed and fixed[/green]")
    
    return data


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
