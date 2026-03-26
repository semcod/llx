#!/usr/bin/env python3
"""
Advanced filtering example showing programmatic model selection
based on various criteria and constraints.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add llx to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx.config import LlxConfig
from llx.routing.selector import select_model, ModelTier
from llx.analysis.collector import ProjectMetrics
from llx.routing.client import LlxClient, ChatMessage


class SmartLLXClient:
    """Smart client that automatically selects the best model based on constraints."""
    
    def __init__(self, project_path: str = "."):
        self.config = LlxConfig.load(project_path)
        self.project_path = Path(project_path)
        self.metrics = self._analyze_project()
        
    def _analyze_project(self) -> ProjectMetrics:
        """Analyze project metrics."""
        from llx.analysis import analyze_project
        return analyze_project(str(self.project_path))
    
    def chat_with_constraints(
        self,
        prompt: str,
        *,
        max_tier: Optional[ModelTier] = None,
        provider: Optional[str] = None,
        prefer_local: bool = False,
        task_hint: Optional[str] = None,
        cost_limit: Optional[float] = None,
        speed_priority: bool = False
    ) -> str:
        """
        Chat with automatic model selection based on constraints.
        
        Args:
            prompt: The prompt to send
            max_tier: Maximum model tier to use
            provider: Specific provider to use
            prefer_local: Prefer local models
            task_hint: Type of task (refactor, explain, quick_fix, etc.)
            cost_limit: Maximum cost limit in USD
            speed_priority: Prioritize speed over quality
        """
        # Apply speed priority by adjusting max tier
        if speed_priority and not max_tier:
            max_tier = ModelTier.BALANCED if self.metrics.total_files > 10 else ModelTier.CHEAP
        
        # Select model with constraints
        selection = select_model(
            self.metrics,
            self.config,
            prefer_local=prefer_local,
            max_tier=max_tier,
            task_hint=task_hint
        )
        
        # Apply provider filter if specified
        if provider and selection.model.provider != provider:
            # Find best model from specified provider
            provider_models = [
                m for m in self.config.models.values() 
                if m.provider == provider
            ]
            if provider_models:
                # Choose the best one within tier limit
                if max_tier:
                    tier_order = [ModelTier.FREE, ModelTier.LOCAL, ModelTier.CHEAP, 
                                ModelTier.BALANCED, ModelTier.PREMIUM]
                    max_index = tier_order.index(max_tier)
                    for model in provider_models:
                        # Simple heuristic: use model name to determine tier
                        if "premium" in model.name.lower() and tier_order.index(ModelTier.PREMIUM) <= max_index:
                            selection.model = model
                            break
                        elif "balanced" in model.name.lower() and tier_order.index(ModelTier.BALANCED) <= max_index:
                            selection.model = model
                            break
                        elif "cheap" in model.name.lower() and tier_order.index(ModelTier.CHEAP) <= max_index:
                            selection.model = model
                            break
                else:
                    selection.model = provider_models[0]
        
        # Check cost limit
        if cost_limit:
            estimated_cost = (selection.model.cost_per_1k_input + selection.model.cost_per_1k_output) / 1000
            if estimated_cost > cost_limit:
                # Downgrade to cheaper model
                if max_tier != ModelTier.FREE:
                    return self.chat_with_constraints(
                        prompt, max_tier=ModelTier.FREE, provider=provider,
                        prefer_local=prefer_local, task_hint=task_hint,
                        cost_limit=cost_limit, speed_priority=speed_priority
                    )
        
        print(f"🎯 Selected: {selection.model.model_id} ({selection.model.provider})")
        print(f"📊 Reason: {'; '.join(selection.reasons)}")
        
        # Send chat
        with LlxClient(self.config) as client:
            response = client.chat(
                messages=[ChatMessage(role="user", content=prompt)],
                model=selection.model.model_id
            )
            return response.content


def demonstrate_filtering():
    """Demonstrate various filtering scenarios."""
    
    print("🚀 Advanced LLX Filtering Demo")
    print("=" * 50)
    
    client = SmartLLXClient()
    
    # Scenario 1: Quick bug fix (speed priority)
    print("\n🏃 Scenario 1: Quick Bug Fix (Speed Priority)")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Fix this bug: division by zero error in calculate_average()",
        speed_priority=True,
        task_hint="quick_fix"
    )
    print(f"Response: {response[:100]}...")
    
    # Scenario 2: Sensitive code (local only)
    print("\n🔒 Scenario 2: Sensitive Code (Local Only)")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Review this authentication code for security issues",
        prefer_local=True,
        task_hint="review"
    )
    print(f"Response: {response[:100]}...")
    
    # Scenario 3: Budget-conscious refactoring
    print("\n💰 Scenario 3: Budget-conscious Refactoring")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Refactor this class to use dependency injection",
        max_tier=ModelTier.CHEAP,
        task_hint="refactor",
        cost_limit=0.01
    )
    print(f"Response: {response[:100]}...")
    
    # Scenario 4: Provider-specific task
    print("\n🔌 Scenario 4: Provider-specific Task")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Generate comprehensive API documentation",
        provider="anthropic",
        task_hint="explain"
    )
    print(f"Response: {response[:100]}...")
    
    # Scenario 5: Premium architecture design
    print("\n💎 Scenario 5: Premium Architecture Design")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Design a microservices architecture for this e-commerce platform",
        max_tier=ModelTier.PREMIUM,
        task_hint="refactor"
    )
    print(f"Response: {response[:100]}...")
    
    # Scenario 6: Balanced code review
    print("\n⚖️  Scenario 6: Balanced Code Review")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Review this pull request and suggest improvements",
        max_tier=ModelTier.BALANCED,
        task_hint="review"
    )
    print(f"Response: {response[:100]}...")
    
    # Scenario 7: Free tier for learning
    print("\n🆓 Scenario 7: Free Tier for Learning")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Explain how the decorator pattern works in Python",
        max_tier=ModelTier.FREE,
        task_hint="explain"
    )
    print(f"Response: {response[:100]}...")
    
    # Scenario 8: Complex constraints
    print("\n🧩 Scenario 8: Complex Constraints")
    print("-" * 50)
    response = client.chat_with_constraints(
        "Optimize this database query for performance",
        max_tier=ModelTier.BALANCED,
        provider="openrouter",
        task_hint="refactor",
        prefer_local=False,
        cost_limit=0.05
    )
    print(f"Response: {response[:100]}...")


def interactive_filtering():
    """Interactive filtering demo."""
    print("\n🎮 Interactive Filtering Demo")
    print("=" * 50)
    
    client = SmartLLXClient()
    
    while True:
        print("\nAvailable constraints:")
        print("1. Speed priority (fast)")
        print("2. Cost limit (cheap)")
        print("3. Privacy first (local)")
        print("4. Quality first (premium)")
        print("5. Provider choice")
        print("6. Task-specific")
        print("7. Exit")
        
        choice = input("\nSelect constraint (1-7): ").strip()
        
        if choice == "7":
            break
            
        prompt = input("Enter your prompt: ").strip()
        
        if choice == "1":
            response = client.chat_with_constraints(prompt, speed_priority=True)
        elif choice == "2":
            response = client.chat_with_constraints(prompt, max_tier=ModelTier.CHEAP)
        elif choice == "3":
            response = client.chat_with_constraints(prompt, prefer_local=True)
        elif choice == "4":
            response = client.chat_with_constraints(prompt, max_tier=ModelTier.PREMIUM)
        elif choice == "5":
            provider = input("Enter provider (anthropic/openai/openrouter): ").strip()
            response = client.chat_with_constraints(prompt, provider=provider)
        elif choice == "6":
            task = input("Enter task (refactor/explain/quick_fix/review): ").strip()
            response = client.chat_with_constraints(prompt, task_hint=task)
        else:
            print("Invalid choice!")
            continue
            
        print(f"\nResponse: {response}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced LLX filtering demo")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run interactive demo")
    args = parser.parse_args()
    
    if args.interactive:
        interactive_filtering()
    else:
        demonstrate_filtering()
