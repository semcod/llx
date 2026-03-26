#!/usr/bin/env python3
"""
Test planfile v2 integration with LLX
"""

import sys
from pathlib import Path

# Add LLX to path
sys.path.insert(0, '/home/tom/github/semcod/llx')

def test_planfile_v2_integration():
    """Test if planfile v2 can work with LLX."""
    
    print("Testing planfile v2 with LLX...")
    
    # Test 1: Import LLX planfile
    try:
        from llx.planfile import execute_strategy, Strategy, TaskType
        print("✓ LLX planfile imports work")
    except ImportError as e:
        print(f"✗ LLX planfile import failed: {e}")
        return False
    
    # Test 2: Create and execute a V2 strategy
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
        
        # Save strategy to file
        strategy_file = Path("/tmp/test_strategy_v2.yaml")
        import yaml
        strategy_file.write_text(yaml.dump(strategy_data))
        
        # Execute with LLX
        results = execute_strategy(str(strategy_file), dry_run=True)
        print(f"✓ Strategy executed: {len(results)} results")
        
        for result in results:
            print(f"  - {result.task_name}: {result.status}")
        
        # Clean up
        strategy_file.unlink()
        
    except Exception as e:
        print(f"✗ Strategy execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
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
        
        # Load with LLX
        from llx.planfile import load_valid_strategy
        loaded_strategy = load_valid_strategy(str(test_file))
        print(f"✓ Strategy loaded with LLX: {loaded_strategy.name if hasattr(loaded_strategy, 'name') else 'Unknown'}")
        
        # Clean up
        test_file.unlink()
    except Exception as e:
        print(f"✗ Strategy load/save failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ All planfile v2 integration tests passed!")
    return True


if __name__ == "__main__":
    success = test_planfile_v2_integration()
    sys.exit(0 if success else 1)
