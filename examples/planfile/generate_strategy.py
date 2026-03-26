#!/usr/bin/env python3
"""
Test planfile generator using the new llx.planfile module
"""

import sys
import re
sys.path.insert(0, '/home/tom/github/semcod/llx')

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import yaml

console = Console()


def _build_strategy_prompt(metrics, focus, sprints):
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


def _extract_yaml_text(content: str) -> str:
    if "```yaml" in content:
        return content.split("```yaml")[1].split("```")[0]
    if "```" in content:
        return content.split("```")[1].split("```")[0]
    return content


def _fix_yaml_text(yaml_text: str) -> str:
    yaml_text = yaml_text.replace("-id:", "- id:")
    yaml_text = yaml_text.replace("-name:", "- name:")
    yaml_text = yaml_text.replace("-task_type:", "- task_type:")
    yaml_text = yaml_text.replace("-description:", "- description:")
    yaml_text = yaml_text.replace("-priority:", "- priority:")
    yaml_text = yaml_text.replace("-model_hints:", "- model_hints:")
    yaml_text = yaml_text.replace("-planning:", "- planning:")
    yaml_text = yaml_text.replace("-implementation:", "- implementation:")
    yaml_text = yaml_text.replace("-review:", "- review:")

    yaml_text = re.sub(r'([a-zA-Z].{50,})\s{2,}([a-zA-Z])', r'\1\n  - \2', yaml_text)
    yaml_text = re.sub(r'(coverage|percentage):\s*>=\s*([0-9]+%)', r'\1: >= \2', yaml_text)

    lines = yaml_text.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        fixed_lines.append(line)
        if line.strip().startswith('- ') and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith('-') and not next_line.startswith(' '):
                if any(word in next_line.lower() for word in ['add', 'run', 'enforce', 'introduce', 'apply']):
                    fixed_lines.append('')

    yaml_text = '\n'.join(fixed_lines)

    lines = yaml_text.split('\n')
    corrected_lines = []
    for line in lines:
        if line.startswith('name:') and not line.startswith('  name:'):
            if corrected_lines and corrected_lines[-1].strip() and not corrected_lines[-1].startswith(' '):
                corrected_lines.append('  ' + line)
            else:
                corrected_lines.append(line)
        else:
            corrected_lines.append(line)

    return '\n'.join(corrected_lines)


def _fallback_strategy(focus):
    return {
        'name': 'Refactoring Strategy',
        'project_type': 'python',
        'domain': 'software',
        'goal': focus or 'improvement',
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


def _normalize_strategy_data(data, focus):
    if not isinstance(data, dict):
        data = _fallback_strategy(focus)

    if 'sprints' in data:
        for i, sprint in enumerate(data['sprints']):
            if isinstance(sprint.get('id'), str):
                if sprint['id'].startswith('sprint-'):
                    sprint['id'] = int(sprint['id'].split('-')[1])
                else:
                    sprint['id'] = i + 1

            if 'task_patterns' in data and 'tasks' not in sprint:
                sprint['tasks'] = []
                if isinstance(data['task_patterns'], list):
                    for task_name in data['task_patterns']:
                        sprint['tasks'].append({
                            'name': task_name,
                            'description': f"Execute {task_name.lower()}",
                            'type': 'tech_debt' if 'refactor' in task_name.lower() or 'extract' in task_name.lower() else 'feature',
                            'model_hints': 'balanced' if 'complex' in task_name.lower() else 'cheap'
                        })

    if 'quality_gates' in data:
        for gate in data['quality_gates']:
            if 'criteria' in gate and isinstance(gate['criteria'], str):
                gate['criteria'] = [gate['criteria']]

    if 'name' not in data:
        data['name'] = f"Refactoring Strategy"
    if 'project_type' not in data:
        data['project_type'] = 'python'
    if 'domain' not in data:
        data['domain'] = 'software'
    if 'goal' not in data:
        data['goal'] = focus or 'improvement'

    return data


def _write_debug_artifact(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def generate_strategy_with_fix(project_path, model="openrouter/nvidia/nemotron-3-super-120b-a12b:free", sprints=2, focus="complexity"):
    """Generate strategy using llx.planfile."""

    # Import llx.planfile modules
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
    prompt = _build_strategy_prompt(metrics, focus, sprints)

    console.print(f"\n[yellow]Sending prompt to LLM...[/yellow]")

    # 3. Call LLM using llx client
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
    _write_debug_artifact("/tmp/llm_response.txt", response.content)
    console.print(f"[dim]Full response saved to /tmp/llm_response.txt[/dim]")

    # 4. Parse with fixes
    yaml_text = _extract_yaml_text(response.content)

    # Save extracted YAML
    _write_debug_artifact("/tmp/extracted_yaml.txt", yaml_text)
    console.print(f"[dim]Extracted YAML saved to /tmp/extracted_yaml.txt[/dim]")

    # Fix common YAML formatting issues
    yaml_text = _fix_yaml_text(yaml_text)

    # Save fixed YAML
    _write_debug_artifact("/tmp/fixed_yaml.txt", yaml_text)
    console.print(f"[dim]Fixed YAML saved to /tmp/fixed_yaml.txt[/dim]")

    console.print(f"\n[yellow]Parsing YAML response...[/yellow]")

    # Parse YAML with fallback
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        console.print(f"[red]✗ YAML parsing failed: {e}[/red]")
        console.print("[yellow]Creating fallback strategy...[/yellow]")
        data = _fallback_strategy(focus)

    data = _normalize_strategy_data(data, focus)

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
