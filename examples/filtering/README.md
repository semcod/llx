# LLX Filtering Examples

This directory demonstrates various filtering options and parameter combinations in LLX.

### 1. **Tier-based Filtering**
Filter models by cost/quality tiers:
```bash
# Use cheap model (via model alias)
llx chat --model cheap --prompt "Refactor this function"

# Use balanced model
llx analyze . --model balanced

# Use premium model for complex tasks
llx chat --model premium --prompt "Design a microservices architecture"
```

### 2. **Provider-based Selection**
Choose specific providers:
```bash
# Use only OpenAI models
llx chat --provider openai --prompt "Explain this code"

# Use Anthropic models
llx chat --provider anthropic --prompt "Write documentation"

# Use OpenRouter for variety
llx chat --provider openrouter --prompt "Debug this issue"
```

### 3. **Task-specific Optimization**
Use task hints for better model selection:
```bash
# For refactoring tasks
llx chat --task refactor --prompt "Improve this code structure"

# For quick fixes
llx chat --task quick_fix --prompt "Fix this bug"

# For code review
llx chat --task review --prompt "Review this pull request"

# For documentation
llx chat --task explain --prompt "Explain how this works"
```

# Fast responses for simple tasks
llx chat --model cheap --task quick_fix --prompt "Add error handling"

# High quality for complex tasks
llx chat --model premium --task refactor --prompt "Optimize this algorithm"

# Balanced approach
llx chat --model balanced --task review --prompt "Review this implementation"
```

# Limit to free models
llx chat --local --prompt "What does this function do?"

llx chat --local --prompt "Create full stack app"

# Use budget-friendly options
llx chat --model cheap --prompt "Add unit tests"

# No cost limit (premium available)
llx chat --prompt "Design a complete system architecture"
```

# Local model for privacy
llx chat --local --task refactor --prompt "Refactor this class"

# Cloud model with specific provider and tier
llx chat --provider anthropic --model balanced --task explain --prompt "Explain this algorithm"

# Fast cloud model for quick tasks
llx chat --provider openai --model cheap --task quick_fix --prompt "Fix this syntax error"
```

# Small project - automatically gets cheaper model
cd small-project && llx chat --prompt "Add logging"

# Large project - automatically gets better model
cd large-project && llx chat --prompt "Review architecture"

# Force local regardless of project size
llx chat --local --prompt "Generate API documentation"
```

### 8. **Model Aliases**
Use convenient aliases:
```bash
# Use coding-specialized model
llx chat --model coding --prompt "Implement this feature"

# Use fast model
llx chat --model fast --prompt "Quick review needed"

# Use reliable model
llx chat --model reliable --prompt "Critical bug fix"
```

# Process multiple files with consistent model
for file in src/*.py; do
    llx chat --model cheap --task quick_fix --prompt "Fix linting errors in $(basename $file)" $file
done

# Generate documentation for all modules
llx chat --model balanced --task explain --prompt "Generate module documentation" src/
```

# Start a chat session with specific constraints
llx chat --local --task refactor  # Will prompt for input

# Analyze then chat with same model
MODEL=$(llx analyze . --model balanced | grep "Selected Model" | awk '{print $4}')
llx chat --model $MODEL --prompt "Suggest improvements"
```

## Tips for Effective Filtering

1. **Know your constraints**: Use `--model` for cost control
2. **Match task to model**: Use `--task` hints for better selection
3. **Consider privacy**: Use `--local` for sensitive code
4. **Provider preferences**: Some providers excel at specific tasks
5. **Project size matters**: LLX automatically adjusts based on codebase metrics

# PR validation - fast and cheap
llx chat --model cheap --task review --prompt "Check for common issues" .

# Documentation generation - balanced
llx chat --model balanced --task explain --prompt "Generate API docs" src/

# Security audit - premium
llx chat --model premium --task review --prompt "Security review" auth/
```

# Quick prototyping - local
llx chat --local --task quick_fix --prompt "Add placeholder implementation"

# Code review - balanced
llx chat --model balanced --task review --prompt "Review this change"

# Architecture design - premium
llx chat --model premium --task refactor --prompt "Design system architecture"
```

# Understand codebase - local
llx chat --local --task explain --prompt "How does this work?"

# Best practices - balanced
llx chat --model balanced --task explain --prompt "Suggest improvements"

# Advanced patterns - premium
llx chat --model premium --task refactor --prompt "Apply design patterns"
```
