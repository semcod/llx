#!/usr/bin/env python3
"""
Test planfile with OpenRouter free models - Simple working example
"""

import subprocess
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_command(cmd, timeout=60):
    """Run command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        console.print("[red]Command timed out[/red]")
        return None


def create_simple_strategy():
    """Create a simple working strategy for testing."""
    
    strategy = {
        "name": "Simple Refactoring Strategy",
        "project_type": "python",
        "domain": "software",
        "goal": "Reduce complexity",
        "sprints": [
            {
                "sprint": 1,
                "objectives": [
                    "Extract complex functions",
                    "Add unit tests"
                ],
                "task_patterns": [
                    {
                        "name": "Extract function",
                        "description": "Extract complex logic into separate functions",
                        "task_type": "refactor",
                        "model_hints": {
                            "implementation": "free"
                        }
                    },
                    {
                        "name": "Add tests",
                        "description": "Write unit tests for extracted functions",
                        "task_type": "test",
                        "model_hints": {
                            "implementation": "free"
                        }
                    }
                ],
                "tasks": ["task-1", "task-2"]
            }
        ],
        "quality_gates": [
            {
                "name": "Complexity check",
                "description": "Verify complexity reduction",
                "criteria": ["avg_cc < 10"]
            }
        ]
    }
    
    # Save strategy
    strategy_file = Path("/home/tom/github/semcod/llx/examples/planfile/simple_strategy.yaml")
    with open(strategy_file, 'w') as f:
        yaml.dump(strategy, f, default_flow_style=False, indent=2)
    
    console.print(f"[green]✓ Created simple strategy: {strategy_file}[/green]")
    return strategy_file


def test_strategy_apply():
    """Test applying the strategy."""
    
    console.print("\n[bold blue]Testing Strategy Apply with OpenRouter[/bold blue]")
    console.print("-" * 50)
    
    # Create simple strategy
    strategy_file = create_simple_strategy()
    
    # Test dry-run
    console.print("[yellow]Running dry-run...[/yellow]")
    cmd = f"PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx plan apply {strategy_file} . --dry-run"
    result = run_command(cmd, timeout=60)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Dry-run successful![/green]")
        if result.stdout:
            console.print("\n[bold]Output:[/bold]")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    console.print(f"  {line}")
        
        # Show models used
        if "→" in result.stdout:
            console.print("\n[bold]Models selected:[/bold]")
            for line in result.stdout.split('\n'):
                if "→" in line:
                    console.print(f"  {line.strip()}")
        
        return True
    else:
        console.print("[red]✗ Dry-run failed[/red]")
        if result and result.stderr:
            console.print(f"[red]Error: {result.stderr[:200]}...[/red]")
        return False


def test_openrouter_chat():
    """Test direct chat with OpenRouter free model."""
    
    console.print("\n[bold blue]Testing OpenRouter Chat[/bold blue]")
    console.print("-" * 50)
    
    # Test with gemma model
    console.print("[yellow]Testing chat with gemma-2-9b-it...[/yellow]")
    cmd = "PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx chat . --model gemma-2-9b-it:free --prompt 'What is 2+2? Answer briefly.'"
    result = run_command(cmd, timeout=30)
    
    if result and result.returncode == 0:
        console.print("[green]✓ OpenRouter chat works![/green]")
        if result.stdout:
            # Extract response
            lines = result.stdout.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('Model:') and not line.startswith('Tokens:'):
                    console.print(f"[blue]Response: {line.strip()}[/blue]")
                    break
        return True
    else:
        console.print("[red]✗ OpenRouter chat failed[/red]")
        if result and result.stderr:
            console.print(f"[red]Error: {result.stderr[:200]}...[/red]")
        return False


def main():
    """Run tests with OpenRouter free models."""
    
    console.print(Panel(
        "[bold cyan]Planfile + OpenRouter Integration Test[/bold cyan]\n"
        "Testing planfile functionality with OpenRouter free models\n"
        "Using gemma-2-9b-it (9B) model",
        title="OpenRouter Test"
    ))
    
    # Test 1: Direct chat
    chat_success = test_openrouter_chat()
    
    # Test 2: Strategy apply
    apply_success = test_strategy_apply()
    
    # Summary
    console.print("\n[bold cyan]Test Summary[/bold cyan]")
    console.print("=" * 50)
    
    if chat_success and apply_success:
        console.print("[green]✓ All tests passed![/green]")
        console.print("\n[yellow]OpenRouter integration is working![/yellow]")
        console.print("You can now use:")
        console.print("  - gemma-2-9b-it:free (free, 9B parameters)")
        console.print("  - deepseek (cheap, high quality)")
    else:
        console.print("[red]✗ Some tests failed[/red]")
        
        if not chat_success:
            console.print("• Check OPENROUTER_API_KEY in .env")
        if not apply_success:
            console.print("• Check strategy format")
    
    # Cleanup
    Path("/home/tom/github/semcod/llx/examples/planfile/simple_strategy.yaml").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
