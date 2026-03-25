#!/usr/bin/env bash
# llx Local Models Example Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 llx Local Models Example Runner${NC}"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found. Please run from examples/local directory${NC}"
    exit 1
fi

# Check if llx is installed
LLX_PATH="$(dirname "$PWD")/.."
if [ ! -d "$LLX_PATH/.venv" ]; then
    echo -e "${RED}❌ Error: Virtual environment not found at $LLX_PATH/.venv${NC}"
    echo "Please install llx first:"
    echo "  cd $LLX_PATH"
    echo "  python -m venv .venv"
    echo "  .venv/bin/pip install -e ."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found. Creating from parent...${NC}"
    cp "$LLX_PATH/.env" .env
    echo "✓ Created .env from parent directory"
fi

# Check for Ollama installation
echo -e "${BLUE}🔍 Checking Ollama installation...${NC}"

if command -v ollama >/dev/null 2>&1; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ Ollama installed: $OLLAMA_VERSION${NC}"
else
    echo -e "${RED}❌ Ollama not found${NC}"
    echo ""
    echo -e "${YELLOW}💡 Install Ollama first:${NC}"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  # Or visit: https://ollama.ai/download"
    echo ""
    echo "After installation:"
    echo "  1. Start Ollama: ollama serve"
    echo "  2. Download a model: ollama pull qwen2.5-coder:7b"
    echo "  3. Run this example again"
    exit 1
fi

# Check if Ollama service is running
echo -e "${BLUE}🔍 Checking Ollama service...${NC}"

if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama service is running${NC}"
    
    # List available models
    MODELS_JSON=$(curl -s http://localhost:11434/api/tags 2>/dev/null || echo '{"models":[]}')
    MODEL_COUNT=$(echo "$MODELS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('models', [])))" 2>/dev/null || echo "0")
    
    if [ "$MODEL_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Found $MODEL_COUNT local model(s)${NC}"
        
        # Show first few models
        echo -e "${BLUE}📋 Available models:${NC}"
        echo "$MODELS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, model in enumerate(data.get('models', [])[:3]):
    name = model.get('name', 'Unknown')
    size = model.get('size', 0)
    size_gb = size / (1024**3) if size else 0
    print(f'   • {name} ({size_gb:.1f}GB)')
" 2>/dev/null || echo "   • Could not parse model list"
    else
        echo -e "${YELLOW}⚠️  No models downloaded yet${NC}"
        echo ""
        echo -e "${BLUE}💡 Download a recommended model:${NC}"
        echo "  ollama pull qwen2.5-coder:7b      # For coding tasks"
        echo "  ollama pull llama3.1:8b           # General purpose"
        echo "  ollama pull mistral:7b            # Fast and efficient"
    fi
else
    echo -e "${YELLOW}⚠️  Ollama service not running${NC}"
    echo ""
    echo -e "${BLUE}💡 Start Ollama service:${NC}"
    echo "  ollama serve"
    echo ""
    echo "Then run this example again to see local models in action."
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -e "${BLUE}📋 Loading environment variables...${NC}"
    set -a
    source .env 2>/dev/null || true
    set +a
    echo "✓ Environment loaded"
fi

# Check for optional dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

PYTHON="$LLX_PATH/.venv/bin/python"

# Check for requests
if ! $PYTHON -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing requests...${NC}"
    $PYTHON -m pip install requests
fi

# Run the example
echo -e "${BLUE}🏃 Running local models example...${NC}"
echo ""

# Set PYTHONPATH to include llx
export PYTHONPATH="$LLX_PATH:$PYTHONPATH"

# Run the example
"$PYTHON" main.py "$@"

echo ""
echo -e "${GREEN}✅ Example completed!${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  • Download a model: ollama pull qwen2.5-coder:7b"
echo "  • Test local model: ollama run qwen2.5-coder:7b"
echo "  • Try with --local flag: cd $LLX_PATH && .venv/bin/python -m llx analyze . --local"
echo "  • Configure local models in llx.toml for specific projects"
