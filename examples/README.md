# llx Examples

This directory contains practical examples of using llx with different LLM providers, proxy setups, Docker integrations, and local coding workflows.

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

### 5. Docker Integration (`docker/`)
- **main.py**: Docker service orchestration and monitoring
- **run.sh**: Docker environment runner
- **README.md**: Docker configuration and workflows

### 6. AI Tools Integration (`ai-tools/`)
- **main.py**: Shell-based AI tools integration through llx
- **README.md**: Aider, Claude Code, and Cursor setup

### 7. VS Code + RooCode (`vscode-roocode/`)
- **demo.py**: RooCode demo and workflow walkthrough
- **README.md**: VS Code / RooCode integration guide

## Environment Setup

1. Copy the main `.env` file to the example directory you want to run:
   ```bash
   cp ../.env basic/.env   # replace `basic` with the example you want
   ```

2. Ensure your API keys are properly configured in `.env`:
   - `ANTHROPIC_API_KEY` for Claude models
   - `OPENROUTER_API_KEY` for OpenRouter models
   - `OPENAI_API_KEY` for OpenAI models
   - `GEMINI_API_KEY` for Gemini models

   For proxy-based examples, also ensure these are available:
   - `LLX_PROXY_HOST` for the proxy listen address
   - `LLX_PROXY_PORT` for the proxy port
   - `LLX_PROXY_MASTER_KEY` for OpenAI-compatible clients

3. Install dependencies:
   ```bash
   cd /home/tom/github/semcod/llx
   .venv/bin/pip install -e .
   ```

## Running Examples

Each example can be run independently from the repository root:
```bash
cd examples/basic
./run.sh
```

Or using Python directly:
```bash
cd examples/basic
../../.venv/bin/python main.py
```

## Security Notes

- Keep your API keys secure and never commit them to version control
- Use environment variables for sensitive configuration
- Consider using a secrets management system for production deployments
