#!/bin/bash
# LLX Simple Strategy Generator - Quick Start Script

echo "🚀 LLX Strategy Generator"
echo "========================="
echo ""

# Check if Ollama is available for local models
if command -v ollama &> /dev/null; then
    echo "✓ Ollama found - local models available"
else
    echo "⚠ Ollama not found - install for local models:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
fi

# Check for OpenRouter API key
if [ -f ".env" ] && grep -q "OPENROUTER_API_KEY" .env; then
    echo "✓ OpenRouter API key found"
else
    echo "⚠ No OpenRouter API key - add to .env file for cloud models:"
    echo "   echo 'OPENROUTER_API_KEY=sk-or-v1-xxxxx' >> .env"
    echo ""
fi

# Run the generator
echo "Generating strategy..."
python3 simple_generate.py "$@"
