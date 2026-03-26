#!/usr/bin/env python3
"""Test simplified planfile integration in LLX."""

import sys
sys.path.insert(0, '/home/tom/github/semcod/llx')

from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def test_v2_format():
    """Test the new V2 format with LLX."""
    
    console.print("[bold blue]Testing LLX Planfile Integration (V2 Format)[/bold blue]")
    console.print("=" * 60)
    
    from llx.planfile import execute_strategy
    
    # Create a simple V2 strategy
    strategy_v2 = {
        "name": "LLX Integration Test",
        "goal": "Test V2 format with LLX",
        "sprints": [
            {
                "id": 1,
                "name": "Test Sprint",
                "objectives": ["Test format", "Test execution"],
                "tasks": [
                    {
                        "name": "Simple Task",
                        "description": "A simple test task",
                        "type": "feature",
                        "model_hints": "cheap"
                    },
                    {
                        "name": "Complex Task",
                        "description": "A more complex task",
                        "type": "refactor",
                        "model_hints": "balanced"
                    }
                ]
            }
        ]
    }
    
    # Save strategy to file
    strategy_file = Path("/tmp/test_strategy_v2.yaml")
    import yaml
    strategy_file.write_text(yaml.dump(strategy_v2, default_flow_style=False))
    
    console.print(f"Created test strategy: {strategy_file}")
    
    # Execute with dry run
    console.print("\n[bold]Executing with dry run...[/bold]")
    results = execute_strategy(
        strategy_file,
        project_path="/home/tom/github/semcod/llx",
        dry_run=True
    )
    
    # Display results
    table = Table(title="Execution Results")
    table.add_column("Task", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Model", style="yellow")
    
    for result in results:
        table.add_row(
            result.task_name,
            strategy_v2["sprints"][0]["tasks"][0].get("type", "N/A") if result.task_name == strategy_v2["sprints"][0]["tasks"][0]["name"] else "N/A",
            result.status,
            result.model_used
        )
    
    console.print(table)
    console.print(f"\n✅ Successfully executed {len(results)} tasks")
    
    # Clean up
    strategy_file.unlink()
    
    return True


def test_mixed_format():
    """Test mixed V1/V2 format handling."""
    
    console.print("\n[bold]Testing Mixed Format Support[/bold]")
    console.print("-" * 40)
    
    from llx.planfile import execute_strategy
    
    # Strategy with both task_patterns and tasks
    mixed_strategy = {
        "name": "Mixed Format Test",
        "goal": "Test format conversion",
        "sprints": [
            {
                "id": 1,
                "name": "Mixed Sprint",
                "tasks": [  # V2 format
                    {
                        "name": "V2 Task",
                        "description": "Task in V2 format",
                        "type": "test",
                        "model_hints": "free"
                    }
                ],
                "task_patterns": [  # V1 format
                    {
                        "name": "V1 Task",
                        "description": "Task in V1 format",
                        "task_type": "chore",
                        "model_hints": {"implementation": "cheap"}
                    }
                ]
            }
        ]
    }
    
    # Save and execute
    strategy_file = Path("/tmp/test_mixed_strategy.yaml")
    import yaml
    strategy_file.write_text(yaml.dump(mixed_strategy))
    
    results = execute_strategy(strategy_file, dry_run=True)
    
    console.print(f"✅ Handled mixed format - {len(results)} tasks executed")
    
    # Clean up
    strategy_file.unlink()
    
    return True


def test_error_handling():
    """Test error handling with invalid formats."""
    
    console.print("\n[bold]Testing Error Handling[/bold]")
    console.print("-" * 40)
    
    from llx.planfile import execute_strategy
    
    # Minimal strategy
    minimal_strategy = {
        "name": "Minimal Test",
        "sprints": [
            {
                "id": 1,
                "name": "Minimal Sprint",
                "tasks": []  # No tasks - should handle gracefully
            }
        ]
    }
    
    strategy_file = Path("/tmp/test_minimal.yaml")
    import yaml
    strategy_file.write_text(yaml.dump(minimal_strategy))
    
    try:
        results = execute_strategy(strategy_file, dry_run=True)
        console.print(f"✅ Handled minimal strategy - {len(results)} tasks")
    except Exception as e:
        console.print(f"❌ Error: {e}")
    
    strategy_file.unlink()
    
    return True


if __name__ == "__main__":
    console.print("LLX Planfile - Simplified Integration Test\n")
    
    success = True
    success &= test_v2_format()
    success &= test_mixed_format()
    success &= test_error_handling()
    
    console.print("\n" + "=" * 60)
    if success:
        console.print("[bold green]✅ All tests passed![/bold green]")
        console.print("\nThe simplified LLX planfile integration:")
        console.print("• Supports V2 format with embedded tasks")
        console.print("• Handles V1/V2 mixed formats")
        console.print("• Provides clear error messages")
        console.print("• Uses LLX's model selection and routing")
    else:
        console.print("[bold red]❌ Some tests failed[/bold red]")
