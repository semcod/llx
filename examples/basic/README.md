# Basic llx Usage Example

This example demonstrates the core functionality of llx: intelligent LLM model selection based on code metrics.

## What it does

1. **Project Analysis**: Analyzes the llx codebase using code2llm metrics
2. **Model Selection**: Chooses the optimal LLM model based on:
   - Project size (files, lines of code)
   - Complexity (cyclomatic complexity)
   - Coupling (dependencies between modules)
3. **Configuration Check**: Loads the current project config and prints the active tier
4. **Provider Availability**: Reports which provider keys are configured

## Prerequisites

- llx installed in development mode
- At least one LLM provider API key configured if you want to see provider availability checks
- Python 3.10+

## Setup

1. **Copy environment configuration:**
   ```bash
   cp ../../.env .env
   ```

2. **Configure API keys** (edit `.env`):
   ```bash
   # For Anthropic Claude models
   ANTHROPIC_API_KEY=sk-ant-api03-...
   
   # For OpenRouter (300+ models)
   OPENROUTER_API_KEY=sk-or-v1-...
   
   # For OpenAI models
   OPENAI_API_KEY=sk-...
   ```

3. **Install llx** (if not already done):
   ```bash
   cd ../../
   .venv/bin/pip install -e .
   ```

## Running the Example

### Quick Start
```bash
./run.sh
```

### Manual Execution
```bash
# Set environment variables
export $(grep -v '^#' .env | xargs)

# Run the example
../../.venv/bin/python main.py
```

## Expected Output

```
🚀 llx Basic Usage Example
==================================================

📋 Loading configuration...
   ✓ Default tier: balanced
   ✓ LiteLLM URL: http://localhost:4000

🔍 Analyzing project...
   ✓ Files: 76
   ✓ Lines: 25,721
   ✓ Complexity: 4.6
   ✓ Scale: 51.1
   ✓ Coupling: 75.0

🤖 Selecting optimal model...
   ✓ Selected: claude-opus-4-20250514
   ✓ Tier: premium
   ✓ Provider: anthropic
   ✓ Context: 200,000 tokens
   ✓ Reasons:
     • Large project: 76 files (≥50)
     • Large codebase: 25,721 lines (≥20,000)

🔑 Provider availability...
   ✓ Anthropic API key available
   ✓ OpenRouter API key available
   💡 API keys available - LLM interaction ready

✅ Example completed successfully!
```

## Key Concepts Demonstrated

### 1. Metric-Driven Selection
llx analyzes your actual code metrics rather than using abstract scores:
- **File count** → Determines project scale
- **Line count** → Indicates project size
- **Cyclomatic complexity** → Measures code complexity
- **Coupling** → Assesses module dependencies

### 2. Cost Optimization
The router balances capability with cost:
- **Small projects** → Free/cheap models
- **Medium projects** → Balanced models
- **Large/complex projects** → Premium models

### 3. Configuration Awareness
The example loads the current project config and checks which provider keys are present.

## Troubleshooting

### Common Issues

**"Analysis failed" error**
- Ensure code2llm is installed: `../../.venv/bin/pip install code2llm`
- Check if the project path is accessible

**"Model selection failed" error**
- Verify the project root is correct and `llx.yaml` is readable
- Check that your local `llx` environment is installed correctly

**"Provider availability" warning**
- API keys are optional for the analysis + selection demo
- Configure provider keys in `.env` if you want to verify availability checks
- Check rate limits and quotas if the provider-specific demo later fails

### Debug Mode

Enable verbose output for debugging:
```bash
../../.venv/bin/python main.py --verbose
```

### Testing Different Models

Override the automatic selection:
```bash
../../.venv/bin/python -m llx analyze . --model cheap
../../.venv/bin/python -m llx analyze . --local  # Force local models
```

## Next Steps

- Try the [Proxy Integration Example](../proxy/) for IDE integration
- Explore the [Multi-Provider Example](../multi-provider/) for fallback strategies
- Check the [Local Models Example](../local/) for offline usage
