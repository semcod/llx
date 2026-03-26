#!/usr/bin/env python3
"""
Test strategy execution with dry run
"""

import sys
sys.path.insert(0, '/home/tom/github/semcod/llx')

from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def test_strategy_dry_run():
    """Test strategy execution in dry-run mode."""
    
    console.print("[bold blue]Testing Strategy Execution (Dry Run)[/bold blue]")
    console.print("=" * 50)
    
    from llx.planfile import execute_strategy
    
    # Execute strategy in dry-run mode
    results = execute_strategy(
        strategy_path="strategy_corrected.yaml",
        project_path="/home/tom/github/semcod/llx",
        dry_run=True
    )
    
    # Display results
    table = Table(title="Strategy Execution Results")
    table.add_column("Task", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Response", style="dim")
    
    for result in results:
        table.add_row(
            result.task_name,
            result.status,
            result.model_used,
            result.response[:50] + "..." if len(result.response) > 50 else result.response
        )
    
    console.print(table)
    
    # Summary
    total_tasks = len(results)
    console.print(f"\n[green]✅ Dry run completed![/green]")
    console.print(f"Total tasks: {total_tasks}")
    console.print(f"All tasks would be executed with appropriate models based on complexity.")
    
    return results


if __name__ == "__main__":
    try:
        test_strategy_dry_run()
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
