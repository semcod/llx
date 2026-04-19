# Aider Integration Examples

This directory contains examples demonstrating how to use Aider (AI pair programming tool) with LLX.

## Overview

Aider is an AI pair programming tool that works directly in your terminal. When integrated with LLX, you get:
- Intelligent model selection based on your codebase
- Automatic routing to local or cloud models
- Seamless integration with LLX's metrics analysis

## Files

- `demo.py` - Complete demonstration of LLX + Aider workflow
- `run.sh` - Quick script to run the demo
- `README.md` - This file

# Pull Aider image
docker pull paulgauthier/aider

# Ensure Ollama is running
docker run -d -v ollama:/root/.ollama -p 11434:11434 ollama/ollama

# Pull a coding model
docker exec -it <ollama_container> ollama pull qwen2.5-coder:7b
```

### Option 2: Local Installation
```bash
pip install aider-chat
```

## What the Demo Does

1. Creates a sample Python project with basic functions
2. Uses LLX to analyze the project and select the best model
3. Calls Aider to add type hints automatically
4. Shows the results

### Basic Refactoring
```python
await session.call_tool('aider', {
    'prompt': 'Add type hints to all functions',
    'path': './my_project',
    'model': 'ollama/qwen2.5-coder:7b'
})
```

### With Specific Files
```python
await session.call_tool('aider', {
    'prompt': 'Convert to async/await',
    'path': '.',
    'files': ['api.py', 'database.py'],
    'model': 'ollama/qwen2.5-coder:7b'
})
```

## Tips

1. **Be Specific**: Clear prompts give better results
2. **Use File Scope**: Specify files for focused changes
3. **Iterate**: Use small, incremental changes
4. **Trust LLX**: Let LLX pick the best model automatically

## Troubleshooting

- **Docker timeouts**: Increase timeout or use local installation
- **Model not found**: Pull the model with `ollama pull`
- **Permission errors**: Check Docker volume permissions

## Integration with LLX Features

- ✅ Automatic model selection
- ✅ Code metrics analysis
- ✅ Proxy support for cloud models
- ✅ MCP tool integration
- ✅ Local and cloud model support
