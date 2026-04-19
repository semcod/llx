# Generate strategy (automatically picks best available model)
python simple_generate.py

# Specify output file
python simple_generate.py -o my-strategy.yaml

# Generate for specific project
python simple_generate.py /path/to/project
```

## How it works

1. **No complex configuration needed** - just run the script
2. **Automatic model selection**:
   - First tries OpenRouter free model (if API key exists)
   - Falls back to local Ollama model
3. **Simple output** - clean YAML strategy file

## Environment Setup (optional)

Create `.env` file for OpenRouter:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

Or use local models with Ollama:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull qwen2.5-coder:7b
```

That's it! No complex config files needed.
