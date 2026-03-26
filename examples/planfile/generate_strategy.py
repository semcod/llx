#!/usr/bin/env python3
"""
Test planfile generator with custom wrapper to fix parsing issues
"""

import sys
import os
sys.path.insert(0, '/home/tom/github/semcod/llx')
sys.path.insert(0, '/home/tom/github/semcod/planfile')

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import yaml

console = Console()


def generate_strategy_with_fix(project_path, model="openrouter/nvidia/nemotron-3-super-120b-a12b:free", sprints=2, focus="complexity"):
    """Generate strategy using planfile with fixes for parsing issues."""
    
    # Import planfile modules
    from planfile.llm.generator import generate_strategy, build_strategy_prompt, _collect_metrics
    from planfile.llm.client import call_llm
    
    console.print(f"[blue]Generating strategy for {project_path}...[/blue]")
    console.print(f"  Model: {model}")
    console.print(f"  Sprints: {sprints}")
    console.print(f"  Focus: {focus}")
    console.print(f"  Using OpenRouter free models")
    
    # 1. Collect metrics
    metrics = _collect_metrics(project_path, None)
    
    # 2. Build prompt
    from planfile.llm.prompts import build_strategy_prompt
    prompt = build_strategy_prompt(metrics, sprints=sprints, focus=focus)
    
    console.print(f"\n[yellow]Sending prompt to LLM...[/yellow]")
    
    # 3. Call LLM with API key
    import os
    from dotenv import load_dotenv
    load_dotenv('/home/tom/github/semcod/llx/.env')
    
    # Set API key for LiteLLM
    os.environ['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY')
    
    response = call_llm(prompt, model=model)
    
    console.print(f"[green]Got response from LLM[/green]")
    
    # Debug: show raw response
    console.print(f"\n[dim]Raw LLM response (first 500 chars):[/dim]")
    console.print(f"[dim]{response[:500]}...[/dim]")
    
    # 4. Parse with fixes
    yaml_text = response
    if "```yaml" in response:
        yaml_text = response.split("```yaml")[1].split("```")[0]
    elif "```" in response:
        yaml_text = response.split("```")[1].split("```")[0]
    
    # Debug: show extracted YAML
    console.print(f"\n[dim]Extracted YAML (first 300 chars):[/dim]")
    console.print(f"[dim]{yaml_text[:300]}...[/dim]")
    
    console.print(f"\n[yellow]Parsing YAML response...[/yellow]")
    
    # Parse YAML
    data = yaml.safe_load(yaml_text)
    
    # Fix the data to match expected schema
    if 'sprints' in data:
        for i, sprint in enumerate(data['sprints']):
            # Convert string ID to int if needed
            if isinstance(sprint.get('id'), str):
                if sprint['id'].startswith('sprint-'):
                    sprint['id'] = int(sprint['id'].split('-')[1])
                else:
                    sprint['id'] = i + 1
            
            # Convert task_patterns to tasks if needed
            if 'task_patterns' in sprint and 'tasks' not in sprint:
                sprint['tasks'] = []
                for task in sprint['task_patterns']:
                    sprint['tasks'].append(f"task-{len(sprint['tasks']) + 1}")
    
    # Fix quality gates
    if 'quality_gates' in data:
        for gate in data['quality_gates']:
            if 'criteria' in gate and isinstance(gate['criteria'], str):
                gate['criteria'] = [gate['criteria']]
    
    # Ensure required fields
    if 'name' not in data:
        data['name'] = f"Refactoring Strategy"
    if 'project_type' not in data:
        data['project_type'] = 'python'
    if 'domain' not in data:
        data['domain'] = 'software'
    if 'goal' not in data:
        data['goal'] = focus or 'improvement'
    
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
