# LLX Planfile Examples - Comprehensive Guide

This directory contains comprehensive examples demonstrating LLX's planfile integration for strategic codebase refactoring.

## 📁 Directory Structure

```
planfile/
├── README.md                    # This file
├── planfile_dev.sh             # Bash script for planfile management
├── planfile_manager.py         # Advanced Python manager with asyncio
├── run.sh                      # Quick demo script
├── microservice_refactor.py    # Microservice extraction demo
├── async_refactor_demo.py      # Callback hell to async/await demo
├── test_planfile.py           # Unit tests for planfile functionality
└── test-cases/
    ├── test_with_free_models.sh # Test with free LLM models
    └── problematic_code.py      # Sample code with various issues
```

## 🚀 Quick Start

### 1. Basic Usage

```bash
# Generate a refactoring strategy
llx plan generate . --focus complexity --sprints 3

# Review the strategy
llx plan review strategy-*.yaml .

# Dry run to see changes
llx plan apply strategy-*.yaml . --dry-run

# Apply the strategy
llx plan apply strategy-*.yaml .
```

### 2. Using the Demo Scripts

```bash
# Run the main demo
./run.sh

# Test with free models
cd test-cases && ./test_with_free_models.sh

# Test functionality
python3 test_planfile.py
```

### 3. Advanced Management

```bash
# Use the Bash manager
./planfile_dev.sh generate --focus duplication --sprints 2

# Use the Python manager
python3 planfile_manager.py generate --focus complexity --sprints 4 --parallel
```

## 📋 Example Scenarios

### 1. Complexity Reduction
Focus: Reduce cyclomatic complexity and improve code structure

```bash
llx plan generate . --focus complexity --model claude-opus-4 --sprints 4
```

**What it does:**
- Identifies high-complexity functions (CC > 10)
- Suggests function extraction strategies
- Recommends design pattern applications
- Creates step-by-step refactoring plan

### 2. Duplication Elimination
Focus: Remove code duplication and improve DRY compliance

```bash
llx plan generate . --focus duplication --sprints 2
```

**What it does:**
- Detects duplicate code blocks
- Suggests common base classes or utilities
- Plans extraction of shared functionality
- Recommends template method patterns

### 3. Test Coverage Improvement
Focus: Generate comprehensive unit tests

```bash
llx plan generate . --focus tests --sprints 3 --model claude-sonnet-4
```

**What it does:**
- Identifies untested code paths
- Generates test cases for edge cases
- Creates mock objects for dependencies
- Sets up test infrastructure

### 4. Documentation Enhancement
Focus: Improve code documentation

```bash
llx plan generate . --focus docs --sprints 1 --model qwen2.5-coder:7b
```

**What it does:**
- Adds docstrings to undocumented functions
- Creates README files for modules
- Generates API documentation
- Adds inline comments for complex logic

## 🔧 Advanced Features

### Multi-Sprint Execution

Execute strategies in multiple phases:

```bash
# Generate 4-sprint strategy
llx plan generate . --sprints 4 --focus complexity

# Execute sprint by sprint
llx plan apply strategy.yaml . --sprint sprint-1
llx plan apply strategy.yaml . --sprint sprint-2
# ... and so on
```

### Parallel Execution

Execute independent sprints in parallel:

```python
# Using Python manager
python3 planfile_manager.py execute \
    --strategy strategy.yaml \
    --parallel \
    --max-parallel 3
```

## 🎯 Real-World Examples

### Microservice Extraction

See `microservice_refactor.py` for a complete example of extracting a monolithic service into microservices.

```bash
python3 microservice_refactor.py
```

### Async Code Refactoring

See `async_refactor_demo.py` for transforming callback hell to clean async/await patterns.

```bash
python3 async_refactor_demo.py
```

## 🤖 Model Selection

### Free Models

- `google/gemini-2.0-flash-exp:free` - Fast, good for simple tasks
- `openrouter/meta-llama/llama-3.2-3b-instruct:free` - Small, efficient
- `huggingface/mistral-7b-instruct-v0.3:free` - Good balance

### Premium Models

- `claude-opus-4` - Best for complex architecture
- `claude-sonnet-4` - Great for feature implementation
- `gpt-4-turbo` - Good all-around performer

### Local Models

- `qwen2.5-coder:7b` - Excellent for code tasks
- `llama-3.1-8b` - Good general purpose
- `codellama:7b` - Specialized for code

## 📊 Testing Planfile

### Run Unit Tests

```bash
# Basic functionality test
python3 test_planfile.py

# Test with free models
cd test-cases && ./test_with_free_models.sh
```

### Test Custom Scenarios

```python
# Create your own test
from llx.planfile import execute_strategy

results = execute_strategy(
    "my-strategy.yaml",
    ".",
    sprint_filter="sprint-1",
    dry_run=True
)

for result in results:
    print(f"{result.task_name}: {result.status}")
```

## 🛠️ Troubleshooting

### Common Issues

1. **Model not available**
   ```bash
   # Check available models
   llx chat --model list
   
   # Use local model
   llx plan generate . --model qwen2.5-coder:7b
   ```

2. **Strategy generation fails**
   ```bash
   # Check project analysis
   llx analyze . --toon-dir .code2llm
   
   # Try with simpler focus
   llx plan generate . --focus docs --sprints 1
   ```

3. **Execution fails midway**
   ```bash
   # Resume from last sprint
   ./planfile_dev.sh resume strategy-complexity.yaml
   
   # Or run specific sprint
   llx plan apply strategy.yaml . --sprint sprint-3
   ```

## 📚 Best Practices

### 1. Strategy Design
- Start with clear objectives
- Include validation in each sprint
- Plan for rollback points
- Consider team capacity

### 2. Model Selection
- Use premium models for architecture
- Use balanced models for features
- Use local models for simple tasks
- Consider cost constraints

### 3. Execution
- Always dry-run first
- Execute sprint by sprint
- Test after each sprint
- Commit after successful sprints

## 🔗 Integration with MCP

```json
{
  "mcpServers": {
    "llx": {
      "command": "python3",
      "args": ["-m", "llx.mcp.server"]
    }
  }
}
```

Then use in Claude Desktop:
- Generate strategy with `planfile_generate`
- Apply with `planfile_apply`

## 📈 Metrics and Analytics

### Track Improvements

```python
# Before and after metrics
from llx.analysis import analyze_project

before = analyze_project(".", toon_dir=".code2llm-before")
# ... apply strategy ...
after = analyze_project(".", toon_dir=".code2llm-after")

print(f"CC reduced: {before.avg_cc:.1f} → {after.avg_cc:.1f}")
print(f"God modules: {before.god_modules} → {after.god_modules}")
```

## 🤝 Contributing

To add new examples:

1. Create a new Python file or script
2. Follow the existing pattern
3. Include clear documentation
4. Add tests if needed
5. Update this README

## 📄 License

These examples are part of the LLX project. See the main LICENSE file for details.
