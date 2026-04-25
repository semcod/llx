# LLX Planfile - Simplified Integration

This document describes the simplified planfile integration in LLX.

## Overview

The LLX planfile module has been simplified to:
- Support the new V2 format with embedded tasks
- Handle both V1 and V2 formats seamlessly
- Support planfile.yaml format (redsl-generated)
- Reduce complexity and improve maintainability
- Use LLX's built-in model selection and routing

### 1. Simplified Executor
- Removed complex executor implementations
- Single `executor_simple.py` with clean implementation
- Automatic format detection and normalization

### 2. Format Support
- **V1 Format**: Tasks defined separately in `task_patterns`
- **V2 Format**: Tasks embedded directly in sprints
- **planfile.yaml Format**: Redsl-generated format with flat tasks list and sprint task_patterns
- **Mixed Format**: Handles all formats in the same strategy

### 3. Reduced Dependencies
- Removed dependency on external planfile package
- Uses only LLX internals
- Cleaner import structure

### Basic Usage
```python
from llx.planfile import execute_strategy

# Execute strategy (supports V1 and V2)
results = execute_strategy(
    "strategy.yaml",
    project_path=".",
    dry_run=True
)
```

### V2 Format Example
```yaml
name: "My Strategy"
goal: "Improve code quality"

sprints:
  - id: 1
    name: "Refactoring Sprint"
    objectives: ["Extract methods", "Add tests"]
    tasks:  # Embedded tasks (V2)
      - name: "Extract Methods"
        description: "Extract complex methods"
        type: "refactor"
        model_hints: "balanced"
```

### planfile.yaml Format Example (redsl-generated)
```yaml
schema: '1.0'
project: llx
version: 0.1.57
generated: '2026-04-19'
generator: redsl planfile sync
sources:
- project/analysis.toon.yaml
stats:
  total: 68
  todo: 65
  done: 3
tasks:
- id: Q01
  title: 'reduce_complexity: collector (CC=10)'
  description: Module 'collector' has cyclomatic complexity CC=10
  file: llx/analysis/collector.py
  action: reduce_complexity
  priority: 3
  effort: medium
  status: todo
  labels:
  - refactor
  - complexity
sprints:
- id: sprint-1
  name: Code Quality Improvements
  duration: 2 weeks
  objectives:
  - Fix code quality issues
  task_patterns:
  - id: ticket-00506015
    name: Fix magic-numbers issues
    description: Resolve 17 magic-numbers issues
    task_type: prefactor
    priority: high
    model_hints:
      planning: balanced
      implementation: balanced
```

### File Structure
```
llx/planfile/
├── __init__.py           # Main exports
├── models.py            # Pydantic models
├── runner.py            # Strategy loading/validation
├── executor_simple.py   # Simplified executor
├── builder.py           # Strategy builders
└── examples.py          # Example strategies
```

### Executor Flow
1. Load YAML strategy
2. Detect format (V1/V2/planfile.yaml)
3. Normalize to internal format
4. Process sprints and tasks
5. Select model using LLX routing
6. Execute tasks with LLM
7. Return results

### Model Selection
- Uses LLX's built-in model selection
- Considers task hints and project metrics
- Supports all LLX model tiers
- Automatic fallback to default model

## Benefits

1. **Simpler Code**
   - Single executor implementation
   - Clear separation of concerns
   - Easier to maintain

2. **Better UX**
   - Supports both formats
   - Clear error messages
   - Flexible model hints

3. **LLX Integration**
   - Uses LLX routing
   - Leverages project metrics
   - Consistent with LLX patterns

# V1 - Separate patterns
sprints:
  - id: 1
    tasks: ["task1"]
tasks:
  patterns:
    - id: "task1"
      name: "Task 1"

# V2 - Embedded tasks
sprints:
  - id: 1
    tasks:
      - name: "Task 1"
```

# No changes needed - executor handles both formats!
from llx.planfile import execute_strategy
results = execute_strategy("strategy.yaml")
```

## Testing

Run the integration test:
```bash
python3 examples/planfile/test_simple_integration.py
```

## Future Improvements

1. Add more format validation
2. Support for task dependencies
3. Progress tracking and resumption
4. Integration with LLX CLI
5. Template generation

## Summary

The simplified LLX planfile integration provides:
- ✅ Support for V1 and V2 formats
- ✅ Clean, maintainable code
- ✅ Full LLX integration
- ✅ Backward compatibility
- ✅ Better error handling

This makes planfile easier to use and maintain while preserving all functionality.
