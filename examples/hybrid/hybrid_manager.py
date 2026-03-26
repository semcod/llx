#!/usr/bin/env python3
"""
Hybrid Cloud-Local Development Manager
Optimizes LLX usage by combining cloud and local models intelligently.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

# Add llx to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx.config import LlxConfig
from llx.analysis.collector import ProjectMetrics
from llx.routing.selector import select_model, ModelTier


class TaskType(Enum):
    """Classification of development tasks."""
    BOILERPLATE = "boilerplate"
    SIMPLE_FIX = "simple_fix"
    DOCUMENTATION = "documentation"
    UNIT_TEST = "unit_test"
    REFACTORING = "refactoring"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    INTEGRATION = "integration"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLEX_ALGORITHM = "complex_algorithm"


class TaskClassifier:
    """Classifies tasks to determine optimal model selection."""
    
    def __init__(self):
        self.task_patterns = {
            TaskType.BOILERPLATE: [
                "create", "generate", "scaffold", "template", "boilerplate",
                "setup", "initialize", "structure", "skeleton"
            ],
            TaskType.SIMPLE_FIX: [
                "fix", "bug", "error", "typo", "lint", "format",
                "simple", "quick", "minor", "small"
            ],
            TaskType.DOCUMENTATION: [
                "document", "readme", "comment", "explain", "describe",
                "manual", "guide", "tutorial", "api docs"
            ],
            TaskType.UNIT_TEST: [
                "test", "spec", "unit test", "pytest", "jest",
                "coverage", "tdd", "testing"
            ],
            TaskType.REFACTORING: [
                "refactor", "improve", "optimize", "clean", "restructure",
                "reorganize", "simplify", "maintain"
            ],
            TaskType.FEATURE_IMPLEMENTATION: [
                "implement", "add", "feature", "functionality", "capability",
                "build", "develop", "create feature"
            ],
            TaskType.INTEGRATION: [
                "integrate", "connect", "api", "service", "database",
                "external", "third-party", "interface"
            ],
            TaskType.ARCHITECTURE: [
                "architecture", "design", "system", "structure", "pattern",
                "microservices", "scalable", "enterprise"
            ],
            TaskType.SECURITY: [
                "security", "auth", "authentication", "authorization",
                "encrypt", "secure", "vulnerability", "audit"
            ],
            TaskType.PERFORMANCE: [
                "performance", "optimize", "speed", "memory", "cpu",
                "efficient", "fast", "scalable", "benchmark"
            ],
            TaskType.COMPLEX_ALGORITHM: [
                "algorithm", "complex", "mathematical", "computational",
                "machine learning", "ai", "data structure"
            ]
        }
        
        self.task_tier_mapping = {
            TaskType.BOILERPLATE: ModelTier.CHEAP,
            TaskType.SIMPLE_FIX: ModelTier.CHEAP,
            TaskType.DOCUMENTATION: ModelTier.CHEAP,
            TaskType.UNIT_TEST: ModelTier.CHEAP,
            TaskType.REFACTORING: ModelTier.BALANCED,
            TaskType.FEATURE_IMPLEMENTATION: ModelTier.BALANCED,
            TaskType.INTEGRATION: ModelTier.BALANCED,
            TaskType.ARCHITECTURE: ModelTier.PREMIUM,
            TaskType.SECURITY: ModelTier.PREMIUM,
            TaskType.PERFORMANCE: ModelTier.PREMIUM,
            TaskType.COMPLEX_ALGORITHM: ModelTier.PREMIUM
        }
    
    def classify_task(self, prompt: str) -> TaskType:
        """Classify a task based on prompt content."""
        prompt_lower = prompt.lower()
        
        # Score each task type based on keyword matches
        scores = {}
        for task_type, keywords in self.task_patterns.items():
            score = sum(1 for keyword in keywords if keyword in prompt_lower)
            if score > 0:
                scores[task_type] = score
        
        # Return the task type with highest score
        if scores:
            return max(scores, key=scores.get)
        
        # Default to feature implementation
        return TaskType.FEATURE_IMPLEMENTATION
    
    def get_recommended_tier(self, task_type: TaskType, prefer_local: bool = False) -> Tuple[ModelTier, bool]:
        """Get recommended model tier for task type."""
        if prefer_local and task_type in [TaskType.BOILERPLATE, TaskType.SIMPLE_FIX, TaskType.DOCUMENTATION]:
            return ModelTier.LOCAL, True
        
        tier = self.task_tier_mapping.get(task_type, ModelTier.BALANCED)
        use_local = prefer_local and tier in [ModelTier.CHEAP, ModelTier.FREE]
        
        return tier, use_local


class HybridManager:
    """Manages hybrid cloud-local development workflow."""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.config = LlxConfig.load(project_path)
        self.classifier = TaskClassifier()
        self.metrics = self._analyze_project()
        self.usage_log = self._load_usage_log()
        
    def _analyze_project(self) -> ProjectMetrics:
        """Analyze project metrics."""
        from llx.analysis import analyze_project
        return analyze_project(str(self.project_path))
    
    def _load_usage_log(self) -> List[Dict]:
        """Load usage log from file."""
        log_file = self.project_path / ".llx" / "usage.json"
        if log_file.exists():
            with open(log_file) as f:
                return json.load(f)
        return []
    
    def _save_usage_log(self):
        """Save usage log to file."""
        log_dir = self.project_path / ".llx"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "usage.json"
        
        with open(log_file, 'w') as f:
            json.dump(self.usage_log, f, indent=2)
    
    def _log_usage(self, task_type: TaskType, tier: ModelTier, provider: str, cost: float, success: bool):
        """Log LLX usage for analytics."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type.value,
            "tier": tier.value,
            "provider": provider,
            "estimated_cost": cost,
            "success": success
        }
        self.usage_log.append(entry)
        self._save_usage_log()
    
    def execute_task(
        self,
        prompt: str,
        *,
        force_tier: Optional[ModelTier] = None,
        prefer_local: bool = False,
        provider: Optional[str] = None,
        execute: bool = False,
        output_dir: Optional[str] = None
    ) -> bool:
        """
        Execute a task with intelligent model selection.
        
        Args:
            prompt: Task description
            force_tier: Override automatic tier selection
            prefer_local: Prefer local models when possible
            provider: Specific provider to use
            execute: Execute generated code
            output_dir: Output directory for generated files
            
        Returns:
            True if successful
        """
        # Classify task
        task_type = self.classifier.classify_task(prompt)
        
        # Determine optimal tier
        if force_tier:
            tier = force_tier
            use_local = prefer_local and tier == ModelTier.LOCAL
        else:
            tier, use_local = self.classifier.get_recommended_tier(task_type, prefer_local)
        
        # Build LLX command
        cmd = ["llx", "chat", "--model", tier.value, "--task", "refactor"]
        
        if provider:
            cmd.extend(["--provider", provider])
        
        if use_local:
            cmd.append("--local")
        
        if output_dir:
            cmd.extend(["--output", output_dir])
        
        cmd.extend(["--prompt", prompt])
        
        # Estimate cost
        estimated_cost = self._estimate_cost(tier, provider)
        
        print(f"🎯 Task: {task_type.value}")
        print(f"🤖 Model: {tier.value} ({'local' if use_local else 'cloud'})")
        print(f"💰 Estimated cost: ${estimated_cost:.4f}")
        
        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=str(self.project_path)
            )
            
            print("✅ Task completed successfully!")
            
            # Log usage
            actual_provider = provider or self._get_provider_for_tier(tier)
            self._log_usage(task_type, tier, actual_provider, estimated_cost, True)
            
            # Execute if requested
            if execute:
                self._execute_generated_code(output_dir)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Task failed: {e}")
            
            # Try fallback
            if not use_local and tier != ModelTier.LOCAL:
                print("🔄 Trying local model as fallback...")
                return self.execute_task(
                    prompt,
                    force_tier=ModelTier.LOCAL,
                    prefer_local=True,
                    execute=execute,
                    output_dir=output_dir
                )
            
            # Log failure
            actual_provider = provider or self._get_provider_for_tier(tier)
            self._log_usage(task_type, tier, actual_provider, estimated_cost, False)
            
            return False
    
    def _estimate_cost(self, tier: ModelTier, provider: Optional[str]) -> float:
        """Estimate cost for task execution."""
        # Simple cost estimation based on tier
        cost_per_1k_tokens = {
            ModelTier.FREE: 0.0,
            ModelTier.LOCAL: 0.0,
            ModelTier.CHEAP: 0.002,
            ModelTier.BALANCED: 0.01,
            ModelTier.PREMIUM: 0.05
        }
        
        base_cost = cost_per_1k_tokens.get(tier, 0.01)
        
        # Adjust for provider
        provider_multipliers = {
            "anthropic": 1.2,
            "openai": 1.0,
            "openrouter": 0.8,
            "google": 0.9
        }
        
        if provider:
            base_cost *= provider_multipliers.get(provider, 1.0)
        
        # Estimate 2k tokens for average task
        return base_cost * 2
    
    def _get_provider_for_tier(self, tier: ModelTier) -> str:
        """Get default provider for tier."""
        if tier == ModelTier.LOCAL:
            return "ollama"
        elif tier in [ModelTier.FREE, ModelTier.CHEAP]:
            return "openrouter"
        else:
            return "anthropic"
    
    def _execute_generated_code(self, output_dir: Optional[str]):
        """Execute generated code if possible."""
        if not output_dir or not Path(output_dir).exists():
            return
        
        work_dir = self.project_path / output_dir
        os.chdir(work_dir)
        
        # Detect and run setup
        if (work_dir / "package.json").exists():
            print("📦 Installing Node.js dependencies...")
            subprocess.run(["npm", "install"], check=True)
        elif (work_dir / "requirements.txt").exists():
            print("🐍 Installing Python dependencies...")
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        elif (work_dir / "go.mod").exists():
            print("🏗️  Building Go application...")
            subprocess.run(["go", "build"], check=True)
    
    def batch_process(self, tasks: List[str], budget: Optional[float] = None):
        """Process multiple tasks with budget constraints."""
        total_cost = 0
        
        for i, task in enumerate(tasks, 1):
            print(f"\n📋 Task {i}/{len(tasks)}")
            print("-" * 40)
            
            # Check budget
            if budget and total_cost >= budget:
                print(f"💸 Budget reached (${total_cost:.2f}/${budget:.2f})")
                break
            
            # Execute task
            success = self.execute_task(task)
            
            if success:
                # Update cost
                last_entry = self.usage_log[-1] if self.usage_log else None
                if last_entry:
                    total_cost += last_entry["estimated_cost"]
            else:
                print("⚠️ Task failed, continuing...")
        
        print(f"\n💰 Total cost: ${total_cost:.4f}")
        print(f"✅ Completed: {sum(1 for e in self.usage_log[-len(tasks):] if e['success'])}/{len(tasks)} tasks")
    
    def analyze_usage(self) -> Dict:
        """Analyze usage patterns."""
        if not self.usage_log:
            return {"message": "No usage data available"}
        
        # Calculate statistics
        total_cost = sum(entry["estimated_cost"] for entry in self.usage_log)
        success_rate = sum(1 for entry in self.usage_log if entry["success"]) / len(self.usage_log)
        
        # Task type distribution
        task_distribution = {}
        for entry in self.usage_log:
            task_type = entry["task_type"]
            task_distribution[task_type] = task_distribution.get(task_type, 0) + 1
        
        # Tier distribution
        tier_distribution = {}
        for entry in self.usage_log:
            tier = entry["tier"]
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Provider distribution
        provider_distribution = {}
        for entry in self.usage_log:
            provider = entry["provider"]
            provider_distribution[provider] = provider_distribution.get(provider, 0) + 1
        
        return {
            "total_tasks": len(self.usage_log),
            "total_cost": total_cost,
            "success_rate": success_rate,
            "task_distribution": task_distribution,
            "tier_distribution": tier_distribution,
            "provider_distribution": provider_distribution,
            "avg_cost_per_task": total_cost / len(self.usage_log)
        }
    
    def optimize_workflow(self) -> Dict:
        """Suggest workflow optimizations based on usage patterns."""
        analysis = self.analyze_usage()
        
        if "message" in analysis:
            return analysis
        
        suggestions = []
        
        # Cost optimization
        if analysis["total_cost"] > 10:
            suggestions.append("Consider using more local models to reduce costs")
        
        # Success rate optimization
        if analysis["success_rate"] < 0.8:
            suggestions.append("Try breaking down complex tasks into smaller ones")
        
        # Tier optimization
        premium_usage = analysis["tier_distribution"].get("premium", 0)
        if premium_usage > analysis["total_tasks"] * 0.3:
            suggestions.append("Consider using balanced tier for non-critical tasks")
        
        # Task pattern optimization
        most_common_task = max(analysis["task_distribution"], key=analysis["task_distribution"].get)
        if most_common_task in ["boilerplate", "simple_fix"]:
            suggestions.append("Create templates for common tasks to reduce repetition")
        
        return {
            "analysis": analysis,
            "suggestions": suggestions
        }


def main():
    parser = argparse.ArgumentParser(description="LLX Hybrid Development Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Execute command
    exec_parser = subparsers.add_parser("execute", help="Execute a task")
    exec_parser.add_argument("prompt", help="Task description")
    exec_parser.add_argument("-t", "--tier", choices=["cheap", "balanced", "premium", "local"])
    exec_parser.add_argument("-p", "--provider", help="LLM provider")
    exec_parser.add_argument("-l", "--local", action="store_true", help="Prefer local models")
    exec_parser.add_argument("-e", "--execute", action="store_true", help="Execute generated code")
    exec_parser.add_argument("-o", "--output", help="Output directory")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Process multiple tasks")
    batch_parser.add_argument("file", help="File with tasks (one per line)")
    batch_parser.add_argument("-b", "--budget", type=float, help="Budget limit")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze usage patterns")
    
    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Get optimization suggestions")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = HybridManager()
    
    if args.command == "execute":
        tier = ModelTier(args.tier) if args.tier else None
        success = manager.execute_task(
            args.prompt,
            force_tier=tier,
            provider=args.provider,
            prefer_local=args.local,
            execute=args.execute,
            output_dir=args.output
        )
        
        if not success:
            sys.exit(1)
            
    elif args.command == "batch":
        with open(args.file) as f:
            tasks = [line.strip() for line in f if line.strip()]
        
        manager.batch_process(tasks, args.budget)
        
    elif args.command == "analyze":
        analysis = manager.analyze_usage()
        print(json.dumps(analysis, indent=2))
        
    elif args.command == "optimize":
        optimization = manager.optimize_workflow()
        print(json.dumps(optimization, indent=2))


if __name__ == "__main__":
    main()
