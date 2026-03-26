#!/usr/bin/env python3
"""
Test that llx.planfile module works correctly after the strategy merge
"""

import sys
sys.path.insert(0, '/home/tom/github/semcod/llx')

def test_planfile_imports():
    """Test that all planfile imports work correctly."""
    
    print("Testing llx.planfile imports...")
    
    try:
        from llx.planfile import (
            Strategy, Goal, Sprint, TaskPattern, 
            TaskType, ModelHints, ModelTier, QualityGate,
            LLXStrategyBuilder, create_strategy_command,
            load_valid_strategy, run_strategy, 
            verify_strategy_post_execution,
            execute_strategy, TaskResult
        )
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test creating a simple strategy
    print("\nTesting strategy creation...")
    
    goal = Goal(
        short="Test refactoring",
        quality=["Test coverage > 80%"],
        delivery=["Complete in 1 week"]
    )
    
    task_pattern = TaskPattern(
        id="refactor_function",
        type=TaskType.feature,
        title="Refactor {function_name}",
        description="Improve the {function_name} function for better readability",
        model_hints=ModelHints(design="balanced", implementation="balanced")
    )
    
    sprint = Sprint(
        id=1,
        name="Refactoring Sprint",
        objectives=["Improve code quality"],
        tasks=["refactor_function"]
    )
    
    strategy = Strategy(
        name="Test Strategy",
        project_type="test",
        domain="testing",
        goal=goal,
        sprints=[sprint],
        tasks={"patterns": [task_pattern]}
    )
    
    print(f"✅ Created strategy: {strategy.name}")
    print(f"   - Sprints: {len(strategy.sprints)}")
    print(f"   - Task patterns: {len(strategy.get_task_patterns())}")
    
    # Test YAML serialization
    print("\nTesting YAML serialization...")
    
    yaml_output = strategy.model_dump_yaml()
    print("✅ Strategy serialized to YAML")
    
    # Test parsing back
    parsed_strategy = Strategy.model_validate_yaml(yaml_output)
    print(f"✅ Strategy parsed from YAML: {parsed_strategy.name}")
    
    return True

if __name__ == "__main__":
    success = test_planfile_imports()
    if success:
        print("\n🎉 All tests passed! llx.planfile is working correctly.")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
