#!/usr/bin/env python3
"""
Simple test to verify planfile functionality with free models
Tests basic refactoring scenarios
"""

import subprocess
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def run_command(cmd, capture_output=True):
    """Run command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=60
        )
        return result
    except subprocess.TimeoutExpired:
        console.print("[red]Command timed out[/red]")
        return None


def test_simple_refactoring():
    """Test simple code refactoring."""
    
    console.print("\n[bold blue]Test 1: Simple Function Refactoring[/bold blue]")
    console.print("-" * 50)
    
    # Create simple problematic code
    test_code = '''
def calculate(a, b, c, d, e):
    x = a + b
    y = x + c
    z = y + d
    result = z + e
    return result

def process_data(items):
    processed = []
    for item in items:
        if item > 0:
            processed.append(item * 2)
        else:
            processed.append(item * 3)
    return processed
'''
    
    Path("simple_test.py").write_text(test_code)
    
    # Generate strategy
    console.print("[yellow]Generating refactoring strategy...[/yellow]")
    cmd = "python3 -m llx plan generate . --model openrouter/meta-llama/llama-3.2-3b-instruct:free --sprints 1 --focus complexity --output simple-strategy.yaml"
    result = run_command(cmd)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Strategy generated[/green]")
        
        # Check if strategy file exists and has content
        if Path("simple-strategy.yaml").exists():
            with open("simple-strategy.yaml") as f:
                strategy = yaml.safe_load(f)
            
            console.print(f"[blue]Strategy has {len(strategy.get('sprints', []))} sprint(s)[/blue]")
            
            # Try dry run
            console.print("[yellow]Running dry-run...[/yellow]")
            cmd = "python3 -m llx plan apply simple-strategy.yaml . --dry-run"
            result = run_command(cmd)
            
            if result and result.returncode == 0:
                console.print("[green]✓ Dry-run successful[/green]")
                return True
            else:
                console.print("[red]✗ Dry-run failed[/red]")
                if result:
                    console.print(f"[red]Error: {result.stderr}[/red]")
        else:
            console.print("[red]✗ Strategy file not created[/red]")
    else:
        console.print("[red]✗ Strategy generation failed[/red]")
        if result:
            console.print(f"[red]Error: {result.stderr}[/red]")
    
    return False


def test_duplication_removal():
    """Test duplicate code removal."""
    
    console.print("\n[bold blue]Test 2: Duplicate Code Removal[/bold blue]")
    console.print("-" * 50)
    
    # Create code with duplication
    duplicate_code = '''
def validate_user(user):
    if not user.get('email'):
        return False
    if '@' not in user['email']:
        return False
    if not user.get('name'):
        return False
    if len(user['name']) < 2:
        return False
    return True

def validate_admin(admin):
    if not admin.get('email'):
        return False
    if '@' not in admin['email']:
        return False
    if not admin.get('name'):
        return False
    if len(admin['name']) < 2:
        return False
    if not admin.get('role'):
        return False
    return True

def validate_customer(customer):
    if not customer.get('email'):
        return False
    if '@' not in customer['email']:
        return False
    if not customer.get('name'):
        return False
    if len(customer['name']) < 2:
        return False
    return True
'''
    
    Path("duplicate_test.py").write_text(duplicate_code)
    
    # Generate strategy
    console.print("[yellow]Generating deduplication strategy...[/yellow]")
    cmd = "python3 -m llx plan generate . --model huggingface/mistral-7b-instruct-v0.3:free --sprints 1 --focus duplication --output dedup-strategy.yaml"
    result = run_command(cmd)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Strategy generated[/green]")
        
        # Show strategy preview
        if Path("dedup-strategy.yaml").exists():
            with open("dedup-strategy.yaml") as f:
                strategy = yaml.safe_load(f)
            
            # Show first task
            sprints = strategy.get('sprints', [])
            if sprints and sprints[0].get('task_patterns'):
                first_task = sprints[0]['task_patterns'][0].get('description', 'No description')
                console.print(f"[blue]First task: {first_task[:100]}...[/blue]")
            
            return True
    else:
        console.print("[red]✗ Strategy generation failed[/red]")
        if result:
            console.print(f"[red]Error: {result.stderr}[/red]")
    
    return False


def test_test_generation():
    """Test automated test generation."""
    
    console.print("\n[bold blue]Test 3: Automated Test Generation[/bold blue]")
    console.print("-" * 50)
    
    # Create code without tests
    code_without_tests = '''
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''
    
    Path("calculator.py").write_text(code_without_tests)
    
    # Generate test strategy
    console.print("[yellow]Generating test strategy...[/yellow]")
    cmd = "python3 -m llx plan generate . --model google/gemini-2.0-flash-exp:free --sprints 1 --focus tests --output test-strategy.yaml"
    result = run_command(cmd)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Test strategy generated[/green]")
        
        # Try to apply (dry run)
        console.print("[yellow]Running test generation (dry-run)...[/yellow]")
        cmd = "python3 -m llx plan apply test-strategy.yaml . --dry-run"
        result = run_command(cmd)
        
        if result and result.returncode == 0:
            console.print("[green]✓ Test generation planned successfully[/green]")
            
            # Check if test file would be created
            if "test_calculator.py" in result.stdout:
                console.print("[green]✓ Test file creation planned[/green]")
            
            return True
        else:
            console.print("[red]✗ Test generation failed[/red]")
    else:
        console.print("[red]✗ Test strategy generation failed[/red]")
        if result:
            console.print(f"[red]Error: {result.stderr}[/red]")
    
    return False


def test_model_availability():
    """Check which free models are available."""
    
    console.print("\n[bold blue]Checking Model Availability[/bold blue]")
    console.print("-" * 50)
    
    # Test different free models
    free_models = [
        ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("openrouter/meta-llama/llama-3.2-3b-instruct:free", "Llama 3.2 3B"),
        ("huggingface/mistral-7b-instruct-v0.3:free", "Mistral 7B"),
    ]
    
    available_models = []
    
    for model_id, model_name in free_models:
        console.print(f"[yellow]Testing {model_name}...[/yellow]")
        
        # Simple test command
        cmd = f"python3 -m llx chat --model {model_id} --prompt 'Say hello' --no-execute"
        result = run_command(cmd)
        
        if result and result.returncode == 0:
            console.print(f"[green]✓ {model_name} is available[/green]")
            available_models.append((model_id, model_name))
        else:
            console.print(f"[red]✗ {model_name} not available[/red]")
    
    return available_models


def create_test_report(results):
    """Create a test report."""
    
    console.print("\n[bold cyan]Test Report[/bold cyan]")
    console.print("=" * 50)
    
    table = Table(title="Planfile Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Notes", style="white")
    
    for test_name, success, notes in results:
        status = "✓ Passed" if success else "✗ Failed"
        status_style = "green" if success else "red"
        table.add_row(test_name, f"[{status_style}]{status}[/{status_style}]", notes)
    
    console.print(table)
    
    # Summary
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    console.print(f"\n[bold]Summary: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[green]All tests passed! Planfile is working correctly.[/green]")
    else:
        console.print("[yellow]Some tests failed. Check configuration and model availability.[/yellow]")


def main():
    """Run all tests."""
    
    console.print(Panel(
        "[bold cyan]Planfile Functionality Test[/bold cyan]\n"
        "Testing planfile with free LLM models",
        title="Planfile Test Suite"
    ))
    
    # Check model availability first
    available_models = test_model_availability()
    
    if not available_models:
        console.print("[red]No free models available. Cannot proceed with tests.[/red]")
        console.print("\n[yellow]To fix this:[/yellow]")
        console.print("1. Check your LLX configuration")
        console.print("2. Ensure you have API keys for free providers")
        console.print("3. Or set up a local model with Ollama")
        return
    
    console.print(f"\n[green]Found {len(available_models)} available model(s)[/green]")
    
    # Run tests
    results = []
    
    # Test 1: Simple refactoring
    results.append((
        "Simple Refactoring",
        test_simple_refactoring(),
        "Basic function optimization"
    ))
    
    # Test 2: Duplication removal
    results.append((
        "Duplication Removal",
        test_duplication_removal(),
        "Extract common validation logic"
    ))
    
    # Test 3: Test generation
    results.append((
        "Test Generation",
        test_test_generation(),
        "Generate unit tests automatically"
    ))
    
    # Create report
    create_test_report(results)
    
    # Cleanup
    console.print("\n[yellow]Cleaning up test files...[/yellow]")
    test_files = [
        "simple_test.py", "duplicate_test.py", "calculator.py",
        "simple-strategy.yaml", "dedup-strategy.yaml", "test-strategy.yaml"
    ]
    
    for file in test_files:
        Path(file).unlink(missing_ok=True)
    
    console.print("[green]✓ Cleanup completed[/green]")


if __name__ == "__main__":
    main()
