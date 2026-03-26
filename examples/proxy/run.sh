#!/usr/bin/env bash
# llx Proxy Example Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 llx Proxy Integration Example Runner${NC}"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found. Please run from examples/proxy directory${NC}"
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

# Check for required API keys
echo -e "${BLUE}🔑 Checking API keys...${NC}"

# Source the .env file to check keys
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
fi

# Map legacy AI_PROXY_* variables to the current llx names when needed.
export LLX_PROXY_HOST="${LLX_PROXY_HOST:-${AI_PROXY_HOST:-0.0.0.0}}"
export LLX_PROXY_PORT="${LLX_PROXY_PORT:-${AI_PROXY_PORT:-4000}}"
export LLX_PROXY_MASTER_KEY="${LLX_PROXY_MASTER_KEY:-${AI_PROXY_MASTER_KEY:-sk-proxy-local-dev}}"

# Check for at least one provider key
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ Error: No API keys found. Please configure at least one provider:${NC}"
    echo "  ANTHROPIC_API_KEY=sk-ant-api03-..."
    echo "  OPENROUTER_API_KEY=sk-or-v1-..."
    echo "  OPENAI_API_KEY=sk-..."
    echo ""
    echo "Edit .env file and add your API keys."
    exit 1
fi

# Show which providers are configured
echo -e "${BLUE}📋 Configured providers:${NC}"
[ ! -z "$ANTHROPIC_API_KEY" ] && echo "   ✓ Anthropic Claude"
[ ! -z "$OPENROUTER_API_KEY" ] && echo "   ✓ OpenRouter (300+ models)"
[ ! -z "$OPENAI_API_KEY" ] && echo "   ✓ OpenAI GPT"
[ ! -z "$GEMINI_API_KEY" ] && echo "   ✓ Google Gemini"
[ ! -z "$DEEPSEEK_API_KEY" ] && echo "   ✓ DeepSeek"

# Check proxy configuration
echo -e "${BLUE}🔧 Proxy configuration:${NC}"
PROXY_HOST=$LLX_PROXY_HOST
PROXY_PORT=$LLX_PROXY_PORT
PROXY_KEY=$LLX_PROXY_MASTER_KEY

echo "   ✓ Host: $PROXY_HOST"
echo "   ✓ Port: $PROXY_PORT"
echo "   ✓ API Key: $PROXY_KEY"

# Check if port is available
if netstat -tuln 2>/dev/null | grep -q ":$PROXY_PORT "; then
    echo -e "${YELLOW}⚠️  Warning: Port $PROXY_PORT is already in use${NC}"
    echo "  The proxy server may fail to start or conflict with another service"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -e "${BLUE}📋 Loading environment variables...${NC}"
    set -a
    source .env
    set +a
    echo "✓ Environment loaded"
fi

# Check for optional dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

PYTHON="$LLX_PATH/.venv/bin/python"

# Check for litellm
if ! $PYTHON -c "import litellm" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing litellm...${NC}"
    $PYTHON -m pip install litellm
fi

# Check for redis (optional)
if command -v redis-server >/dev/null 2>&1; then
    echo "   ✓ Redis server available (for caching)"
else
    echo -e "${YELLOW}⚠️  Redis not found - caching will be disabled${NC}"
    echo "   Install Redis for better performance: sudo apt-get install redis-server"
fi

# Run the example
echo -e "${BLUE}🏃 Starting proxy server...${NC}"
echo ""
echo -e "${YELLOW}💡 The proxy will start and run until you stop it with Ctrl+C${NC}"
echo ""

# Set PYTHONPATH to include llx
export PYTHONPATH="$LLX_PATH:$PYTHONPATH"

# Run the example
"$PYTHON" main.py "$@"
