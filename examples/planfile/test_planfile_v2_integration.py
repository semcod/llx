#!/usr/bin/env python3
"""
Test planfile v2 integration with LLX
"""

import sys
import os
from pathlib import Path

# Add LLX and planfile to path
sys.path.insert(0, '/home/tom/github/semcod/llx')
sys.path.insert(0, '/home/tom/github/semcod/planfile')

def test_planfile_v2_integration():
    """Test if planfile v2 can work with LLX."""
    
    print("Testing planfile v2 with LLX...")
    
    # Test 1: Import planfile v2
    try:
        sys.path.insert(0, '/home/tom/github/semcod/planfile')
        from planfile.models_v2 import Strategy, Task, Sprint
        from planfile.executor_v2 import StrategyExecutor
        print("✓ Planfile v2 imports work")
    except ImportError as e:
        print(f"✗ Planfile v2 import failed: {e}")
        return False
    
    # Test 2: Create a simple strategy
    try:
        strategy_data = {
            "name": "Test Strategy",
            "version": "1.0.0",
            "project_type": "python",
            "domain": "software",
            "goal": "Test integration",
            
            "sprints": [
                {
                    "id": 1,
                    "name": "Test Sprint",
                    "objectives": ["Test objective"],
                    "tasks": [
                        {
                            "name": "Test Task",
                            "description": "Test description",
                            "type": "feature",
                            "model_hints": "free"
                        }
                    ]
                }
            ]
        }
        
        strategy = Strategy(**strategy_data)
        print(f"✓ Strategy created: {strategy.name}")
    except Exception as e:
        print(f"✗ Strategy creation failed: {e}")
        return False
    
    # Test 3: Save and load strategy
    try:
        import yaml
        test_file = Path("/tmp/test_strategy_v2.yaml")
        
        # Save
        with open(test_file, 'w') as f:
            yaml.dump(strategy_data, f)
        print(f"✓ Strategy saved to {test_file}")
        
        # Load with planfile v2
        loaded_v2 = Strategy.load_flexible(test_file)
        print(f"✓ Strategy loaded with planfile v2: {loaded_v2.name}")
        
        # Convert to LLX format
        llx_data = loaded_v2.to_llx_format()
        print(f"✓ Converted to LLX format")
        
        # Save LLX format
        llx_file = Path("/tmp/test_strategy_llx.yaml")
        with open(llx_file, 'w') as f:
            yaml.dump(llx_data, f)
        
        # Load with LLX
        from llx.planfile import load_valid_strategy
        loaded_strategy = load_valid_strategy(str(llx_file))
        print(f"✓ Strategy loaded with LLX: {loaded_strategy.name if hasattr(loaded_strategy, 'name') else 'Unknown'}")
        
        # Clean up
        test_file.unlink()
        llx_file.unlink()
    except Exception as e:
        print(f"✗ Strategy load/save failed: {e}")
        return False
    
    # Test 4: Execute with LLX executor
    try:
        from llx.planfile import execute_strategy
        
        # Create test strategy file for LLX
        llx_strategy_data = {
            "name": "LLX Test Strategy",
            "project_type": "python",
            "domain": "software",
            
            "sprints": [
                {
                    "id": 1,
                    "name": "Test Sprint",
                    "objectives": ["Test objective"],
                    "task_patterns": [
                        {
                            "name": "Test Task",
                            "description": "Test description",
                            "task_type": "feature",
                            "model_hint": "free"
                        }
                    ]
                }
            ]
        }
        
        test_file = Path("/tmp/test_strategy_llx.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(llx_strategy_data, f)
        
        # Execute dry run
        results = execute_strategy(
            strategy_path=str(test_file),
            project_path="/tmp",
            dry_run=True
        )
        
        print(f"✓ Strategy executed with {len(results)} tasks")
        
        # Clean up
        test_file.unlink()
    except Exception as e:
        print(f"✗ Strategy execution failed: {e}")
        return False
    
    print("\n✅ All planfile v2 integration tests passed!")
    return True


if __name__ == "__main__":
    success = test_planfile_v2_integration()
    sys.exit(0 if success else 1)
