# llx Orchestration System

Advanced multi-instance LLM and VS Code orchestration with intelligent routing, rate limiting, and session management.

## 🎯 Overview

The llx Orchestration System provides comprehensive management of multiple LLM providers, VS Code instances, and AI tools with intelligent routing, load balancing, and resource optimization.

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    llx Orchestration System                │
├─────────────────────────────────────────────────────────────┤
│  🧭 Routing Engine      │  📋 Queue Manager   │  ⏱️ Rate Limiter │
│  🤖 LLM Orchestrator    │  🏗️ Instance Mgr  │  👥 Session Mgr  │
│  📝 VS Code Orchestrator│                    │                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Resources & Providers                │
├─────────────────────────────────────────────────────────────┤
│  🤖 LLM Providers (OpenAI, Anthropic, Ollama, etc.)     │
│  📝 VS Code Instances (Multiple accounts, ports)          │
│  🛠️  AI Tools (Aider, Claude Code, Cursor)                │
│  🐳 Docker Containers                                   │
└─────────────────────────────────────────────────────────────┘
```

# Or install orchestrator only
pip install llx[orchestration]
```

# Start orchestration system
llx-orchestrator start

# Check system status
llx-orchestrator status

# Route LLM request
llx-orchestrator route llm "Hello, world!"

# Start VS Code instance
llx-orchestrator vscode start-instance --instance-id dev-1

# Complete LLM request
llx-orchestrator llm complete --prompt "Write a Python function"

# Monitor system
llx-orchestrator monitor --interval 30 --duration 300
```

## 🧭 Routing Engine

The routing engine intelligently routes requests to optimal resources based on availability, performance, cost, and user preferences.

### Routing Strategies

- **Availability First**: Prioritizes available resources
- **Least Loaded**: Routes to least utilized resources
- **Priority Based**: Routes based on request priority
- **Cost Optimized**: Routes to cheapest available option
- **Performance Optimized**: Routes to highest performing option
- **Round Robin**: Distributes load evenly

# Route with specific strategy
llx-orchestrator route llm "Hello" --strategy cost_optimized

# Route with priority
llx-orchestrator route llm "Urgent task" --priority urgent

# Route to specific provider
llx-orchestrator route llm "Code generation" --provider ollama
```

## 🤖 LLM Orchestrator

Manages multiple LLM providers and models with automatic failover, load balancing, and cost optimization.

### Supported Providers

- **OpenAI**: GPT models
- **Anthropic**: Claude models
- **Google**: Gemini models
- **OpenRouter**: Multiple providers via single API
- **Ollama**: Local models
- **Custom**: OpenAI-compatible APIs

# List available providers
llx-orchestrator llm list-providers

# List available models
llx-orchestrator llm list-models

# Filter by capability
llx-orchestrator llm list-models --capability code_generation

# Get model details
llx-orchestrator llm model-info --model-id qwen2.5-coder:7b
```

# Simple completion
llx-orchestrator llm complete --prompt "Write a Python function"

# With specific model
llx-orchestrator llm complete --provider ollama --model qwen2.5-coder:7b --prompt "Debug this code"

# With parameters
llx-orchestrator llm complete --prompt "Explain this" --temperature 0.2 --max-tokens 500
```

## 📝 VS Code Orchestrator

Manages multiple VS Code instances with different accounts, ports, and configurations.

### Account Types

- **Local**: Local development instances
- **GitHub**: GitHub Copilot integration
- **Microsoft**: Microsoft accounts
- **Windsurf**: Windsurf browser-based VS Code
- **Cursor**: Cursor AI integration
- **Codeium**: Codeium AI integration

# Add VS Code account
llx-orchestrator vscode add-account \
  --account-id my-github \
  --name "GitHub Account" \
  --type github \
  --email user@example.com \
  --auth-method browser

# List accounts
llx-orchestrator vscode list-accounts

# Start instance
llx-orchestrator vscode start-instance \
  --instance-id dev-1 \
  --account-id my-github \
  --workspace ./my-project
```

# List instances
llx-orchestrator vscode list-instances

# List active sessions
llx-orchestrator vscode list-sessions

# Stop instance
llx-orchestrator vscode stop-instance --instance-id dev-1
```

## 📋 Queue Manager

Manages request queuing with intelligent prioritization and load distribution.

### Queue Features

- **Priority-based queuing**: Urgent, High, Normal, Low, Background
- **Automatic retry**: Exponential backoff retry logic
- **Load balancing**: Distribute requests across available resources
- **Timeout handling**: Automatic request timeout management

# Show queue status
llx-orchestrator queue status

# Show queue metrics
llx-orchestrator queue metrics

# Get specific queue metrics
llx-orchestrator queue metrics --queue-id ollama-default
```

## ⏱️ Rate Limiter

Manages rate limiting and cooldown periods for all providers and accounts.

### Rate Limit Types

- **Requests per hour**: Hourly request limits
- **Tokens per hour**: Hourly token limits
- **Requests per minute**: Minute-level request limits
- **Concurrent requests**: Simultaneous request limits

# Show rate limit status
llx-orchestrator rate-limit status

# Show available providers
llx-orchestrator rate-limit available --type requests_per_hour

# Check specific provider
python -m llx.orchestration.rate_limiter check --provider ollama --account default
```

## 👥 Session Manager

Manages active sessions for LLM providers, VS Code instances, and AI tools.

### Session Types

- **LLM Sessions**: Active LLM provider sessions
- **VS Code Sessions**: Active VS Code user sessions
- **AI Tools Sessions**: Active AI tool sessions

# List all sessions
llx-orchestrator session list

# Filter by type
llx-orchestrator session list --type llm

# Filter by status
llx-orchestrator session list --status active

# Create session
llx-orchestrator session create \
  --session-id my-session \
  --type llm \
  --provider ollama \
  --model qwen2.5-coder:7b
```

## 🏗️ Instance Manager

Manages Docker instances for VS Code, AI tools, and LLM proxy services.

### Instance Types

- **VS Code**: VS Code server instances
- **AI Tools**: AI tools container instances
- **LLM Proxy**: LiteLLM proxy instances

# List all instances
llx-orchestrator instance list

# Filter by type
llx-orchestrator instance list --type vscode

# Filter by status
llx-orchestrator instance list --status running

# Create instance
llx-orchestrator instance create \
  --instance-id vscode-dev-1 \
  --type vscode \
  --account my-account \
  --port 8080
```

## 🔧 Configuration

All components use JSON configuration files stored in `orchestration/` directory:

- `sessions.json` - Session configurations and state
- `instances.json` - Instance configurations and state
- `rate_limits.json` - Rate limit configurations
- `queues.json` - Queue configurations
- `routing.json` - Routing engine configuration
- `vscode.json` - VS Code orchestration configuration
- `llm.json` - LLM provider and model configurations

# Show all configurations
llx-orchestrator config show

# Show specific component
llx-orchestrator config show --component vscode

# Save all configurations
llx-orchestrator config save

# Load all configurations
llx-orchestrator config load
```

# Comprehensive health check
llx-orchestrator health

# Real-time monitoring
llx-orchestrator monitor --interval 30 --duration 300
```

# Usage statistics
llx-orchestrator llm usage

# Routing performance
llx-orchestrator routing status

# Queue metrics
llx-orchestrator queue metrics
```

# Run system diagnostics
llx-orchestrator utils doctor

# Performance benchmarks
llx-orchestrator utils benchmark --component all --iterations 1000
```

# Create multiple VS Code accounts
llx-orchestrator vscode add-account --account-id personal --type local --name "Personal Dev"
llx-orchestrator vscode add-account --account-id work --type github --name "Work Account"

# Start instances with different accounts
llx-orchestrator vscode start-instance --instance-id personal-dev --account-id personal
llx-orchestrator vscode start-instance --instance-id work-dev --account-id work
```

# Route to cheapest available provider
llx-orchestrator route llm "Generate code" --strategy cost_optimized

# Check cost-effective models
llx-orchestrator llm list-models | grep "cost_per_1k_input"
```

# Route to fastest available provider
llx-orchestrator route llm "Urgent task" --strategy performance_optimized --priority urgent

# Monitor routing performance
llx-orchestrator routing status
```

# Check available providers when rate limited
llx-orchestrator rate-limit available

# Monitor rate limit status
llx-orchestrator rate-limit status
```

# Start multiple instances
for i in {1..3}; do
  llx-orchestrator vscode start-instance --instance-id dev-$i --account-id my-account
done

# Route with least loaded strategy
llx-orchestrator route vscode "Open project" --strategy least_loaded
```

# Configure multiple LLM providers
python -c "
from llx.orchestration.llm_orchestrator import LLMOrchestrator

orchestrator = LLMOrchestrator()

# Add OpenAI provider
openai_provider = LLMProvider(
    provider_id='openai-gpt4',
    provider_type=LLMProviderType.OPENAI,
    name='OpenAI GPT-4',
    api_base='https://api.openai.com/v1',
    auth_method='api_key',
    auth_config={'api_key': 'your-api-key'}
)
orchestrator.add_provider(openai_provider)

# Add Anthropic provider
anthropic_provider = LLMProvider(
    provider_id='anthropic-claude',
    provider_type=LLMProviderType.ANTHROPIC,
    name='Anthropic Claude',
    api_base='https://api.anthropic.com/v1',
    auth_method='api_key',
    auth_config={'api_key': 'your-api-key'}
)
orchestrator.add_provider(anthropic_provider)
"
```

### Custom Routing Logic

```python
from llx.orchestration.routing_engine import RoutingEngine, ResourceType, RoutingRequest

engine = RoutingEngine()

# Create custom routing request
request = RoutingRequest(
    request_id='custom-request',
    resource_type=ResourceType.LLM,
    strategy=RoutingStrategy.COST_OPTIMIZED,
    constraints={'max_cost': 0.01, 'max_wait_time': 10}
)

# Route request
decision = engine.route_request(request)
print(f"Routed to: {decision.selected_resource}")
```

# Monitor and auto-scale based on queue length
while true; do
  queue_length=$(llx-orchestrator queue status | jq '.queue_length')
  
  if [ $queue_length -gt 10 ]; then
    echo "High queue length: $queue_length, starting new instance"
    llx-orchestrator vscode start-instance --instance-id auto-$(date +%s)
  fi
  
  sleep 60
done
```

### Adding New Providers

```python
from llx.orchestration.llm_orchestrator import LLMProvider, LLMProviderType

# Create custom provider
custom_provider = LLMProvider(
    provider_id='custom-provider',
    provider_type=LLMProviderType.CUSTOM,
    name='Custom LLM Provider',
    api_base='https://api.custom.com/v1',
    auth_method='api_key',
    auth_config={'api_key': 'your-api-key'},
    rate_limits={'requests_per_hour': 1000}
)

# Add to orchestrator
orchestrator.add_provider(custom_provider)
```

### Custom Routing Strategies

```python
from llx.orchestration.routing_engine import RoutingEngine

class CustomRoutingStrategy:
    def route(self, candidates, request):
        # Custom routing logic
        return best_candidate

# Register custom strategy
engine = RoutingEngine()
engine.register_strategy('custom', CustomRoutingStrategy())
```

### Common Issues

**Provider Not Available:**
```bash
# Check provider status
llx-orchestrator llm list-providers

# Check rate limits
llx-orchestrator rate-limit status

# Check health
llx-orchestrator health
```

**VS Code Instance Not Starting:**
```bash
# Check instance status
llx-orchestrator vscode list-instances

# Check Docker status
docker ps | grep vscode

# View logs
docker logs llx-vscode-dev-1
```

**Routing Failures:**
```bash
# Check routing status
llx-orchestrator routing status

# Check available resources
llx-orchestrator status

# Run diagnostics
llx-orchestrator utils doctor
```

# Enable debug logging
export DEBUG=true
export LLX_LOG_LEVEL=DEBUG

# Run with verbose output
llx-orchestrator --verbose start
```

### Core Components

- **SessionManager**: Manages LLM, VS Code, and AI tool sessions
- **InstanceManager**: Manages Docker instances
- **RateLimiter**: Manages rate limiting and cooldowns
- **QueueManager**: Manages request queuing
- **RoutingEngine**: Intelligent request routing
- **VSCodeOrchestrator**: VS Code-specific orchestration
- **LLMOrchestrator**: LLM-specific orchestration

# System management
llx-orchestrator start|stop|restart|status|health|monitor

# VS Code management
llx-orchestrator vscode [start|stop|list|add-account]

# LLM management
llx-orchestrator llm [list-providers|list-models|complete]

# Routing
llx-orchestrator route [llm|vscode|ai_tools] "request"

# Queue management
llx-orchestrator queue [status|metrics]

# Rate limiting
llx-orchestrator rate-limit [status|available]

# Session management
llx-orchestrator session [list|create]

# Instance management
llx-orchestrator instance [list|create]

# Configuration
llx-orchestrator config [show|save|load]

# Utilities
llx-orchestrator utils [cleanup|reset|doctor|benchmark]
```

### 1. Resource Management

- Monitor resource utilization regularly
- Set appropriate rate limits
- Use cost-optimized routing for non-critical tasks
- Implement proper error handling and retry logic

### 2. Security

- Use secure authentication methods
- Rotate API keys regularly
- Implement proper access controls
- Monitor for unusual usage patterns

### 3. Performance

- Use appropriate routing strategies
- Monitor queue lengths and wait times
- Implement caching where appropriate
- Use connection pooling for API calls

### 4. Reliability

- Implement proper health checks
- Use automatic failover
- Monitor and alert on failures
- Maintain backup configurations

---

**🚀 The llx Orchestration System provides comprehensive management of multi-instance LLM and VS Code environments with intelligent routing and resource optimization!**
