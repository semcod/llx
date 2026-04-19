# llx Proxy Integration Example

This example demonstrates how to set up and use the llx LiteLLM proxy server for IDE integration and multi-provider access.

## What it does

1. **Proxy Server Setup**: Generates a LiteLLM proxy config from the current llx project settings
2. **Model Tiers**: Exposes the llx model tiers directly (`cheap`, `balanced`, `premium`, `free`, `local`, `openrouter`)
3. **IDE Integration**: Shows how to connect VS Code extensions and terminal tools
4. **Semantic Caching**: Demonstrates caching for cost and performance optimization
5. **Cost Tracking**: Monitors API usage across all connected tools

## Architecture

```
IDE/Tool → llx Proxy (localhost:4000) → Multiple LLM Providers
                                   ├─ Anthropic Claude
                                   ├─ OpenRouter (300+ models)  
                                   ├─ OpenAI GPT
                                   ├─ Google Gemini
                                   └─ Local Models (Ollama)
```

## Prerequisites

- llx installed in development mode
- At least one LLM provider API key configured
- Port 4000 available, or set `LLX_PROXY_PORT` to override it

## Setup

1. **Copy environment configuration:**
   ```bash
   cp ../../.env .env
   ```

2. **Configure API keys** (edit `.env`):
   ```bash
   # Required for proxy functionality (configure the providers you use)
   ANTHROPIC_API_KEY=sk-ant-api03-...
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENAI_API_KEY=sk-...
   GEMINI_API_KEY=...
   
   # Proxy configuration (defaults already come from llx.yaml)
   LLX_PROXY_HOST=0.0.0.0
   LLX_PROXY_PORT=4000
   LLX_PROXY_MASTER_KEY=sk-proxy-local-dev
   ```

3. **Install dependencies:**
   ```bash
   cd ../../
   .venv/bin/pip install litellm
   ```

### Quick Start
```bash
./run.sh
```

The proxy will start and run until you stop it with Ctrl+C.

# Set environment variables
export $(grep -v '^#' .env | xargs)

# Map legacy names if your .env still uses AI_PROXY_*
export LLX_PROXY_HOST="${LLX_PROXY_HOST:-${AI_PROXY_HOST:-0.0.0.0}}"
export LLX_PROXY_PORT="${LLX_PROXY_PORT:-${AI_PROXY_PORT:-4000}}"
export LLX_PROXY_MASTER_KEY="${LLX_PROXY_MASTER_KEY:-${AI_PROXY_MASTER_KEY:-sk-proxy-local-dev}}"

# Start the proxy
../../.venv/bin/python main.py
```

### VS Code Extensions

**Roo Code:**
1. Install Roo Code extension
2. Set API endpoint: `http://localhost:4000`
3. Set API key: `sk-proxy-local-dev`
4. Use model tiers: `cheap`, `balanced`, `premium`, `free`, `local`

**Cline:**
1. Install Cline extension  
2. Set OpenAI API Base URL: `http://localhost:4000`
3. Set API key: `sk-proxy-local-dev`

**Continue.dev:**
1. Install Continue.dev extension
2. Set API base URL: `http://localhost:4000`
3. Set API key: `sk-proxy-local-dev`

### Terminal Tools

**Aider:**
```bash
export OPENAI_API_BASE=http://localhost:4000
export OPENAI_API_KEY=sk-proxy-local-dev
aider
```

**Claude Code:**
```bash
export ANTHROPIC_BASE_URL=http://localhost:4000
claude-code
```

## Model Aliases

The proxy exposes the llx tiers as model names:

- **`cheap`** → Fast, inexpensive models for simple tasks
- **`balanced`** → Good performance-to-cost ratio for general work
- **`premium`** → High-quality models for complex tasks
- **`free`** → Free-tier models for testing and learning

Additional tiers available in the current project config:

- **`local`** → Ollama-backed local models
- **`openrouter`** → Fallback pool via OpenRouter

The model list is generated from the current `llx.yaml`, so you usually do not
need to maintain a separate alias file.

### Test Models Endpoint
```bash
curl -H "Authorization: Bearer sk-proxy-local-dev" \
     http://localhost:4000/v1/models
```

### Test Chat Completion
```bash
curl -H "Authorization: Bearer sk-proxy-local-dev" \
     -H "Content-Type: application/json" \
     -d '{"model":"balanced","messages":[{"role":"user","content":"Hello!"}]}' \
     http://localhost:4000/v1/chat/completions
```

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

### Proxy Settings
```bash
LLX_PROXY_HOST=0.0.0.0         # Listen address
LLX_PROXY_PORT=4000            # Port number
LLX_PROXY_MASTER_KEY=sk-proxy-local-dev  # Master API key
LLX_VERBOSE=true               # Verbose logging
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
# Check what's using the port
netstat -tuln | grep :4000

# Use a different port
export LLX_PROXY_PORT=4002
./run.sh
```

# Test provider directly
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages
```

# Check if proxy is running
curl http://localhost:4000/health

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
   # Use your reverse proxy or upstream TLS terminator
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
   LLX_VERBOSE=true
   
   # Set up metrics collection in your proxy / observability stack
   ```

## Next Steps

- Try the [Multi-Provider Example](../multi-provider/) for advanced provider management
- Explore the [Local Models Example](../local/) for offline usage
- Check the [Basic Example](../basic/) for core llx functionality
- Read the main [llx Documentation](../../README.md)
