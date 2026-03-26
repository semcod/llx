# Aider Integration with LLX

## Overview

LLX now supports Aider as an MCP tool, allowing you to use AI pair programming capabilities directly through LLX with intelligent model selection.

## Installation

### Option 1: Local Installation
```bash
pip install aider-chat
```

### Option 2: Docker (Recommended for compatibility)
```bash
# Pull the Aider Docker image
docker pull paulgauthier/aider

# Ensure Ollama is running
docker run -d -v ollama:/root/.ollama -p 11434:11434 ollama/ollama

# Pull a coding model
docker exec -it <ollama_container> ollama pull qwen2.5-coder:7b
```

## Usage

### 1. Via MCP Server

```python
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async def use_aider():
    server_params = {
        'command': 'python',
        'args': ['-m', 'llx.mcp.server']
    }
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Use aider to refactor code
            result = await session.call_tool('aider', {
                'prompt': 'Add type hints and improve error handling',
                'path': './my_project',
                'model': 'ollama/qwen2.5-coder:7b',
                'files': ['main.py', 'utils.py']
            })
            
            print(result.content[0].text)
```

### 2. Direct Python API

```python
from llx.mcp.tools import _handle_aider
import asyncio

async def refactor_code():
    result = await _handle_aider({
        'prompt': 'Convert this to use async/await patterns',
        'path': './my_project',
        'model': 'ollama/qwen2.5-coder:7b',
        'files': ['api.py']
    })
    
    if result['success']:
        print("Refactoring successful!")
        print(result['stdout'])
    else:
        print("Error:", result.get('error'))

asyncio.run(refactor_code())
```

### 3. Command Line (when aider is installed)

```bash
# LLX will automatically select the best model
llx chat --local --prompt "Use aider to add unit tests"

# Or specify model explicitly
aider --model ollama/qwen2.5-coder:7b --message "Add type hints"
```

## Configuration

Add to your `.env` or `llx.toml`:

```toml
[tools.aider]
model = "ollama/qwen2.5-coder:7b"
auto_commit = true
timeout = 300

[models.ollama]
base_url = "http://localhost:11434"
```

## Examples

### Refactoring a Python Module

```python
# Before: synchronous code
def fetch_data(url):
    response = requests.get(url)
    return response.json()

# Use aider to convert to async
await _handle_aider({
    'prompt': 'Convert to async/await with proper error handling',
    'path': '.',
    'files': ['api_client.py']
})
```

### Adding Type Hints

```python
# Ask aider to add type hints to entire project
await _handle_aider({
    'prompt': 'Add comprehensive type hints to all functions',
    'path': './src',
    'model': 'ollama/qwen2.5-coder:7b'
})
```

### Writing Tests

```python
# Generate unit tests
await _handle_aider({
    'prompt': 'Write comprehensive unit tests using pytest',
    'path': '.',
    'files': ['calculator.py'],
    'model': 'ollama/qwen2.5-coder:7b'
})
```

## Tips

1. **Model Selection**: LLX automatically selects the best model based on your codebase metrics
2. **File Scope**: Be specific about which files to modify for better results
3. **Iterative**: Use small, focused prompts for complex refactoring
4. **Context**: Provide clear context about the desired changes

## Integration with LLX Features

- **Automatic Model Selection**: Uses LLX's intelligent routing
- **Code Metrics**: Analyzes your codebase to select optimal models
- **Context Building**: Automatically includes relevant file context
- **Proxy Support**: Works with LiteLLM proxy for cloud models

## Troubleshooting

### Aider not found
```bash
pip install aider-chat
# or use Docker
```

### Docker connection issues
```bash
# Ensure Ollama is accessible from Docker
docker run --network host paulgauthier/aider --model ollama_chat/qwen2.5-coder:7b
```

### Model not available
```bash
# Check available models
ollama list

# Pull the model
ollama pull qwen2.5-coder:7b
```
