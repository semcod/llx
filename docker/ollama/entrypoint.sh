#!/bin/sh

# Ollama entrypoint script
# Downloads models on first start and starts the server

set -e

echo "🚀 Starting Ollama service..."

# Check if models are already downloaded
if [ ! -d "/root/.ollama/models/manifests/registry.ollama.ai/library" ]; then
    echo "📥 First start - downloading recommended models..."
    
    # Wait a bit for the service to be ready
    sleep 5
    
    # Download recommended models
    MODELS_TO_DOWNLOAD="qwen2.5-coder:7b llama3.1:8b mistral:7b"
    
    for model in $MODELS_TO_DOWNLOAD; do
        echo "📦 Downloading model: $model"
        ollama pull "$model" || echo "⚠️ Failed to download $model"
    done
    
    echo "✅ Model download completed"
else
    echo "✅ Models already exist, skipping download"
fi

echo "🌐 Starting Ollama server..."
exec ollama serve
