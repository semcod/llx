#!/usr/bin/env python3
"""
Final test report for planfile examples
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()


def main():
    console.print(Panel(
        "[bold cyan]Planfile Examples - Test Report[/bold cyan]\n"
        "Testing LLX planfile integration with free models",
        title="Test Summary"
    ))
    
    # Test Results Table
    console.print("\n[bold]Test Results:[/bold]")
    table = Table(title="Planfile Functionality Tests")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Notes", style="white")
    
    test_results = [
        ("LLX Plan Commands", "✓ Working", "All planfile commands available"),
        ("Strategy Generation", "⚠ Partial", "Works but needs model fixes"),
        ("Strategy Apply", "✓ Working", "Successfully applies strategies"),
        ("Strategy Review", "⚠ Limited", "Backend configuration needed"),
        ("Local Models", "✓ Working", "Ollama models accessible"),
        ("Free Cloud Models", "⚠ Limited", "Need proper provider format"),
    ]
    
    for component, status, notes in test_results:
        status_style = "green" if "✓" in status else "yellow" if "⚠" in status else "red"
        table.add_row(component, f"[{status_style}]{status}[/{status_style}]", notes)
    
    console.print(table)
    
    # Working Examples
    console.print("\n[bold]Working Examples:[/bold]")
    working_examples = """
1. **Basic Strategy Application**
   ```bash
   # Create strategy.yaml manually
   llx plan apply strategy.yaml . --dry-run
   ```

2. **Using Local Models**
   ```bash
   # Model works with chat
   llx chat . --model qwen2.5-coder:7b --prompt "Refactor this"
   ```

3. **Demo Scripts**
   ```bash
   python3 microservice_refactor.py  # Shows structure
   python3 async_refactor_demo.py    # Shows patterns
   ```
    """
    console.print(Markdown(working_examples))
    
    # Issues Found
    console.print("\n[bold red]Issues Identified:[/bold red]")
    issues = """
1. **Strategy Generation**: 
   - LiteLLM provider format issues
   - Needs `ollama/model-name` format for local models
   - YAML validation errors in generated strategies

2. **Strategy Review**:
   - Backend configuration required
   - Missing default backend setup

3. **Model Integration**:
   - Free models need proper provider prefixes
   - Some models not accessible via LiteLLM
    """
    console.print(Markdown(issues))
    
    # Recommendations
    console.print("\n[bold green]Recommendations:[/bold green]")
    recommendations = """
1. **For Users**:
   - Use `llx plan apply` with manually created strategies
   - Use local models with `ollama/model-name` format
   - Check example strategies in the repo

2. **For Development**:
   - Fix LiteLLM provider detection
   - Add default backend configuration
   - Improve YAML validation in strategy generation

3. **Testing**:
   - Test with actual refactoring scenarios
   - Validate generated code quality
   - Check test generation functionality
    """
    console.print(Markdown(recommendations))
    
    # Example Working Strategy
    console.print("\n[bold]Example Working Strategy (strategy.yaml):[/bold]")
    example_strategy = """
```yaml
name: "Complexity Reduction"
project_type: "python"
domain: "general"
goal: "Reduce cyclomatic complexity"

sprints:
  - id: 1
    name: "Extract Functions"
    description: "Extract complex logic into smaller functions"
    task_patterns:
      - name: "Refactor complex function"
        description: "Break down function into smaller pieces"
        file_pattern: "*.py"
        model_hint: "qwen2.5-coder:7b"

quality_gates:
  - name: "Complexity Check"
    description: "Verify complexity reduction"
    criteria:
      - "avg_cc <= 10"
    metric: "avg_cc"
    threshold: 10.0
    operator: "<="

success_criteria:
  - "All functions have CC < 10"
  - "Tests pass"
```
    """
    console.print(Markdown(example_strategy))
    
    console.print("\n[bold green]✓ Planfile integration is partially working![/bold green]")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("1. Create strategies manually")
    console.print("2. Use `llx plan apply` for execution")
    console.print("3. Use local models via Ollama")
    console.print("4. Check generated code after applying")


if __name__ == "__main__":
    main()
