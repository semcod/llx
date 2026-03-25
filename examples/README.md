# llx Examples

This directory contains practical examples of using llx with different LLM providers and configurations.

## Available Examples

### 1. Basic Usage (`basic/`)
- **main.py**: Simple project analysis and model selection
- **run.sh**: Execution script with environment setup
- **README.md**: Detailed explanation and usage instructions

### 2. Proxy Integration (`proxy/`)
- **main.py**: LiteLLM proxy server setup
- **run.sh**: Proxy server startup script
- **README.md**: Proxy configuration and IDE integration

### 3. Multi-Provider (`multi-provider/`)
- **main.py**: Using multiple LLM providers with fallback
- **run.sh**: Multi-provider testing script
- **README.md**: Provider configuration and cost optimization

### 4. Local Models (`local/`)
- **main.py**: Local model integration with Ollama
- **run.sh**: Local model setup and testing
- **README.md**: Local model configuration and usage

## Environment Setup

1. Copy the main `.env` file to the example directory:
   ```bash
   cp ../.env .env
   ```

2. Ensure your API keys are properly configured in `.env`:
   - `ANTHROPIC_API_KEY` for Claude models
   - `OPENROUTER_API_KEY` for OpenRouter models
   - `OPENAI_API_KEY` for OpenAI models
   - `GOOGLE_AI_KEY` for Gemini models

3. Install dependencies:
   ```bash
   cd /home/tom/github/semcod/llx
   .venv/bin/pip install -e .
   ```

## Running Examples

Each example can be run independently:
```bash
cd examples/basic
./run.sh
```

Or using Python directly:
```bash
cd examples/basic
python main.py
```

## Security Notes

- Keep your API keys secure and never commit them to version control
- Use environment variables for sensitive configuration
- Consider using a secrets management system for production deployments
