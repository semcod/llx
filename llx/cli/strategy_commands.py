"""
LLX Strategy CLI commands.
"""
import typer
from pathlib import Path
from typing import Optional

from ..strategy import (
    create_strategy_command,
    load_valid_strategy,
    run_strategy,
    verify_strategy_post_execution
)

# Create strategy app
strategy_app = typer.Typer(help="Strategy management commands")


@strategy_app.command("create")
def create_strategy(
    output: str = typer.Option("strategy.yaml", help="Output file path"),
    model: str = typer.Option("qwen2.5:3b", help="LLM model to use"),
    local: bool = typer.Option(True, help="Use local model"),
):
    """Create a new strategy interactively with LLM."""
    print("🚀 Starting interactive strategy creation...")
    print(f"Using model: {model} (local: {local})")
    print(f"Output will be saved to: {output}")
    print()
    
    create_strategy_command(output=output, model=model, local=local)


@strategy_app.command("validate")
def validate_strategy(
    strategy_file: Path = typer.Argument(..., help="Strategy YAML file to validate"),
):
    """Validate a strategy YAML file."""
    try:
        strategy = load_valid_strategy(str(strategy_file))
        print(f"✅ Strategy '{strategy.name}' is valid!")
        print(f"   - Project type: {strategy.project_type}")
        print(f"   - Domain: {strategy.domain}")
        print(f"   - Sprints: {len(strategy.sprints)}")
        print(f"   - Task patterns: {len(strategy.get_task_patterns())}")
        print(f"   - Quality gates: {len(strategy.quality_gates)}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        raise typer.Exit(1)


@strategy_app.command("run")
def run_strategy_command(
    strategy_file: Path = typer.Argument(..., help="Strategy YAML file"),
    project_path: Path = typer.Argument(..., help="Project directory path"),
    backend: str = typer.Option("github", help="Backend system (github, jira, gitlab)"),
    dry_run: bool = typer.Option(True, help="Simulate without creating tickets"),
):
    """Run strategy to create tickets."""
    print(f"🏃 Running strategy: {strategy_file}")
    print(f"Project path: {project_path}")
    print(f"Backend: {backend}")
    print(f"Dry run: {dry_run}")
    print()
    
    run_strategy(
        strategy_path=str(strategy_file),
        project_path=str(project_path),
        backend=backend,
        dry_run=dry_run
    )


@strategy_app.command("verify")
def verify_strategy(
    strategy_file: Path = typer.Argument(..., help="Strategy YAML file"),
    project_path: Path = typer.Argument(..., help="Project directory path"),
    backend: Optional[str] = typer.Option(None, help="Backend system for ticket verification"),
):
    """Verify strategy execution."""
    print(f"🔍 Verifying strategy: {strategy_file}")
    print(f"Project path: {project_path}")
    print()
    
    try:
        strategy = load_valid_strategy(str(strategy_file))
        issues = verify_strategy_post_execution(
            strategy=strategy,
            project_path=str(project_path),
            backend=backend
        )
        
        if not any(issues.values()):
            print("✅ Strategy verification passed - no issues found!")
        else:
            print("⚠️  Issues found:")
            for category, items in issues.items():
                if items:
                    print(f"\n{category.upper()}:")
                    for item in items:
                        print(f"  - {item}")
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise typer.Exit(1)


# Add strategy commands to main LLX CLI
def add_strategy_commands(main_app):
    """Add strategy commands to main typer app."""
    main_app.add_typer(strategy_app, name="strategy")
