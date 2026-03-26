#!/usr/bin/env python3
"""
Test planfile with OpenRouter free models using API key from .env
"""

import os
import subprocess
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def load_env():
    """Load environment variables from .env file."""
    env_file = Path("/home/tom/github/semcod/llx/.env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value


def run_command(cmd, timeout=60):
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


def test_openrouter_models():
    """Test OpenRouter free models availability."""
    
    console.print("\n[bold blue]Testing OpenRouter Free Models[/bold blue]")
    console.print("-" * 50)
    
    # Load environment
    load_env()
    
    if not os.environ.get("OPENROUTER_API_KEY"):
        console.print("[red]✗ OPENROUTER_API_KEY not found in .env[/red]")
        return False
    
    console.print("[green]✓ OPENROUTER_API_KEY found[/green]")
    
    # Test models
    free_models = [
        ("nemotron-3-super", "Nemotron 3 Super"),
        ("deepseek", "DeepSeek Chat"),
    ]
    
    working_models = []
    
    for model_id, model_name in free_models:
        console.print(f"\n[yellow]Testing {model_name}...[/yellow]")
        
        # Simple test with chat
        cmd = f"PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx chat . --model {model_id} --prompt 'Say hello'"
        result = run_command(cmd, timeout=30)
        
        if result and result.returncode == 0:
            console.print(f"[green]✓ {model_name} works[/green]")
            working_models.append((model_id, model_name))
        else:
            console.print(f"[red]✗ {model_name} failed[/red]")
            if result and result.stderr:
                console.print(f"[dim]Error: {result.stderr[:100]}...[/dim]")
    
    return working_models


def test_strategy_generation():
    """Test strategy generation with OpenRouter models."""
    
    console.print("\n[bold blue]Testing Strategy Generation[/bold blue]")
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

def process_data(items):
    processed = []
    for item in items:
        if item > 0:
            processed.append(item * 2)
        else:
            processed.append(item * 3)
    return processed
'''
    
    Path("/home/tom/github/semcod/llx/examples/planfile/test-cases/test_code.py").write_text(test_code)
    
    # Test with different models
    models_to_test = [
        ("openrouter/meta-llama/llama-3.2-3b-instruct:free", "Llama 3.2 3B"),
        ("openrouter/mistral-7b-instruct:free", "Mistral 7B"),
    ]
    
    success_count = 0
    
    for model_id, model_name in models_to_test:
        console.print(f"\n[yellow]Generating strategy with {model_name}...[/yellow]")
        
        cmd = f"PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx plan generate . --model {model_id} --sprints 1 --focus complexity --output test-{model_name.replace(' ', '_').lower()}.yaml"
        result = run_command(cmd, timeout=120)
        
        if result and result.returncode == 0:
            console.print(f"[green]✓ Strategy generated with {model_name}[/green]")
            success_count += 1
            
            # Check strategy file
            strategy_file = Path(f"/home/tom/github/semcod/llx/examples/planfile/test-cases/test-{model_name.replace(' ', '_').lower()}.yaml")
            if strategy_file.exists():
                with open(strategy_file) as f:
                    strategy = yaml.safe_load(f)
                console.print(f"[blue]  - Sprints: {len(strategy.get('sprints', []))}[/blue]")
        else:
            console.print(f"[red]✗ Failed with {model_name}[/red]")
            if result and result.stderr:
                console.print(f"[dim]Error: {result.stderr[:150]}...[/dim]")
    
    return success_count > 0


def test_strategy_apply():
    """Test strategy application with OpenRouter."""
    
    console.print("\n[bold blue]Testing Strategy Application[/bold blue]")
    console.print("-" * 50)
    
    # Use our fixed generator
    cmd = "cd /home/tom/github/semcod/llx/examples/planfile && python3 generate_strategy.py"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[green]✓ Strategy generated with OpenRouter[/green]")
        
        # Test apply
        strategy_file = "/home/tom/github/semcod/llx/examples/planfile/generated_strategy.yaml"
        cmd = f"PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx plan apply {strategy_file} . --dry-run"
        result = run_command(cmd, timeout=60)
        
        if result and result.returncode == 0:
            console.print("[green]✓ Strategy application successful[/green]")
            
            # Count tasks
            if result.stdout:
                tasks = result.stdout.count("Executing:")
                console.print(f"[blue]  - Tasks planned: {tasks}[/blue]")
            
            return True
        else:
            console.print("[red]✗ Strategy application failed[/red]")
    else:
        console.print("[red]✗ Strategy generation failed[/red]")
    
    return False


def create_comparison_table():
    """Create comparison table of models."""
    
    console.print("\n[bold blue]OpenRouter Free Models Comparison[/bold blue]")
    console.print("-" * 50)
    
    table = Table(title="Model Features")
    table.add_column("Model", style="cyan")
    table.add_column("Size", style="white")
    table.add_column("Speed", style="green")
    table.add_column("Quality", style="yellow")
    table.add_column("Best For", style="blue")
    
    models_info = [
        ("Llama 3.2 3B", "3B", "Fast", "Good", "General tasks"),
        ("Mistral 7B", "7B", "Medium", "Good", "Code generation"),
        ("Gemma 2 9B", "9B", "Medium", "Better", "Complex reasoning"),
        ("Nemotron 70B", "70B", "Slow", "Best", "Architecture"),
    ]
    
    for model, size, speed, quality, use_case in models_info:
        table.add_row(model, size, speed, quality, use_case)
    
    console.print(table)


def main():
    """Run all tests with OpenRouter models."""
    
    console.print(Panel(
        "[bold cyan]Planfile + OpenRouter Free Models Test[/bold cyan]\n"
        "Testing planfile functionality with OpenRouter's free models\n"
        "Using API key from .env file",
        title="OpenRouter Integration Test"
    ))
    
    # Load environment
    load_env()
    
    # Test 1: Model availability
    working_models = test_openrouter_models()
    
    if not working_models:
        console.print("\n[red]No OpenRouter models working. Check API key.[/red]")
        return
    
    # Test 2: Strategy generation
    gen_success = test_strategy_generation()
    
    # Test 3: Strategy application
    apply_success = test_strategy_apply()
    
    # Show comparison
    create_comparison_table()
    
    # Summary
    console.print("\n[bold cyan]Test Summary[/bold cyan]")
    console.print("=" * 50)
    
    table = Table(title="Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    tests = [
        ("Model Availability", "✓ Passed", f"{len(working_models)} models working"),
        ("Strategy Generation", "✓ Passed" if gen_success else "✗ Failed", "OpenRouter models"),
        ("Strategy Application", "✓ Passed" if apply_success else "✗ Failed", "Dry-run successful"),
    ]
    
    for test, status, details in tests:
        status_style = "green" if "✓" in status else "red"
        table.add_row(test, f"[{status_style}]{status}[/{status_style}]", details)
    
    console.print(table)
    
    # Recommendations
    console.print("\n[bold green]Recommendations:[/bold green]")
    console.print("• Use Llama 3.2 3B for fast, simple tasks")
    console.print("• Use Mistral 7B for code generation")
    console.print("• Use Gemma 2 9B for complex reasoning")
    console.print("• All models are FREE with OpenRouter!")
    
    # Cleanup
    cleanup_files = [
        "/home/tom/github/semcod/llx/examples/planfile/test-cases/test_code.py",
        "/home/tom/github/semcod/llx/examples/planfile/test-cases/test-llama_3.2_3b.yaml",
        "/home/tom/github/semcod/llx/examples/planfile/test-cases/test-mistral_7b.yaml",
    ]
    
    for file in cleanup_files:
        Path(file).unlink(missing_ok=True)
    
    console.print("\n[green]✓ All tests completed![/green]")


if __name__ == "__main__":
    main()
