"""Simplified strategy builder for LLX planfile."""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage
from .models import Strategy, Goal, Sprint, TaskPattern, TaskType, ModelHints
from .config import PlanfileConfig


class SimpleStrategyBuilder:
    """Simplified strategy builder using LLX client directly."""
    
    def __init__(
        self, 
        model: Optional[str] = None,
        config_file: Optional[Path] = None
    ):
        """Initialize builder.
        
        Args:
            model: Model to use (optional, will use config default)
            config_file: Path to configuration file
        """
        self.model = model
        self.config = None
        self.planfile_config = PlanfileConfig(config_file)
    
    def build_from_analysis(
        self,
        project_path: str,
        focus: str = "complexity",
        sprints: int = 3
    ) -> Strategy:
        """Build strategy from project analysis.
        
        Args:
            project_path: Path to analyze
            focus: Focus area (complexity, duplication, tests, docs)
            sprints: Number of sprints to create
            
        Returns:
            Strategy object
        """
        # Load config
        self.config = LlxConfig.load(project_path)
        
        # Analyze project
        from llx.analysis.collector import analyze_project
        metrics = analyze_project(project_path)
        
        # Generate strategy content
        strategy_content = self._generate_strategy_content(metrics, focus, sprints)
        
        # Parse into Strategy object
        return Strategy(**strategy_content)
    
    def _generate_strategy_content(
        self,
        metrics: Any,
        focus: str,
        sprints: int
    ) -> Dict[str, Any]:
        """Generate strategy content based on metrics."""
        
        # Create basic strategy structure
        strategy = {
            "name": f"{focus.title()} Refactoring Strategy",
            "project_type": "python",
            "domain": "software",
            "goal": {
                "short": f"Improve {focus} in the codebase",
                "quality": [f"Reduce {focus} issues", "Improve maintainability"],
                "delivery": ["Complete in sprints", "Review changes"]
            },
            "sprints": [],
            "task_patterns": []
        }
        
        # Add all task patterns
        all_patterns = []
        for i in range(sprints):
            tasks = self._get_tasks_for_focus(focus, i + 1)
            for j, task in enumerate(tasks):
                pattern = {
                    "id": f"task-{j+1}",
                    "type": task["task_type"].value if hasattr(task["task_type"], 'value') else task["task_type"],
                    "title": task["name"],
                    "description": task["description"],
                    "priority": "medium",
                    "model_hints": task["model_hints"]
                }
                all_patterns.append(pattern)
        
        strategy["tasks"] = {"patterns": all_patterns}
        
        # Generate sprints based on focus
        for i in range(sprints):
            sprint_id = i + 1
            sprint = {
                "id": sprint_id,
                "name": f"Sprint {sprint_id}",
                "objectives": self._get_sprint_objectives(focus, sprint_id, sprints),
                "tasks": [f"task-{j+1}" for j in range(len(self._get_tasks_for_focus(focus, sprint_id)))]
            }
            
            strategy["sprints"].append(sprint)
        
        return strategy
    
    def _get_sprint_objectives(self, focus: str, sprint_id: int, total_sprints: int) -> List[str]:
        """Get objectives for a sprint."""
        objectives_map = {
            "complexity": {
                1: ["Identify high-complexity functions", "Analyze cyclomatic complexity"],
                2: ["Extract complex methods", "Reduce nesting depth"],
                3: ["Refactor remaining issues", "Add tests for refactored code"]
            },
            "duplication": {
                1: ["Scan for duplicate code", "Identify common patterns"],
                2: ["Extract common functionality", "Create shared utilities"],
                3: ["Eliminate remaining duplicates", "Update documentation"]
            },
            "tests": {
                1: ["Analyze test coverage", "Identify untested modules"],
                2: ["Add unit tests", "Improve test quality"],
                3: ["Add integration tests", "Set up CI/CD"]
            },
            "docs": {
                1: ["Review existing documentation", "Identify gaps"],
                2: ["Update API docs", "Add examples"],
                3: ["Create tutorials", "Review and finalize"]
            }
        }
        
        return objectives_map.get(focus, {}).get(sprint_id, ["Complete refactoring tasks"])
    
    def _get_tasks_for_focus(self, focus: str, sprint_id: int) -> List[Dict[str, Any]]:
        """Get tasks for a specific focus and sprint."""
        # Get tasks from config
        focus_config = self.planfile_config.get(f'focus_areas.{focus}')
        if not focus_config:
            # Fallback to default tasks
            return [
                {
                    "name": "Analysis Task",
                    "description": "Analyze and improve code",
                    "task_type": "feature",
                    "model_hints": {"implementation": "balanced"}
                }
            ]
        
        # Convert task names to full task objects
        task_names = focus_config.get("tasks", [])
        tasks = []
        
        for task_name in task_names:
            # Determine task type based on name
            if "test" in task_name.lower():
                task_type = TaskType.documentation if "doc" in task_name.lower() else TaskType.bug
            elif "refactor" in task_name.lower() or "extract" in task_name.lower():
                task_type = TaskType.tech_debt
            else:
                task_type = TaskType.feature
            
            # Determine model tier
            if "complex" in task_name.lower():
                model_hints = {"implementation": "balanced"}
            else:
                model_hints = {"implementation": "cheap"}
            
            tasks.append({
                "name": task_name,
                "description": f"Execute {task_name.lower()}",
                "task_type": task_type,
                "model_hints": model_hints
            })
        
        return tasks


def create_strategy_command(
    project_path: str = ".",
    focus: str = "complexity",
    sprints: int = 3,
    output: Optional[str] = None
) -> Path:
    """Create a strategy file.
    
    Args:
        project_path: Path to analyze
        focus: Focus area
        sprints: Number of sprints
        output: Output file path
        
    Returns:
        Path to created strategy file
    """
    builder = SimpleStrategyBuilder()
    strategy = builder.build_from_analysis(project_path, focus, sprints)
    
    # Determine output path
    if not output:
        output = f"strategy-{focus}-{sprints}sprints.yaml"
    
    output_path = Path(output)
    
    # Save strategy - convert to dict first to avoid Python object tags
    strategy_dict = {
        "name": strategy.name,
        "version": strategy.version,
        "project_type": strategy.project_type,
        "domain": strategy.domain,
        "goal": {
            "short": strategy.goal.short,
            "quality": strategy.goal.quality,
            "delivery": strategy.goal.delivery,
            "metrics": strategy.goal.metrics
        },
        "sprints": []
    }
    
    # Add sprints
    for sprint in strategy.sprints:
        sprint_dict = {
            "id": sprint.id,
            "name": sprint.name,
            "length_days": sprint.length_days,
            "objectives": sprint.objectives,
            "tasks": sprint.tasks
        }
        strategy_dict["sprints"].append(sprint_dict)
    
    # Add tasks/patterns if present
    if hasattr(strategy, 'tasks') and strategy.tasks:
        strategy_dict["tasks"] = {
            "patterns": [
                {
                    "id": p.id,
                    "type": p.type.value if hasattr(p.type, 'value') else str(p.type),
                    "title": p.title,
                    "description": p.description,
                    "priority": p.priority,
                    "model_hints": {
                        "design": p.model_hints.design.value if hasattr(p.model_hints.design, 'value') else p.model_hints.design,
                        "implementation": p.model_hints.implementation.value if hasattr(p.model_hints.implementation, 'value') else p.model_hints.implementation,
                        "review": p.model_hints.review.value if hasattr(p.model_hints.review, 'value') else p.model_hints.review
                    }
                }
                for p in strategy.tasks.get("patterns", [])
            ]
        }
    
    # Save to file
    with open(output_path, 'w') as f:
        yaml.dump(strategy_dict, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Strategy created: {output_path}")
    return output_path


# For backward compatibility
LLXStrategyBuilder = SimpleStrategyBuilder
