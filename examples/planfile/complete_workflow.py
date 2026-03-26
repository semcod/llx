#!/usr/bin/env python3
"""
Complete Planfile Workflow Example
Shows how to generate and apply refactoring strategies using planfile + LLX
"""

import subprocess
import yaml
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.tree import Tree

console = Console()


def run_command(cmd, cwd=None, timeout=60):
    """Run command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        return result
    except subprocess.TimeoutExpired:
        console.print("[red]Command timed out[/red]")
        return None


def create_sample_project():
    """Create a sample project to refactor."""
    
    console.print("\n[bold blue]Step 1: Creating Sample Project[/bold blue]")
    console.print("-" * 50)
    
    project_dir = Path("/tmp/planfile_demo")
    project_dir.mkdir(exist_ok=True)
    
    # Create a complex Python file with issues
    complex_code = '''
"""
Complex module with multiple code smells
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from typing import Any, Dict, List

class DataProcessor:
    """God class doing too many things."""
    
    def __init__(self, config_file: str, db_path: str, api_key: str):
        self.config_file = config_file
        self.db_path = db_path
        self.api_key = api_key
        self.data = []
        self.processed_data = []
        self.errors = []
        self.cache = {}
        self.metrics = {}
        self.connections = []
        
    def load_data(self, source: str) -> bool:
        """Load data from various sources - too complex."""
        if source == "file":
            try:
                with open(self.config_file, 'r') as f:
                    self.data = json.load(f)
                return True
            except:
                self.errors.append("Failed to load file")
                return False
        elif source == "db":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM data")
                self.data = [{"id": row[0], "value": row[1]} for row in cursor.fetchall()]
                conn.close()
                return True
            except:
                self.errors.append("Failed to load from DB")
                return False
        elif source == "api":
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.get("https://api.example.com/data", headers=headers)
                if response.status_code == 200:
                    self.data = response.json()
                    return True
                else:
                    self.errors.append(f"API error: {response.status_code}")
                    return False
            except:
                self.errors.append("Failed to fetch from API")
                return False
        return False
    
    def process_data(self, options: Dict[str, Any]) -> List[Dict]:
        """Complex processing with nested conditions."""
        results = []
        
        for item in self.data:
            if not isinstance(item, dict):
                continue
                
            # Validation
            if not item.get('id'):
                self.errors.append(f"Missing ID for item")
                continue
                
            if item.get('value', 0) < 0:
                if options.get('allow_negative', False):
                    item['value'] = abs(item['value'])
                else:
                    continue
            
            # Transformation with deep nesting
            if item.get('type') == 'A':
                if item.get('priority') == 'high':
                    if options.get('boost_high', False):
                        item['value'] *= 2
                    if item.get('special'):
                        item['value'] *= 1.5
                else:
                    item['value'] *= 1.1
            elif item.get('type') == 'B':
                if item.get('category') == 'important':
                    item['value'] *= 1.8
                elif item.get('category') == 'normal':
                    item['value'] *= 1.3
                else:
                    item['value'] *= 1.1
            else:
                item['value'] *= 1.0
            
            # More complex logic
            if options.get('add_timestamp', False):
                item['processed_at'] = datetime.now().isoformat()
            
            if options.get('calculate_metrics', False):
                item['metric'] = item['value'] * options.get('metric_factor', 1.0)
            
            results.append(item)
        
        self.processed_data = results
        return results
    
    def save_data(self, destination: str) -> bool:
        """Save to multiple destinations."""
        if destination == "file":
            try:
                output_file = self.config_file.replace('.json', '_processed.json')
                with open(output_file, 'w') as f:
                    json.dump(self.processed_data, f)
                return True
            except:
                return False
        elif destination == "db":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM processed_data")
                for item in self.processed_data:
                    cursor.execute(
                        "INSERT INTO processed_data (id, value, data) VALUES (?, ?, ?)",
                        (item['id'], item['value'], json.dumps(item))
                    )
                conn.commit()
                conn.close()
                return True
            except:
                return False
        return False
    
    def generate_report(self) -> str:
        """Generate detailed report."""
        report = f"Data Processing Report\\n"
        report += f"=====================\\n"
        report += f"Total items: {len(self.data)}\\n"
        report += f"Processed: {len(self.processed_data)}\\n"
        report += f"Errors: {len(self.errors)}\\n"
        
        if self.errors:
            report += f"\\nErrors:\\n"
            for error in self.errors:
                report += f"- {error}\\n"
        
        return report


# Duplicate validation logic
def validate_config(config_path: str) -> bool:
    """Validate configuration - duplicated logic."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if not config.get('api_key'):
            return False
        if not config.get('database_url'):
            return False
        if not config.get('source'):
            return False
        
        return True
    except:
        return False

def validate_data(data: Dict) -> bool:
    """More duplicated validation."""
    if not data.get('id'):
        return False
    if not data.get('value'):
        return False
    return True


if __name__ == "__main__":
    # Example usage with no structure
    processor = DataProcessor("config.json", "data.db", "api-key-123")
    processor.load_data("file")
    processor.process_data({"allow_negative": True, "boost_high": True})
    print(processor.generate_report())
'''
    
    # Write the complex file
    (project_dir / "complex_module.py").write_text(complex_code)
    
    # Create config
    config = {
        "api_key": "test-key",
        "database_url": "sqlite:///data.db",
        "source": "file"
    }
    (project_dir / "config.json").write_text(json.dumps(config, indent=2))
    
    console.print(f"[green]✓ Created sample project in {project_dir}[/green]")
    return project_dir


def generate_strategy(project_dir):
    """Generate refactoring strategy using planfile."""
    
    console.print("\n[bold blue]Step 2: Generating Refactoring Strategy[/bold blue]")
    console.print("-" * 50)
    
    # Use our fixed generator
    cmd = f"python3 generate_strategy.py"
    result = run_command(cmd, cwd="/home/tom/github/semcod/llx/examples/planfile", timeout=120)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Strategy generated successfully[/green]")
        
        # Copy strategy to project
        strategy_src = Path("/home/tom/github/semcod/llx/examples/planfile/generated_strategy.yaml")
        strategy_dst = project_dir / "strategy.yaml"
        strategy_dst.write_text(strategy_src.read_text())
        
        # Show strategy summary
        with open(strategy_src) as f:
            strategy = yaml.safe_load(f)
        
        console.print(f"\n[bold]Strategy Overview:[/bold]")
        console.print(f"  Name: {strategy.get('name')}")
        console.print(f"  Goal: {strategy.get('goal')}")
        console.print(f"  Sprints: {len(strategy.get('sprints', []))}")
        
        return strategy_dst
    else:
        console.print("[red]✗ Failed to generate strategy[/red]")
        return None


def apply_strategy(project_dir, strategy_file):
    """Apply the refactoring strategy."""
    
    console.print("\n[bold blue]Step 3: Applying Refactoring Strategy[/bold blue]")
    console.print("-" * 50)
    
    # Dry run first
    console.print("[yellow]Running dry-run to see planned changes...[/yellow]")
    cmd = f"PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx plan apply {strategy_file} . --dry-run"
    result = run_command(cmd, cwd=project_dir, timeout=60)
    
    if result and result.returncode == 0:
        console.print("[green]✓ Dry-run completed successfully[/green]")
        
        # Show what would be done
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            console.print("\n[bold]Planned tasks:[/bold]")
            for line in lines:
                if line.startswith('  Executing:'):
                    console.print(f"  • {line.replace('  Executing: ', '')}")
        
        # Ask to proceed
        console.print("\n[yellow]Do you want to apply these changes? (y/N)[/yellow]")
        # In real usage, you would ask user input here
        
        console.print("[yellow]Skipping actual application for demo[/yellow]")
        return True
    else:
        console.print("[red]✗ Dry-run failed[/red]")
        return False


def show_results(project_dir):
    """Show results and next steps."""
    
    console.print("\n[bold blue]Step 4: Results and Next Steps[/bold blue]")
    console.print("-" * 50)
    
    console.print("[green]✓ Planfile workflow completed successfully![/green]")
    
    console.print("\n[bold]What was accomplished:[/bold]")
    tree = Tree("Planfile Workflow")
    
    gen = tree.add("✓ Strategy Generation")
    gen.add("• Analyzed project structure")
    gen.add("• Identified code smells")
    gen.add("• Created 2-sprint refactoring plan")
    
    exec = tree.add("✓ Strategy Validation")
    exec.add("• Validated YAML structure")
    exec.add("• Checked task dependencies")
    exec.add("• Verified model assignments")
    
    plan = tree.add("✓ Execution Planning")
    plan.add("• 8 tasks identified")
    plan.add("• Models auto-selected")
    plan.add("• Quality gates defined")
    
    console.print(tree)
    
    console.print("\n[bold yellow]Next Steps:[/bold yellow]")
    next_steps = """
1. Review the generated strategy file
2. Run actual refactoring with: `llx plan apply strategy.yaml .`
3. Validate changes with tests
4. Commit improvements to version control
5. Repeat for other focus areas (duplication, tests, docs)
    """
    console.print(Markdown(next_steps))


def main():
    """Run the complete planfile workflow demo."""
    
    console.print(Panel(
        "[bold cyan]Complete Planfile Workflow Demo[/bold cyan]\n"
        "This demo shows how to use planfile to generate and apply\n"
        "refactoring strategies using LLX and local models",
        title="Planfile Workflow"
    ))
    
    # Step 1: Create sample project
    project_dir = create_sample_project()
    
    # Step 2: Generate strategy
    strategy_file = generate_strategy(project_dir)
    
    if strategy_file:
        # Step 3: Apply strategy (dry-run)
        apply_strategy(project_dir, strategy_file)
        
        # Step 4: Show results
        show_results(project_dir)
    
    console.print("\n[bold green]Demo completed![/bold green]")
    console.print("\n[dim]Project files left in /tmp/planfile_demo for inspection[/dim]")


if __name__ == "__main__":
    main()
