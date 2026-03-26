#!/usr/bin/env python3
"""
Simple strategy generator - just works!
"""

import os
import sys
from pathlib import Path
from rich.console import Console

console = Console()

def generate_simple_strategy(project_path=".", output="strategy.yaml"):
    """Generate strategy with minimal configuration."""
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv('/home/tom/github/semcod/llx/.env')
    
    # List of models to try in order
    models_to_try = [
        "openrouter/nvidia/nemotron-3-super-120b-a12b:free",  # Default for free tier
        "openrouter/meta-llama/llama-3.2-3b-instruct:free",
        "openrouter/mistral/mistral-7b-instruct:free",
        "openrouter/deepseek/deepseek-chat-v3-0324",
        "ollama/qwen2.5-coder:7b",
        "ollama/llama3.2:3b"
    ]
    
    console.print(f"[blue]Generating strategy for {project_path}...[/blue]")
    
    # Import and generate
    from llx.planfile.generate_strategy import generate_strategy_with_fix, save_fixed_strategy
    
    for model in models_to_try:
        try:
            console.print(f"  Trying model: {model}")
            
            strategy_data = generate_strategy_with_fix(
                project_path=project_path,
                model=model,
                sprints=3,
                focus="improvement"
            )
            
            save_fixed_strategy(strategy_data, output)
            console.print(f"[green]✓ Strategy saved to {output}[/green]")
            
            # Show summary
            console.print("\n[bold]Strategy Summary:[/bold]")
            console.print(f"  Sprints: {len(strategy_data.get('sprints', []))}")
            console.print(f"  Tasks: {sum(len(s.get('tasks', [])) for s in strategy_data.get('sprints', []))}")
            
            return True
            
        except Exception as e:
            console.print(f"[yellow]  ✗ {model} failed: {str(e)[:100]}...[/yellow]")
            continue
    
    console.print(f"[red]✗ All models failed![/red]")
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate refactoring strategy")
    parser.add_argument("path", nargs="?", default=".", help="Project path (default: .)")
    parser.add_argument("-o", "--output", default="strategy.yaml", help="Output file (default: strategy.yaml)")
    
    args = parser.parse_args()
    
    success = generate_simple_strategy(args.path, args.output)
    sys.exit(0 if success else 1)
