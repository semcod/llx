#!/usr/bin/env bash
# Basic llx Example Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 llx Basic Usage Example Runner${NC}"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found. Please run from examples/basic directory${NC}"
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

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  ANTHROPIC_API_KEY not set${NC}"
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENROUTER_API_KEY not set${NC}"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set${NC}"
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -e "${BLUE}📋 Loading environment variables...${NC}"
    set -a
    source .env
    set +a
    echo "✓ Environment loaded"
fi

# Run the example
echo -e "${BLUE}🏃 Running basic example...${NC}"
echo ""

# Use the virtual environment's Python
PYTHON="$LLX_PATH/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo -e "${RED}❌ Python not found in virtual environment${NC}"
    exit 1
fi

# Set PYTHONPATH to include llx
export PYTHONPATH="$LLX_PATH:$PYTHONPATH"

# Run the example
"$PYTHON" main.py "$@"

echo ""
echo -e "${GREEN}✅ Example completed!${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  • Try other examples: cd ../proxy && ./run.sh"
echo "  • Read the documentation: cat ../README.md"
echo "  • Check project analysis: cd $LLX_PATH && .venv/bin/python -m llx analyze ."
