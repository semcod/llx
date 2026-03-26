#!/usr/bin/env python3
"""
Planfile Strategy Manager - Advanced orchestration for LLX planfile-driven refactoring.

This manager provides intelligent strategy generation, execution monitoring, and
progress tracking for comprehensive codebase refactoring projects.
"""

import json
import yaml
import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.live import Live

console = Console()


class FocusArea(str, Enum):
    """Focus areas for refactoring strategies."""
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    TESTS = "tests"
    DOCS = "docs"


class ExecutionStatus(str, Enum):
    """Execution status for tasks and sprints."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskMetrics:
    """Metrics for a specific task."""
    name: str
    status: ExecutionStatus
    model_used: str
    execution_time: float
    validation_score: float
    error: Optional[str] = None


@dataclass
class SprintMetrics:
    """Metrics for a sprint."""
    id: str
    name: str
    tasks: List[TaskMetrics]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING


@dataclass
class StrategyMetrics:
    """Overall strategy execution metrics."""
    strategy_file: Path
    focus_area: FocusArea
    sprints: List[SprintMetrics]
    total_cost: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def progress(self) -> float:
        """Calculate overall progress percentage."""
        if not self.sprints:
            return 0.0
        total_tasks = sum(len(sprint.tasks) for sprint in self.sprints)
        completed_tasks = sum(
            sum(1 for task in sprint.tasks if task.status == ExecutionStatus.COMPLETED)
            for sprint in self.sprints
        )
        return (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0


class PlanfileManager:
    """Advanced manager for planfile-driven refactoring strategies."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.planfile_dir = self.project_root / ".llx" / "planfile"
        self.metrics_dir = self.project_root / ".code2llm"
        self.planfile_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_strategy(
        self,
        focus: FocusArea,
        sprints: int = 3,
        model: Optional[str] = None,
        output: Optional[Path] = None,
        custom_prompt: Optional[str] = None
    ) -> Path:
        """Generate a comprehensive refactoring strategy."""
        
        # Analyze current state
        console.print("[blue]Analyzing current project state...[/blue]")
        await self._analyze_project()
        
        # Select optimal model if not specified
        if not model:
            model = await self._select_model_for_focus(focus)
            console.print(f"[green]Selected model: {model}[/green]")
        
        # Generate strategy
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        strategy_file = output or self.planfile_dir / f"strategy-{focus}-{timestamp}.yaml"
        
        cmd = [
            "llx", "plan", "generate",
            str(self.project_root),
            "--model", model,
            "--sprints", str(sprints),
            "--focus", focus.value,
            "--output", str(strategy_file)
        ]
        
        if custom_prompt:
            # Save custom prompt to temp file and reference it
            prompt_file = self.planfile_dir / "custom-prompt.txt"
            prompt_file.write_text(custom_prompt)
            cmd.extend(["--custom-prompt", str(prompt_file)])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating strategy...", total=None)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                console.print(f"[red]Strategy generation failed: {result.stderr}[/red]")
                raise RuntimeError(f"Strategy generation failed: {result.stderr}")
        
        console.print(f"[green]✓ Strategy generated: {strategy_file.name}[/green]")
        
        # Show strategy summary
        await self._show_strategy_summary(strategy_file)
        
        return strategy_file
    
    async def review_strategy(self, strategy_file: Path) -> Dict[str, Any]:
        """Review strategy quality gates and provide recommendations."""
        
        console.print("[blue]Reviewing strategy quality gates...[/blue]")
        
        cmd = ["llx", "plan", "review", str(strategy_file), str(self.project_root)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse review results
        review_data = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy_file.name,
            "quality_gates": [],
            "recommendations": [],
            "estimated_cost": 0.0,
            "estimated_duration": "0h 0m"
        }
        
        # Extract quality gates from output
        for line in result.stdout.split('\n'):
            if '✓' in line or '✗' in line:
                review_data["quality_gates"].append(line.strip())
        
        # Estimate metrics
        with open(strategy_file) as f:
            strategy = yaml.safe_load(f)
        
        total_tasks = sum(
            len(sprint.get("task_patterns", []))
            for sprint in strategy.get("sprints", [])
        )
        review_data["estimated_cost"] = total_tasks * 0.02  # Rough estimate
        review_data["estimated_duration"] = f"{total_tasks * 5 // 60}h {total_tasks * 5 % 60}m"
        
        # Display review
        self._display_review(review_data)
        
        return review_data
    
    async def execute_strategy(
        self,
        strategy_file: Path,
        sprint_filter: Optional[str] = None,
        dry_run: bool = False,
        parallel: bool = False,
        max_parallel: int = 2
    ) -> StrategyMetrics:
        """Execute a refactoring strategy with monitoring."""
        
        console.print(f"[blue]Executing strategy: {strategy_file.name}[/blue]")
        
        # Load strategy
        with open(strategy_file) as f:
            strategy = yaml.safe_load(f)
        
        # Initialize metrics
        metrics = StrategyMetrics(
            strategy_file=strategy_file,
            focus_area=FocusArea(strategy.get("focus", "complexity")),
            sprints=[],
            start_time=datetime.now()
        )
        
        # Create backup if not dry run
        if not dry_run:
            await self._create_backup()
        
        # Execute sprints
        sprints_to_execute = strategy.get("sprints", [])
        if sprint_filter:
            sprints_to_execute = [
                s for s in sprints_to_execute 
                if s.get("id") == sprint_filter
            ]
        
        if parallel and not sprint_filter:
            await self._execute_sprints_parallel(
                sprints_to_execute, metrics, dry_run, max_parallel
            )
        else:
            await self._execute_sprints_sequential(
                sprints_to_execute, metrics, dry_run
            )
        
        metrics.end_time = datetime.now()
        
        # Show final report
        self._display_execution_report(metrics)
        
        # Save metrics
        await self._save_metrics(metrics)
        
        return metrics
    
    async def monitor_execution(
        self,
        strategy_file: Path,
        refresh_interval: int = 5
    ) -> None:
        """Monitor strategy execution in real-time."""
        
        metrics_file = self.planfile_dir / f"{strategy_file.stem}-metrics.json"
        
        def generate_display():
            if not metrics_file.exists():
                return Panel("[yellow]Waiting for execution to start...[/yellow]")
            
            with open(metrics_file) as f:
                data = json.load(f)
            
            # Create progress table
            table = Table(title="Execution Progress")
            table.add_column("Sprint", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Progress", style="blue")
            table.add_column("Tasks", style="white")
            
            for sprint in data.get("sprints", []):
                status = sprint.get("status", "pending")
                status_style = {
                    "completed": "green",
                    "in_progress": "yellow",
                    "failed": "red",
                    "pending": "white"
                }.get(status, "white")
                
                completed = sum(
                    1 for task in sprint.get("tasks", [])
                    if task.get("status") == "completed"
                )
                total = len(sprint.get("tasks", []))
                progress = f"{completed}/{total}" if total > 0 else "0/0"
                
                table.add_row(
                    sprint.get("id", "unknown"),
                    f"[{status_style}]{status}[/{status_style}]",
                    progress,
                    f"{total} tasks"
                )
            
            overall_progress = data.get("progress", 0)
            panel = Panel(
                table,
                title=f"Overall Progress: {overall_progress:.1f}%",
                border_style="blue"
            )
            
            return panel
        
        # Live monitoring
        with Live(generate_display(), refresh_per_second=1) as live:
            while True:
                live.update(generate_display())
                await asyncio.sleep(refresh_interval)
    
    async def _analyze_project(self) -> Dict[str, Any]:
        """Analyze project metrics."""
        cmd = [
            "llx", "analyze", str(self.project_root),
            "--toon-dir", str(self.metrics_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {"output": result.stdout, "error": result.stderr}
    
    async def _select_model_for_focus(self, focus: FocusArea) -> str:
        """Select optimal model based on focus area."""
        model_map = {
            FocusArea.COMPLEXITY: "claude-opus-4",
            FocusArea.DUPLICATION: "claude-sonnet-4",
            FocusArea.TESTS: "claude-sonnet-4",
            FocusArea.DOCS: "qwen2.5-coder:7b"
        }
        return model_map.get(focus, "claude-sonnet-4")
    
    async def _show_strategy_summary(self, strategy_file: Path) -> None:
        """Display strategy summary."""
        with open(strategy_file) as f:
            strategy = yaml.safe_load(f)
        
        console.print("\n[bold cyan]Strategy Summary:[/bold cyan]")
        console.print(f"  Description: {strategy.get('description', 'N/A')}")
        console.print(f"  Focus: {strategy.get('focus', 'N/A')}")
        console.print(f"  Sprints: {len(strategy.get('sprints', []))}")
        
        total_tasks = sum(
            len(sprint.get("task_patterns", []))
            for sprint in strategy.get("sprints", [])
        )
        console.print(f"  Total Tasks: {total_tasks}")
        
        # Show sprint breakdown
        tree = Tree("Sprints")
        for sprint in strategy.get("sprints", []):
            sprint_node = tree.add(f"[blue]{sprint.get('id', 'unknown')}[/blue]: {sprint.get('name', 'Unnamed')}")
            for task in sprint.get("task_patterns", []):
                sprint_node.add(f"• {task.get('name', 'Unnamed task')}")
        
        console.print(tree)
    
    def _display_review(self, review_data: Dict[str, Any]) -> None:
        """Display strategy review results."""
        console.print("\n[bold cyan]Strategy Review:[/bold cyan]")
        
        # Quality gates
        if review_data["quality_gates"]:
            console.print("\n[bold]Quality Gates:[/bold]")
            for gate in review_data["quality_gates"]:
                console.print(f"  {gate}")
        
        # Estimates
        console.print(f"\n[bold]Estimated Cost:[/bold] ${review_data['estimated_cost']:.2f}")
        console.print(f"[bold]Estimated Duration:[/bold] {review_data['estimated_duration']}")
        
        # Recommendations
        if review_data["recommendations"]:
            console.print("\n[bold]Recommendations:[/bold]")
            for rec in review_data["recommendations"]:
                console.print(f"  • {rec}")
    
    async def _execute_sprints_sequential(
        self,
        sprints: List[Dict],
        metrics: StrategyMetrics,
        dry_run: bool
    ) -> None:
        """Execute sprints one by one."""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            overall_task = progress.add_task("Overall Progress", total=len(sprints))
            
            for sprint_data in sprints:
                sprint = await self._execute_sprint(
                    sprint_data, progress, dry_run
                )
                metrics.sprints.append(sprint)
                progress.advance(overall_task)
                
                # Save intermediate metrics
                await self._save_metrics(metrics)
    
    async def _execute_sprints_parallel(
        self,
        sprints: List[Dict],
        metrics: StrategyMetrics,
        dry_run: bool,
        max_parallel: int
    ) -> None:
        """Execute multiple sprints in parallel."""
        
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def execute_with_semaphore(sprint_data: Dict):
            async with semaphore:
                progress = Progress(console=console)
                return await self._execute_sprint(sprint_data, progress, dry_run)
        
        # Execute all sprints
        tasks = [execute_with_semaphore(sprint) for sprint in sprints]
        results = await asyncio.gather(*tasks)
        metrics.sprints.extend(results)
    
    async def _execute_sprint(
        self,
        sprint_data: Dict,
        progress: Progress,
        dry_run: bool
    ) -> SprintMetrics:
        """Execute a single sprint."""
        
        sprint = SprintMetrics(
            id=sprint_data.get("id", "unknown"),
            name=sprint_data.get("name", "Unnamed"),
            tasks=[],
            start_time=datetime.now(),
            status=ExecutionStatus.IN_PROGRESS
        )
        
        # Build command
        cmd = [
            "llx", "plan", "apply",
            str(self.project_root / ".llx" / "planfile" / "current-strategy.yaml"),
            str(self.project_root),
            "--sprint", sprint.id
        ]
        
        if dry_run:
            cmd.append("--dry-run")
        
        # Execute sprint
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse results
        if result.returncode == 0:
            sprint.status = ExecutionStatus.COMPLETED
        else:
            sprint.status = ExecutionStatus.FAILED
            console.print(f"[red]Sprint {sprint.id} failed: {result.stderr}[/red]")
        
        sprint.end_time = datetime.now()
        
        # Parse task results (simplified)
        for task_data in sprint_data.get("task_patterns", []):
            task = TaskMetrics(
                name=task_data.get("name", "Unnamed"),
                status=ExecutionStatus.COMPLETED if sprint.status == ExecutionStatus.COMPLETED else ExecutionStatus.FAILED,
                model_used="auto-selected",
                execution_time=0.0,
                validation_score=0.0
            )
            sprint.tasks.append(task)
        
        return sprint
    
    async def _create_backup(self) -> None:
        """Create project backup before execution."""
        backup_dir = self.planfile_dir / "backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup source code
        src_dir = self.project_root / "src"
        if src_dir.exists():
            subprocess.run(["cp", "-r", str(src_dir), str(backup_dir)], check=True)
        
        console.print(f"[green]✓ Backup created: {backup_dir.name}[/green]")
    
    def _display_execution_report(self, metrics: StrategyMetrics) -> None:
        """Display final execution report."""
        console.print("\n[bold cyan]Execution Report:[/bold cyan]")
        
        # Summary table
        table = Table(title="Execution Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        duration = (metrics.end_time - metrics.start_time).total_seconds() / 3600
        table.add_row("Duration", f"{duration:.2f} hours")
        table.add_row("Progress", f"{metrics.progress:.1f}%")
        table.add_row("Total Sprints", str(len(metrics.sprints)))
        table.add_row("Completed", f"{sum(1 for s in metrics.sprints if s.status == ExecutionStatus.COMPLETED)}")
        table.add_row("Failed", f"{sum(1 for s in metrics.sprints if s.status == ExecutionStatus.FAILED)}")
        
        console.print(table)
        
        # Sprint details
        for sprint in metrics.sprints:
            status_color = {
                ExecutionStatus.COMPLETED: "green",
                ExecutionStatus.FAILED: "red",
                ExecutionStatus.IN_PROGRESS: "yellow",
                ExecutionStatus.PENDING: "white"
            }.get(sprint.status, "white")
            
            console.print(f"\n[bold]Sprint {sprint.id}:[/bold] [{status_color}]{sprint.value}[/{status_color}]")
            for task in sprint.tasks:
                task_status = "✓" if task.status == ExecutionStatus.COMPLETED else "✗"
                console.print(f"  {task_status} {task.name}")
    
    async def _save_metrics(self, metrics: StrategyMetrics) -> None:
        """Save execution metrics to file."""
        metrics_file = self.planfile_dir / f"{metrics.strategy_file.stem}-metrics.json"
        
        # Convert to dict
        data = asdict(metrics)
        data["start_time"] = metrics.start_time.isoformat() if metrics.start_time else None
        data["end_time"] = metrics.end_time.isoformat() if metrics.end_time else None
        
        for sprint in data["sprints"]:
            sprint["start_time"] = sprint["start_time"] if sprint["start_time"] else None
            sprint["end_time"] = sprint["end_time"] if sprint["end_time"] else None
        
        with open(metrics_file, "w") as f:
            json.dump(data, f, indent=2)


# CLI Application
app = typer.Typer(help="Planfile Strategy Manager - Advanced orchestration for LLX planfile-driven refactoring")


@app.command()
def generate(
    focus: FocusArea = typer.Option(..., help="Focus area for refactoring"),
    sprints: int = typer.Option(3, help="Number of sprints to generate"),
    model: Optional[str] = typer.Option(None, help="LLM model to use"),
    output: Optional[Path] = typer.Option(None, help="Output file for strategy"),
    project: Path = typer.Option(".", help="Project directory"),
    parallel: bool = typer.Option(False, help="Enable parallel execution"),
):
    """Generate a refactoring strategy."""
    
    async def _generate():
        manager = PlanfileManager(project)
        strategy_file = await manager.generate_strategy(
            focus=focus,
            sprints=sprints,
            model=model,
            output=output
        )
        
        # Ask if user wants to review
        if typer.confirm("Review the generated strategy?"):
            await manager.review_strategy(strategy_file)
        
        # Ask if user wants to execute
        if typer.confirm("Execute the strategy now?"):
            await manager.execute_strategy(strategy_file, parallel=parallel)
    
    asyncio.run(_generate())


@app.command()
def review(
    strategy: Path = typer.Argument(..., help="Strategy file to review"),
    project: Path = typer.Option(".", help="Project directory"),
):
    """Review strategy quality gates."""
    
    async def _review():
        manager = PlanfileManager(project)
        await manager.review_strategy(strategy)
    
    asyncio.run(_review())


@app.command()
def execute(
    strategy: Path = typer.Argument(..., help="Strategy file to execute"),
    sprint: Optional[str] = typer.Option(None, help="Specific sprint to execute"),
    dry_run: bool = typer.Option(False, help="Simulate execution"),
    parallel: bool = typer.Option(False, help="Execute sprints in parallel"),
    max_parallel: int = typer.Option(2, help="Maximum parallel sprints"),
    project: Path = typer.Option(".", help="Project directory"),
):
    """Execute a refactoring strategy."""
    
    async def _execute():
        manager = PlanfileManager(project)
        await manager.execute_strategy(
            strategy_file=strategy,
            sprint_filter=sprint,
            dry_run=dry_run,
            parallel=parallel,
            max_parallel=max_parallel
        )
    
    asyncio.run(_execute())


@app.command()
def monitor(
    strategy: Path = typer.Argument(..., help="Strategy file to monitor"),
    project: Path = typer.Option(".", help="Project directory"),
):
    """Monitor strategy execution in real-time."""
    
    async def _monitor():
        manager = PlanfileManager(project)
        await manager.monitor_execution(strategy)
    
    asyncio.run(_monitor())


@app.command()
def status(
    project: Path = typer.Option(".", help="Project directory"),
):
    """Show current status of all strategies."""
    
    manager = PlanfileManager(project)
    
    # List all strategies
    strategies = list(manager.planfile_dir.glob("strategy-*.yaml"))
    
    if not strategies:
        console.print("[yellow]No strategies found[/yellow]")
        return
    
    table = Table(title="Strategy Status")
    table.add_column("Strategy", style="cyan")
    table.add_column("Focus", style="white")
    table.add_column("Progress", style="green")
    table.add_column("Status", style="blue")
    
    for strategy_file in sorted(strategies):
        metrics_file = manager.planfile_dir / f"{strategy_file.stem}-metrics.json"
        
        if metrics_file.exists():
            with open(metrics_file) as f:
                data = json.load(f)
            
            progress = data.get("progress", 0)
            status = "Completed" if data.get("end_time") else "In Progress"
            focus = data.get("focus_area", "unknown")
        else:
            progress = 0
            status = "Not Started"
            focus = "unknown"
        
        table.add_row(
            strategy_file.name,
            focus,
            f"{progress:.1f}%",
            status
        )
    
    console.print(table)


if __name__ == "__main__":
    app()
