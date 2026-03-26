#!/usr/bin/env bash
# llx Multi-Provider Example Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 llx Multi-Provider Example Runner${NC}"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found. Please run from examples/multi-provider directory${NC}"
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

# Check for API keys
echo -e "${BLUE}🔑 Checking API keys...${NC}"

# Source the .env file to check keys
if [ -f ".env" ]; then
    set -a
    source .env 2>/dev/null || true
    set +a
fi

# Count available providers
PROVIDER_COUNT=0

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "   ✓ Anthropic Claude API key"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
fi

if [ ! -z "$OPENROUTER_API_KEY" ]; then
    echo "   ✓ OpenRouter API key"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
fi

if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "   ✓ OpenAI API key"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
fi

if [ ! -z "$GEMINI_API_KEY" ]; then
    echo "   ✓ Gemini API key"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
fi

if [ ! -z "$DEEPSEEK_API_KEY" ]; then
    echo "   ✓ DeepSeek API key"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
fi

if [ ! -z "$GROQ_API_KEY" ]; then
    echo "   ✓ Groq API key"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
fi

if [ ! -z "$MISTRAL_API_KEY" ]; then
    echo "   ✓ Mistral API key"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
fi

if [ $PROVIDER_COUNT -eq 0 ]; then
    echo -e "${RED}❌ Error: No API keys found. Please configure at least one provider:${NC}"
    echo ""
    echo "Edit .env file and add your API keys:"
    echo "  ANTHROPIC_API_KEY=sk-ant-api03-..."
    echo "  OPENROUTER_API_KEY=sk-or-v1-..."
    echo "  OPENAI_API_KEY=sk-..."
    echo "  GEMINI_API_KEY=..."
    echo "  DEEPSEEK_API_KEY=..."
    exit 1
fi

echo -e "${GREEN}✓ Found $PROVIDER_COUNT provider(s) configured${NC}"

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

# Run the example
echo -e "${BLUE}🏃 Running multi-provider example...${NC}"
echo ""

# Set PYTHONPATH to include llx
export PYTHONPATH="$LLX_PATH:$PYTHONPATH"

# Run the example
"$PYTHON" main.py "$@"

echo ""
echo -e "${GREEN}✅ Example completed!${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  • Try the proxy example: cd ../proxy && ./run.sh"
echo "  • Test with real API calls (requires credits)"
echo "  • Configure provider-specific models in llx.toml"
echo "  • Set up budget limits per provider"
