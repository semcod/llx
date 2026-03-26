#!/usr/bin/env python3
"""
Updated test to use available free models
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
    """Test simple code refactoring with OpenRouter free models."""
    
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
    
    # Generate strategy with OpenRouter free model
    console.print("[yellow]Generating refactoring strategy with OpenRouter Nemotron...[/yellow]")
    cmd = "python3 -m llx plan generate . --model nemotron-3-super --sprints 1 --focus complexity --output simple-strategy.yaml"
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
    """Test duplicate code removal with OpenRouter."""
    
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
    
    # Generate strategy with OpenRouter
    console.print("[yellow]Generating deduplication strategy with OpenRouter Mistral...[/yellow]")
    cmd = "python3 -m llx plan generate . --model openrouter/mistral-7b-instruct:free --sprints 1 --focus duplication --output dedup-strategy.yaml"
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
    console.print("[yellow]Generating test strategy with OpenRouter Gemma...[/yellow]")
    cmd = "python3 -m llx plan generate . --model openrouter/google/gemma-2-9b-it:free --sprints 1 --focus tests --output test-strategy.yaml"
    result = run_command(cmd)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Test strategy generated[/green]")
        
        # Try to apply (dry run)
        console.print("[yellow]Running test generation (dry-run)...[/yellow]")
        cmd = "python3 -m llx plan apply test-strategy.yaml . --dry-run"
        result = run_command(cmd)
        
        if result and result.returncode == 0:
            console.print("[green]✓ Test generation planned successfully[/green]")
            
            # Check output
            if result.stdout:
                console.print(f"[blue]Output: {result.stdout[:200]}...[/blue]")
            
            return True
        else:
            console.print("[red]✗ Test generation failed[/red]")
    else:
        console.print("[red]✗ Test strategy generation failed[/red]")
        if result:
            console.print(f"[red]Error: {result.stderr}[/red]")
    
    return False


def test_planfile_commands():
    """Test basic planfile commands."""
    
    console.print("\n[bold blue]Test 4: Planfile Commands[/bold blue]")
    console.print("-" * 50)
    
    # Test plan command help
    console.print("[yellow]Testing plan command help...[/yellow]")
    cmd = "python3 -m llx plan --help"
    result = run_command(cmd)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Plan command available[/green]")
        
        # Check subcommands
        if "generate" in result.stdout and "apply" in result.stdout and "review" in result.stdout:
            console.print("[green]✓ All planfile subcommands available[/green]")
            return True
        else:
            console.print("[red]✗ Missing planfile subcommands[/red]")
    else:
        console.print("[red]✗ Plan command not working[/red]")
    
    return False


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
        console.print("[yellow]Some tests failed. Check the output above.[/yellow]")


def main():
    """Run all tests with available models."""
    
    console.print(Panel(
        "[bold cyan]Planfile Functionality Test[/bold cyan]\n"
        "Testing planfile with available free models",
        title="Planfile Test Suite"
    ))
    
    # Run tests
    results = []
    
    # Test 1: Simple refactoring
    results.append((
        "Simple Refactoring",
        test_simple_refactoring(),
        "Basic function optimization with nemotron"
    ))
    
    # Test 2: Duplication removal
    results.append((
        "Duplication Removal",
        test_duplication_removal(),
        "Extract common validation with qwen2.5-coder:7b"
    ))
    
    # Test 3: Test generation
    results.append((
        "Test Generation",
        test_test_generation(),
        "Generate unit tests with nemotron"
    ))
    
    # Test 4: Commands
    results.append((
        "Planfile Commands",
        test_planfile_commands(),
        "Check if all planfile commands work"
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
