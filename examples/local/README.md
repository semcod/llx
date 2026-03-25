# llx Local Models Example

This example demonstrates how to use llx with local LLM models via Ollama for privacy, offline capability, and zero API costs.

## What it does

1. **Ollama Setup**: Checks Ollama installation and service status
2. **Model Management**: Lists and manages local models
3. **Resource Analysis**: Estimates hardware requirements
4. **Local Selection**: Demonstrates local model integration with llx
5. **Performance Guidance**: Provides optimization tips

## Why Use Local Models?

| Benefit | Description |
|---------|-------------|
| **Privacy** | Code never leaves your machine |
| **Zero Cost** | No API fees or per-token charges |
| **Offline** | Works without internet connection |
| **Speed** | No network latency, local processing |
| **Control** | Full control over models and data |

## Prerequisites

- llx installed in development mode
- Ollama installed and running
- Sufficient RAM/VRAM for model sizes

## Setup

### 1. Install Ollama

**Linux/macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai/download

**Manual Installation:**
```bash
# Or download binary directly
curl -L https://ollama.ai/download/ollama-linux-amd64 -o ollama
chmod +x ollama
sudo mv ollama /usr/local/bin/
```

### 2. Start Ollama Service
```bash
ollama serve
# Runs on http://localhost:11434
```

### 3. Download Models
```bash
# Coding models
ollama pull qwen2.5-coder:7b      # Code specialization
ollama pull codellama:7b           # Meta's code model
ollama pull deepseek-coder:6.7b    # Strong coding performance

# General models  
ollama pull llama3.1:8b           # Well-balanced
ollama pull mistral:7b            # Fast and efficient

# Large models (if you have resources)
ollama pull llama3.1:70b          # High performance
```

## Running the Example

### Quick Start
```bash
./run.sh
```

### Manual Execution
```bash
# Set environment variables
export OLLAMA_BASE_URL=http://localhost:11434

# Run the example
../../.venv/bin/python main.py
```

## Expected Output

```
🚀 llx Local Models Example
==================================================

🔍 Checking Ollama installation...
   ✓ Ollama installed: ollama version is 0.9.0

🔍 Checking Ollama service...
   ✓ Ollama service running with 3 models
     • qwen2.5-coder:7b (4.7GB)
     • llama3.1:8b (4.7GB)
     • mistral:7b (4.1GB)

🎯 Recommended Local Models
========================================

🔷 Coding models:
   • qwen2.5-coder:7b
     Specialized for code generation and debugging
     Size: 4.7GB, Context: 32K
     Strengths: Code completion, Debugging, Code explanation

🎯 Local Model Selection Demo
========================================
📊 Project Analysis:
   Files: 26, Lines: 3,502, Complexity: 0.0
✓ Recommended model: ollama/qwen2.5-coder:7b
   Provider: ollama
   Tier: local
   🏠 Local model selected - Zero API costs!
   ✓ Privacy: Code never leaves your machine
   ✓ Offline: Works without internet connection

✅ Local models example completed!
```

## Recommended Models

### Coding Models

| Model | Size | Context | Strengths | Hardware |
|-------|------|---------|-----------|----------|
| **qwen2.5-coder:7b** | 4.7GB | 32K | Code completion, debugging | 8GB RAM, 6GB VRAM |
| **codellama:7b** | 3.8GB | 4K | Code generation, documentation | 8GB RAM, 5GB VRAM |
| **deepseek-coder:6.7b** | 3.8GB | 4K | Algorithm design, problem solving | 8GB RAM, 5GB VRAM |

### General Models

| Model | Size | Context | Strengths | Hardware |
|-------|------|---------|-----------|----------|
| **llama3.1:8b** | 4.7GB | 128K | General chat, analysis | 8GB RAM, 6GB VRAM |
| **mistral:7b** | 4.1GB | 32K | Speed, low resource usage | 8GB RAM, 5GB VRAM |
| **llama3.2:3b** | 1.9GB | 128K | Lightweight, fast | 4GB RAM, 2GB VRAM |

### Large Models (Advanced)

| Model | Size | Context | Strengths | Hardware |
|-------|------|---------|-----------|----------|
| **llama3.1:70b** | 40GB | 128K | Complex reasoning, architecture | 64GB RAM, 40GB VRAM |
| **qwen2.5-coder:32b** | 19GB | 32K | Advanced coding tasks | 32GB RAM, 24GB VRAM |

## Hardware Requirements

### Minimum Requirements (7B Models)
- **RAM**: 8GB
- **VRAM**: 5-6GB (GPU acceleration)
- **Storage**: 5GB per model
- **CPU**: 4+ cores
- **OS**: Linux/macOS/Windows

### Recommended Setup (13B+ Models)
- **RAM**: 16-32GB
- **VRAM**: 8-16GB (GPU acceleration)
- **Storage**: 20GB+ for multiple models
- **CPU**: 8+ cores
- **GPU**: CUDA/Metal compatible

### Performance Optimization

**GPU Acceleration:**
```bash
# Check if GPU is available
ollama list

# GPU should be detected automatically
# Force GPU usage if needed
CUDA_VISIBLE_DEVICES=0 ollama serve
```

**Memory Optimization:**
```bash
# Reduce context window for memory efficiency
ollama run llama3.1:8b --context 4096

# Use quantized models for lower memory
ollama pull llama3.1:8b-q4_0  # 4-bit quantization
```

## Configuration

### Environment Variables
```bash
# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=/usr/share/ollama/.ollama/models

# llx configuration for local models
LLX_LOCAL_MODELS=true
LLX_LOCAL_MODEL_PATH=/path/to/ollama/models
```

### llx Configuration
```toml
# llx.toml
[local_models]
enabled = true
base_url = "http://localhost:11434"
default_model = "qwen2.5-coder:7b"
timeout = 30

[local_models.aliases]
coder = "qwen2.5-coder:7b"
general = "llama3.1:8b"
fast = "mistral:7b"
```

## Using Local Models with llx

### Command Line
```bash
# Force local model selection
../../.venv/bin/python -m llx analyze . --local

# Specify local model
../../.venv/bin/python -m llx analyze . --model ollama/qwen2.5-coder:7b

# Chat with local model
../../.venv/bin/python -m llx chat "Explain this code" --local
```

### Python API
```python
from llx import analyze_project, select_model, LlxConfig

# Configure for local models
config = LlxConfig.load()
config.local_models.enabled = True
config.local_models.base_url = "http://localhost:11434"

# Analyze and select local model
metrics = analyze_project(".")
selection = select_model(metrics, config=config, local_only=True)
```

## Model Management

### List Models
```bash
ollama list
# Shows downloaded models with sizes

# Detailed information
ollama show qwen2.5-coder:7b
```

### Remove Models
```bash
ollama rm llama3.1:8b
# Frees up disk space
```

### Update Models
```bash
ollama pull qwen2.5-coder:7b
# Downloads latest version if available
```

### Model Information
```bash
# Check model details
ollama show --modelfile qwen2.5-coder:7b

# Test model interactively
ollama run qwen2.5-coder:7b
```

## Performance Tips

### Speed Optimization
1. **Use GPU acceleration** when available
2. **Choose appropriate model size** for your hardware
3. **Reduce context window** for faster responses
4. **Use quantized models** for lower memory usage

### Quality Optimization
1. **Use coding-specific models** for code tasks
2. **Larger models** for complex reasoning
3. **Appropriate temperature** settings
4. **Good prompting techniques**

### Resource Management
1. **Monitor RAM/VRAM usage**
2. **Stop unused models** to free memory
3. **Use SSD storage** for faster model loading
4. **Limit concurrent requests**

## Troubleshooting

### Common Issues

**Ollama Service Not Running:**
```bash
# Start Ollama service
ollama serve

# Check if running
ps aux | grep ollama

# Test connection
curl http://localhost:11434/api/tags
```

**Out of Memory Errors:**
```bash
# Check available memory
free -h

# Use smaller model
ollama pull llama3.2:3b

# Reduce context
ollama run llama3.1:8b --context 2048
```

**Slow Performance:**
```bash
# Check GPU usage
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# Enable GPU acceleration
CUDA_VISIBLE_DEVICES=0 ollama serve

# Use quantized model
ollama pull llama3.1:8b-q4_0
```

**Model Not Found:**
```bash
# Download model
ollama pull qwen2.5-coder:7b

# List available models
ollama list

# Check model name
ollama list | grep qwen
```

### Debug Mode
```bash
# Enable verbose logging
OLLAMA_DEBUG=1 ollama serve

# Check logs
journalctl -u ollama  # systemd
# or check terminal output
```

## Integration Examples

### VS Code Integration
```json
// .vscode/settings.json
{
    "ollama.baseURL": "http://localhost:11434",
    "ollama.model": "qwen2.5-coder:7b"
}
```

### Docker Integration
```dockerfile
FROM ollama/ollama

# Download models during build
RUN ollama pull qwen2.5-coder:7b
RUN ollama pull llama3.1:8b

EXPOSE 11434

CMD ["ollama", "serve"]
```

### API Integration
```python
import requests

def chat_with_local_model(prompt, model="qwen2.5-coder:7b"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]
```

## Production Considerations

### Security
- Local models keep data private
- No network exposure for sensitive data
- Control model versions and updates
- Audit model behavior and outputs

### Scalability
- Run multiple Ollama instances
- Load balance across instances
- Use model-specific servers
- Implement request queuing

### Monitoring
```bash
# Monitor resource usage
htop          # CPU/Memory
nvidia-smi    # GPU usage
iotop         # Disk I/O

# Monitor Ollama
curl http://localhost:11434/api/ps
```

## Next Steps

- Try the [Proxy Integration Example](../proxy/) for IDE setup
- Explore the [Multi-Provider Example](../multi-provider/) for cloud options
- Check the [Basic Example](../basic/) for core llx functionality
- Read the main [llx Documentation](../../README.md)

## Additional Resources

- [Ollama Documentation](https://ollama.ai/documentation)
- [Model Library](https://ollama.ai/library)
- [Hardware Requirements](https://ollama.ai/documentation/hardware)
- [Performance Tips](https://ollama.ai/documentation/performance)
