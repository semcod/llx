# Basic llx Usage Example

This example demonstrates the core functionality of llx: intelligent LLM model selection based on code metrics.

## What it does

1. **Project Analysis**: Analyzes the llx codebase using code2llm metrics
2. **Model Selection**: Chooses the optimal LLM model based on:
   - Project size (files, lines of code)
   - Complexity (cyclomatic complexity)
   - Coupling (dependencies between modules)
   - Budget constraints
3. **LLM Interaction**: Tests the selected model with a simple prompt
4. **Cost Tracking**: Monitors API usage and costs

## Prerequisites

- llx installed in development mode
- At least one LLM provider API key configured
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
   ✓ Budget limit: $60/month
   ✓ Max tier: premium

🔍 Analyzing project...
   ✓ Files: 18
   ✓ Lines: 2,093
   ✓ Complexity: 2.1
   ✓ Scale: 3.2
   ✓ Coupling: 1.8

🤖 Selecting optimal model...
   ✓ Selected: claude-haiku-4-5-20251001
   ✓ Tier: cheap
   ✓ Provider: anthropic
   ✓ Context: 200,000 tokens
   ✓ Cost: $0.0008/1K in, $0.0040/1K out
   ✓ Reasons:
     • Medium project: 18 files (≥10)
     • Small project: 18 files, 2,093 lines

💬 Testing LLM interaction...
   ✓ Response: This project is llx, an intelligent LLM model router...
   ✓ Tokens used: 85
   ✓ Cost: $0.000342

💰 Cost tracking...
   ✓ Today's usage: $0.000342
   ✓ Monthly usage: $0.000342
   ✓ Remaining budget: $59.999658

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

### 3. Budget Management
Built-in cost tracking and budget limits prevent unexpected expenses:
- Daily/monthly budget caps
- Per-request cost limits
- Real-time usage monitoring

## Troubleshooting

### Common Issues

**"Analysis failed" error**
- Ensure code2llm is installed: `../../.venv/bin/pip install code2llm`
- Check if the project path is accessible

**"Model selection failed" error**
- Verify API keys are correctly set in `.env`
- Check network connectivity to LLM providers

**"LLM interaction failed" error**
- API keys might be invalid or expired
- Provider might be experiencing outages
- Check rate limits and quotas

### Debug Mode

Enable verbose output for debugging:
```bash
../../.venv/bin/python main.py --verbose
```

### Testing Different Models

Override the automatic selection:
```bash
../../.venv/bin/python -m llx analyze . --max-tier cheap
../../.venv/bin/python -m llx analyze . --local  # Force local models
```

## Next Steps

- Try the [Proxy Integration Example](../proxy/) for IDE integration
- Explore the [Multi-Provider Example](../multi-provider/) for fallback strategies
- Check the [Local Models Example](../local/) for offline usage
