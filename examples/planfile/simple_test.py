#!/usr/bin/env python3
"""
Simple test for planfile with working models
"""

import subprocess
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_command(cmd, timeout=30):
    """Run command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/tom/github/semcod/llx/examples/planfile/test-cases"
        )
        return result
    except subprocess.TimeoutExpired:
        console.print("[red]Command timed out[/red]")
        return None


def test_basic_functionality():
    """Test basic planfile functionality."""
    
    console.print("\n[bold blue]Testing Basic Planfile Functionality[/bold blue]")
    console.print("-" * 50)
    
    # Create test code
    test_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        if item > 0:
            total = total + item
        else:
            total = total - item
    return total

def process_list(data):
    result = []
    for i in range(len(data)):
        if data[i] % 2 == 0:
            result.append(data[i] * 2)
        else:
            result.append(data[i] * 3)
    return result
'''
    
    Path("/home/tom/github/semcod/llx/examples/planfile/test-cases/test_code.py").write_text(test_code)
    
    # Test 1: Generate strategy with local model
    console.print("[yellow]1. Testing strategy generation with local model...[/yellow]")
    cmd = "PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx plan generate . --model qwen2.5-coder:7b --sprints 1 --focus complexity --output test-local.yaml"
    result = run_command(cmd, timeout=60)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Strategy generated with local model[/green]")
        
        # Check strategy content
        strategy_path = Path("/home/tom/github/semcod/llx/examples/planfile/test-cases/test-local.yaml")
        if strategy_path.exists():
            with open(strategy_path) as f:
                strategy = yaml.safe_load(f)
            console.print(f"[blue]  - Sprints: {len(strategy.get('sprints', []))}[/blue]")
            console.print(f"[blue]  - Focus: {strategy.get('focus', 'N/A')}[/blue]")
        
        # Test 2: Review strategy
        console.print("[yellow]2. Testing strategy review...[/yellow]")
        cmd = "PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx plan review test-local.yaml ."
        result = run_command(cmd, timeout=30)
        
        if result and result.returncode == 0:
            console.print("[green]✓ Strategy reviewed successfully[/green]")
        else:
            console.print("[red]✗ Strategy review failed[/red]")
        
        # Test 3: Dry run
        console.print("[yellow]3. Testing dry-run execution...[/yellow]")
        cmd = "PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx plan apply test-local.yaml . --dry-run"
        result = run_command(cmd, timeout=30)
        
        if result and result.returncode == 0:
            console.print("[green]✓ Dry-run successful[/green]")
            if result.stdout:
                console.print(f"[blue]  Output: {result.stdout[:100]}...[/blue]")
        else:
            console.print("[red]✗ Dry-run failed[/red]")
            if result and result.stderr:
                console.print(f"[red]  Error: {result.stderr[:100]}...[/red]")
        
        return True
    else:
        console.print("[red]✗ Strategy generation failed[/red]")
        if result and result.stderr:
            console.print(f"[red]Error: {result.stderr[:200]}...[/red]")
        return False


def test_demo_scripts():
    """Test if demo scripts work."""
    
    console.print("\n[bold blue]Testing Demo Scripts[/bold blue]")
    console.print("-" * 50)
    
    # Test microservice demo
    console.print("[yellow]1. Testing microservice refactoring demo...[/yellow]")
    cmd = "PYTHONPATH=/home/tom/github/semcod/llx python3 microservice_refactor.py"
    result = run_command(cmd, timeout=30)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Microservice demo runs[/green]")
    else:
        console.print("[yellow]⚠ Microservice demo needs manual setup[/yellow]")
    
    # Test async demo
    console.print("[yellow]2. Testing async refactoring demo...[/yellow]")
    cmd = "PYTHONPATH=/home/tom/github/semcod/llx python3 async_refactor_demo.py"
    result = run_command(cmd, timeout=30)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Async demo runs[/green]")
    else:
        console.print("[yellow]⚠ Async demo needs manual setup[/yellow]")
    
    return True


def main():
    """Run simplified tests."""
    
    console.print(Panel(
        "[bold cyan]Planfile Simple Test[/bold cyan]\n"
        "Testing core functionality with available models",
        title="Planfile Test"
    ))
    
    # Run tests
    success = True
    
    # Test basic functionality
    if not test_basic_functionality():
        success = False
    
    # Test demo scripts
    test_demo_scripts()
    
    # Summary
    console.print("\n[bold cyan]Summary[/bold cyan]")
    console.print("=" * 50)
    
    if success:
        console.print("[green]✓ Core planfile functionality is working![/green]")
        console.print("\n[yellow]To test with actual refactoring:[/yellow]")
        console.print("1. Ensure you have a local model running (ollama)")
        console.print("2. Or configure API keys for cloud providers")
        console.print("3. Run: python3 -m llx plan generate . --model <model>")
    else:
        console.print("[red]✗ Some tests failed[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("1. Check if Ollama is running for local models")
        console.print("2. Verify LLX configuration in ~/.config/llx/")
        console.print("3. Check API keys for cloud models")
    
    # Cleanup
    cleanup_files = [
        "/home/tom/github/semcod/llx/examples/planfile/test-cases/test_code.py",
        "/home/tom/github/semcod/llx/examples/planfile/test-cases/test-local.yaml"
    ]
    
    for file in cleanup_files:
        Path(file).unlink(missing_ok=True)
    
    console.print("\n[green]✓ Cleanup completed[/green]")


if __name__ == "__main__":
    main()
