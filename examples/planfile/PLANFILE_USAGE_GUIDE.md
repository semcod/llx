# LLX Planfile Usage Guide

## Overview
Planfile allows you to define and execute multi-sprint refactoring strategies with intelligent model selection.

## Quick Start

### 1. Create a Strategy
Create a `strategy.yaml` file:

```yaml
name: "My Refactoring Strategy"
project_type: "python"
domain: "software"

sprints:
  - id: 1
    name: "Complexity Reduction"
    objectives:
      - "Extract complex methods"
      - "Add unit tests"
    task_patterns:
      - name: "Extract Method"
        description: "Extract methods with CC > 10"
        task_type: "tech_debt"
        model_hints:
          implementation: "balanced"  # local, cheap, balanced, premium
      - name: "Add Tests"
        description: "Write unit tests for extracted methods"
        task_type: "feature"
        model_hints:
          implementation: "cheap"
```

### 2. Execute Strategy

```bash
# Dry run to see what will happen
llx plan apply strategy.yaml . --dry-run

# Actually execute
llx plan apply strategy.yaml .
```

## Model Selection

LLX automatically selects models based on:
- Task complexity
- Project metrics (files, lines, CC)
- Model hints in strategy
- Available models

### Model Tiers:
- **local**: Local models (Ollama)
- **cheap**: Free/low-cost models
- **balanced**: Good performance/cost ratio
- **premium**: Best quality (GPT-4, Claude)

## Strategy Schema

### Basic Structure
```yaml
name: string           # Strategy name
project_type: string   # python, javascript, etc.
domain: string         # software, web, mobile

sprints:
  - id: int
    name: string
    objectives: string[]
    task_patterns: Task[]
```

### Task Definition
```yaml
task_patterns:
  - name: string
    description: string
    task_type: feature|tech_debt|bug|chore|documentation
    model_hints:
      implementation: local|cheap|balanced|premium
```

## Advanced Features

### Model Hints
Guide model selection per task:
```yaml
model_hints:
  design: "balanced"      # For design phase
  implementation: "cheap"  # For implementation
  review: "premium"       # For code review
```

### Quality Gates
Define success criteria:
```yaml
quality_gates:
  - name: "Complexity Check"
    description: "Verify complexity reduction"
    criteria:
      - "Average CC < 5"
      - "No functions with CC > 10"
    required: true
```

## Best Practices

1. **Start with Dry Run**: Always use `--dry-run` first
2. **Use Model Hints**: Guide expensive models to complex tasks only
3. **Break Down Work**: Split large tasks into smaller ones
4. **Set Quality Gates**: Define clear success criteria
5. **Review Results**: Check generated code before applying

## Integration with OpenRouter

Configure in `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

Free models available:
- `meta-llama/llama-3.2-3b-instruct:free`
- `mistral/mistral-7b-instruct:free`
- `deepseek/deepseek-chat-v3-0324`
- `meta-llama/llama-3.2-3b-instruct:free`

## Example: Full Refactoring Strategy

See `strategy_corrected.yaml` for a complete example with:
- 2 sprints
- 8 task patterns
- 4 quality gates
- Model hints for cost optimization

## Troubleshooting

### Strategy Validation Errors
- Check task_type is valid enum value
- Verify model_hints use correct tier names
- Ensure required fields are present

### Model Selection Issues
- Tasks may use higher-tier models if complex
- Use `model_hints.implementation: "cheap"` for cost control
- Consider local models with Ollama for privacy

### Execution Problems
- Use `--dry-run` to preview
- Check API keys in `.env`
- Verify strategy YAML syntax

## CLI Commands

```bash
# Apply strategy
llx plan apply <strategy.yaml> <project_path> [options]

# Options:
#   --dry-run        Preview without executing
#   --sprint N       Execute only sprint N
#   --model MODEL    Override model selection
```
