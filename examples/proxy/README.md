# llx Proxy Integration Example

This example demonstrates how to set up and use the llx LiteLLM proxy server for IDE integration and multi-provider access.

## What it does

1. **Proxy Server Setup**: Configures a LiteLLM proxy server with model routing
2. **Model Aliases**: Sets up convenient aliases (cheap, balanced, premium, free)
3. **IDE Integration**: Shows how to connect VS Code extensions and terminal tools
4. **Semantic Caching**: Demonstrates caching for cost and performance optimization
5. **Cost Tracking**: Monitors API usage across all connected tools

## Architecture

```
IDE/Tool → llx Proxy (localhost:4001) → Multiple LLM Providers
                                   ├─ Anthropic Claude
                                   ├─ OpenRouter (300+ models)  
                                   ├─ OpenAI GPT
                                   ├─ Google Gemini
                                   └─ Local Models (Ollama)
```

## Prerequisites

- llx installed in development mode
- At least one LLM provider API key configured
- Port 4001 available (or modify in script)

## Setup

1. **Copy environment configuration:**
   ```bash
   cp ../../.env .env
   ```

2. **Configure API keys** (edit `.env`):
   ```bash
   # Required for proxy functionality
   ANTHROPIC_API_KEY=sk-ant-api03-...
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENAI_API_KEY=sk-...
   
   # Proxy configuration
   AI_PROXY_HOST=0.0.0.0
   AI_PROXY_PORT=4001
   AI_PROXY_MASTER_KEY=sk-proxy-local-dev
   ```

3. **Install dependencies:**
   ```bash
   cd ../../
   .venv/bin/pip install litellm
   ```

## Running the Proxy

### Quick Start
```bash
./run.sh
```

The proxy will start and run until you stop it with Ctrl+C.

### Manual Execution
```bash
# Set environment variables
export $(grep -v '^#' .env | xargs)

# Start the proxy
../../.venv/bin/python main.py
```

## IDE Integration

### VS Code Extensions

**Roo Code:**
1. Install Roo Code extension
2. Set API endpoint: `http://localhost:4001`
3. Set API key: `sk-proxy-local-dev`
4. Use model aliases: `cheap`, `balanced`, `premium`, `free`

**Cline:**
1. Install Cline extension  
2. Set OpenAI API Base URL: `http://localhost:4001`
3. Set API key: `sk-proxy-local-dev`

**Continue.dev:**
1. Install Continue.dev extension
2. Set API base URL: `http://localhost:4001`
3. Set API key: `sk-proxy-local-dev`

### Terminal Tools

**Aider:**
```bash
export OPENAI_API_BASE=http://localhost:4001
export OPENAI_API_KEY=sk-proxy-local-dev
aider
```

**Claude Code:**
```bash
export ANTHROPIC_BASE_URL=http://localhost:4001
claude-code
```

## Model Aliases

The proxy provides convenient aliases that map to optimal models:

- **`cheap`** → Fast, inexpensive models for simple tasks
- **`balanced`** → Good performance-to-cost ratio for general work
- **`premium`** → High-quality models for complex tasks
- **`free`** → Free-tier models for testing and learning

Configure aliases in `.env`:
```bash
PROXYM_ALIAS_CHEAP=openrouter/nvidia/nemotron-3-nano-30b-a3b:free
PROXYM_ALIAS_BALANCED=openrouter/mistralai/mistral-7b-instruct-v0.1
PROXYM_ALIAS_PREMIUM=openrouter/anthropic/claude-3.5-sonnet
PROXYM_ALIAS_FREE=openrouter/nvidia/nemotron-3-nano-30b-a3b:free
```

## Testing the Proxy

### Test Models Endpoint
```bash
curl -H "Authorization: Bearer sk-proxy-local-dev" \
     http://localhost:4001/v1/models
```

### Test Chat Completion
```bash
curl -H "Authorization: Bearer sk-proxy-local-dev" \
     -H "Content-Type: application/json" \
     -d '{"model":"cheap","messages":[{"role":"user","content":"Hello!"}]}' \
     http://localhost:4001/v1/chat/completions
```

## Features

### 1. Intelligent Routing
The proxy automatically routes requests to the best provider based on:
- Model availability
- Rate limits
- Cost optimization
- Performance metrics

### 2. Cost Tracking
Monitor usage across all connected tools:
- Per-request cost tracking
- Daily/monthly budget limits
- Provider-specific cost breakdown

### 3. Semantic Caching
Reduce costs and improve performance:
- Automatic response caching
- Semantic similarity matching
- Configurable cache duration

### 4. Load Balancing
Distribute load across providers:
- Automatic failover
- Rate limit handling
- Provider health monitoring

## Configuration Options

### Proxy Settings
```bash
AI_PROXY_HOST=0.0.0.0          # Listen address
AI_PROXY_PORT=4001             # Port number
AI_PROXY_MASTER_KEY=sk-proxy-local-dev  # Master API key
AI_PROXY_LOG_LEVEL=info        # Logging level
```

### Budget Limits
```bash
MONTHLY_BUDGET_USD=60          # Monthly budget cap
DAILY_BUDGET_USD=5             # Daily budget cap  
MAX_REQUEST_COST_USD=2.0       # Per-request limit
```

### Caching
```bash
REDIS_URL=redis://localhost:6379/0  # Redis for caching
# Without Redis, in-memory caching is used
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
netstat -tuln | grep :4001

# Use a different port
export AI_PROXY_PORT=4002
./run.sh
```

### API Key Issues
```bash
# Verify keys are loaded
env | grep API_KEY

# Test provider directly
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages
```

### Connection Refused
```bash
# Check if proxy is running
curl http://localhost:4001/health

# Check logs for errors
# The script outputs connection status during startup
```

## Security Notes

- The proxy API key provides access to all configured providers
- Use firewall rules to restrict access to the proxy port
- Consider using HTTPS in production environments
- Rotate API keys regularly
- Monitor usage for unusual activity

## Production Deployment

For production use:

1. **Use HTTPS:**
   ```bash
   # Configure SSL certificates
   AI_PROXY_SSL_CERT=/path/to/cert.pem
   AI_PROXY_SSL_KEY=/path/to/key.pem
   ```

2. **Set up Redis:**
   ```bash
   # Install and start Redis
   sudo apt-get install redis-server
   sudo systemctl start redis
   
   # Configure in .env
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Configure Monitoring:**
   ```bash
   # Enable health checks
   AI_PROXY_HEALTH_CHECK=true
   
   # Set up metrics collection
   AI_PROXY_METRICS_ENABLED=true
   ```

## Next Steps

- Try the [Multi-Provider Example](../multi-provider/) for advanced provider management
- Explore the [Local Models Example](../local/) for offline usage
- Check the [Basic Example](../basic/) for core llx functionality
- Read the main [llx Documentation](../../README.md)
