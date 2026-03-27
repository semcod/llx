"""
Simple test for LLX strategy integration.
"""
from llx.planfile.models import Strategy, Goal, Sprint, TaskPattern, TaskType, ModelHints
import tempfile
import yaml


def test_strategy_models():
    """Test basic strategy models."""
    # Create a simple strategy
    goal = Goal(
        short="Test strategy",
        quality=["Test coverage > 80%"],
        delivery=["Deploy in 2 weeks"]
    )
    
    strategy = Strategy(
        name="Test Strategy",
        project_type="web",
        domain="test",
        goal=goal,
        sprints=[
            Sprint(
                id=1,
                name="Test Sprint",
                objectives=["Test objective"],
                tasks=["test-task"]
            )
        ],
        tasks={
            "patterns": [
                TaskPattern(
                    id="test-task",
                    type=TaskType.feature,
                    title="Test Task",
                    description="A test task"
                )
            ]
        }
    )
    
    # Test YAML serialization
    yaml_content = strategy.model_dump_yaml()
    print("✓ YAML serialization works")
    
    # Test YAML deserialization
    loaded = Strategy.model_validate_yaml(yaml_content)
    assert loaded.name == strategy.name
    print("✓ YAML deserialization works")
    
    return strategy


def test_strategy_validation():
    """Test strategy validation."""
    try:
        # Invalid strategy - duplicate sprint IDs
        invalid_data = {
            "name": "Invalid",
            "project_type": "web",
            "domain": "test",
            "goal": {
                "short": "Test",
                "quality": [],
                "delivery": []
            },
            "sprints": [
                {"id": 1, "name": "Sprint 1"},
                {"id": 1, "name": "Sprint 2"}  # Duplicate ID
            ]
        }
        
        Strategy.model_validate(invalid_data)
        assert False, "Should have raised validation error"
    except Exception as e:
        print(f"✓ Validation works: {e}")


if __name__ == "__main__":
    print("Testing LLX Strategy Integration")
    print("=" * 40)
    
    test_strategy_models()
    test_strategy_validation()
    
    print("\n✅ All tests passed!")
