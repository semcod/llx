# llx Multi-Provider Example

This example demonstrates how to configure and use multiple LLM providers with llx for reliability, cost optimization, and provider-specific capabilities.

## What it does

1. **Provider Detection**: Automatically detects available API keys and providers
2. **Cost Comparison**: Compares costs across different providers and models
3. **Fallback Strategy**: Implements intelligent provider failover
4. **Load Balancing**: Distributes requests across multiple providers
5. **Provider Selection**: Chooses optimal providers based on task requirements

## Supported Providers

| Provider | Models | Cost Range | Strengths |
|----------|--------|------------|-----------|
| **Anthropic** | Claude Opus, Sonnet, Haiku | $0.0008-$0.075/1K | High quality, reliable |
| **OpenRouter** | 300+ models | $0.0005-$0.015/1K | Variety, good uptime |
| **OpenAI** | GPT-4, GPT-4o, GPT-4o-mini | $0.00015-$0.03/1K | Popular, reliable |
| **Google** | Gemini 2.5 Pro/Flash | $0.000075-$0.00375/1K | Free tier available |
| **DeepSeek** | DeepSeek Chat/Reasoning | $0.00014-$0.00219/1K | Cheapest option |
| **Groq** | Llama, Mixtral | $0.00005-$0.0008/1K | Ultra-fast inference |
| **Mistral** | Codestral, Mistral Large | $0.0003-$0.008/1K | Code specialization |

## Prerequisites

- llx installed in development mode
- API keys for at least one provider
- Internet connection for API access

## Setup

1. **Copy environment configuration:**
   ```bash
   cp ../../.env .env
   ```

2. **Configure API keys** (edit `.env`):
   ```bash
   # Add your API keys - configure as many as you have
   ANTHROPIC_API_KEY=sk-ant-api03-...
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENAI_API_KEY=sk-...
   GOOGLE_AI_KEY=...
   DEEPSEEK_API_KEY=...
   GROQ_API_KEY=...
   MISTRAL_API_KEY=...
   ```

3. **Install dependencies:**
   ```bash
   cd ../../
   .venv/bin/pip install litellm
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
🚀 llx Multi-Provider Example
==================================================

🔑 Checking available providers...
✓ Found 3 configured providers:
   • Anthropic Claude
   • OpenRouter (300+ models)
   • OpenAI GPT

💰 Provider Cost Comparison (per 1K tokens):
============================================================

🔷 Anthropic Claude:
   • claude-opus-4-20250514
     Input: $0.0150 | Output: $0.0750
   • claude-sonnet-4-20250514
     Input: $0.0030 | Output: $0.0150

🔷 OpenRouter (300+ models):
   • anthropic/claude-3.5-sonnet
     Input: $0.0030 | Output: $0.0150
   • openai/gpt-4o
     Input: $0.0025 | Output: $0.0100

🏆 Cheapest input cost: OpenRouter: meta-llama/llama-3.1-70b-instruct ($0.0005/1K)

🔄 Provider Fallback Strategy
========================================
Provider priority (for failover):
  1. Anthropic Claude - Primary - High quality, reliable
  2. OpenRouter (300+ models) - Secondary - Large model pool, good uptime
  3. OpenAI GPT - Tertiary - Reliable, widely used

✅ Multi-provider example completed!
```

## Provider Configuration

### Anthropic Claude
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...

# Available models
# claude-opus-4-20250514      # Premium, highest quality
# claude-sonnet-4-20250514    # Balanced, good performance
# claude-haiku-4-5-20251001   # Cheap, fast responses
```

### OpenRouter
```bash
OPENROUTER_API_KEY=sk-or-v1-...

# Popular models
# anthropic/claude-3.5-sonnet
# openai/gpt-4o
# meta-llama/llama-3.1-70b-instruct
# google/gemini-pro
```

### OpenAI
```bash
OPENAI_API_KEY=sk-...

# Available models
# gpt-4-turbo     # Premium
# gpt-4o          # Balanced
# gpt-4o-mini     # Cheap
```

### Google AI
```bash
GOOGLE_AI_KEY=...

# Available models
# gemini-2.5-pro  # Premium
# gemini-2.5-flash # Cheap
# gemini-1.5-pro  # Balanced
```

## Fallback Strategy

The example demonstrates a robust fallback strategy:

1. **Primary Provider**: Highest quality, most reliable (Anthropic)
2. **Secondary**: Large model pool, good uptime (OpenRouter)
3. **Tertiary**: Widely used, reliable (OpenAI)
4. **Quaternary**: Free tier available (Google)
5. **Last Resort**: Cheapest option (DeepSeek)

### Fallback Logic
```python
def select_provider_with_fallback(request):
    for provider in provider_priority:
        try:
            if is_provider_available(provider):
                return make_request(provider, request)
        except (RateLimitError, ProviderError):
            continue
    raise NoProvidersAvailableError()
```

## Cost Optimization

### Model Selection by Task Type

| Task Type | Recommended Provider | Model | Cost Strategy |
|-----------|-------------------|-------|--------------|
| **Simple Questions** | Google/DeepSeek | Gemini Flash/DeepSeek Chat | Cheapest |
| **Code Generation** | Anthropic/OpenRouter | Claude Sonnet/Codellama | Quality-focused |
| **Complex Reasoning** | Anthropic | Claude Opus | Premium quality |
| **General Chat** | OpenRouter/OpenAI | Mix of models | Balanced |
| **High Volume** | DeepSeek/Groq | DeepSeek Chat/Llama | Speed & cost |

### Budget Management

```bash
# Set budget limits in .env
MONTHLY_BUDGET_USD=60
DAILY_BUDGET_USD=5
MAX_REQUEST_COST_USD=2.0

# Provider-specific budgets
ANTHROPIC_BUDGET_USD=30
OPENROUTER_BUDGET_USD=20
OPENAI_BUDGET_USD=10
```

## Advanced Configuration

### Provider Weights
Configure provider selection probabilities:

```python
provider_weights = {
    'anthropic': 0.4,    # 40% of requests
    'openrouter': 0.3,   # 30% of requests  
    'openai': 0.2,       # 20% of requests
    'google': 0.1        # 10% of requests
}
```

### Model Aliases
Create consistent model names across providers:

```bash
# In .env or llx.toml
MODEL_ALIAS_PREMIUM=anthropic/claude-opus-4-20250514
MODEL_ALIAS_BALANCED=anthropic/claude-sonnet-4-20250514
MODEL_ALIAS_CHEAP=anthropic/claude-haiku-4-5-20251001
MODEL_ALIAS_FREE=google/gemini-2.5-flash
```

### Provider-Specific Settings
```bash
# Rate limiting
ANTHROPIC_RATE_LIMIT=50          # requests/minute
OPENROUTER_RATE_LIMIT=100
OPENAI_RATE_LIMIT=60

# Timeouts
ANTHROPIC_TIMEOUT=30             # seconds
OPENROUTER_TIMEOUT=20
OPENAI_TIMEOUT=25
```

## Performance Monitoring

### Metrics to Track
- Request success rate per provider
- Average response time
- Cost per request
- Error rates and types
- Rate limit hits

### Monitoring Setup
```python
# Track provider performance
provider_metrics = {
    'anthropic': {
        'success_rate': 0.98,
        'avg_response_time': 2.3,
        'cost_per_request': 0.015,
        'errors': ['rate_limit': 2, 'timeout': 1]
    }
}
```

## Troubleshooting

### Common Issues

**API Key Not Working:**
```bash
# Test API key directly
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages

# Check for extra spaces or characters
echo "$ANTHROPIC_API_KEY" | wc -c
```

**Rate Limiting:**
```bash
# Implement exponential backoff
import time
def retry_with_backoff(request, max_retries=3):
    for attempt in range(max_retries):
        try:
            return make_request(request)
        except RateLimitError:
            wait_time = 2 ** attempt
            time.sleep(wait_time)
```

**Provider Outage:**
```bash
# Check provider status
curl https://status.anthropic.com/
curl https://openrouter.ai/status
```

### Debug Mode
Enable verbose logging:
```bash
export LLX_DEBUG=true
./run.sh
```

## Best Practices

1. **Diversify Providers**: Use 3+ providers for reliability
2. **Set Budget Limits**: Prevent unexpected costs
3. **Monitor Performance**: Track success rates and response times
4. **Use Model Aliases**: Maintain consistency across providers
5. **Implement Caching**: Reduce costs for repeated requests
6. **Handle Failures Gracefully**: Implement proper error handling
7. **Regular Key Rotation**: Maintain security and access

## Production Considerations

### High Availability
- Configure multiple API keys per provider
- Set up health checks and automatic failover
- Use load balancing across provider instances
- Implement circuit breakers for failing providers

### Cost Control
- Set strict budget limits with alerts
- Use cheaper providers for non-critical tasks
- Implement request caching
- Monitor usage patterns and optimize

### Security
- Store API keys securely (environment variables, secret management)
- Use API key rotation
- Monitor for unusual usage patterns
- Implement access controls and audit logs

## Next Steps

- Try the [Proxy Integration Example](../proxy/) for IDE setup
- Explore the [Local Models Example](../local/) for offline usage
- Check the [Basic Example](../basic/) for core functionality
- Read the main [llx Documentation](../../README.md)
