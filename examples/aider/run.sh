#!/usr/bin/env bash
# Aider Integration Example Runner

set -e

# Try to find llx command or fallback to local repo
if ! command -v llx &> /dev/null; then
    LLX_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    if [ -x "$LLX_PATH/.venv/bin/llx" ]; then
        shopt -s expand_aliases
        alias llx="$LLX_PATH/.venv/bin/llx"
    else
        export PYTHONPATH="$LLX_PATH"
        shopt -s expand_aliases
        alias llx="$LLX_PATH/.venv/bin/python3 -m llx"
    fi
fi

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Aider Integration Example Runner${NC}"
echo "======================================="

echo -e "\n${BLUE}🔍 Assuming you have a project to analyze...${NC}"
llx analyze . --max-tier free

echo -e "\n${BLUE}🤖 Starting LiteLLM proxy in the background...${NC}"
echo "To use Aider with llx, you can start the proxy:"
echo "  llx proxy start"
echo ""
echo "Then run aider pointing to the local proxy:"
echo "  export OPENAI_API_BASE=http://localhost:4000"
echo "  export OPENAI_API_KEY=dummy"
echo "  aider --model openai/gpt-3.5-turbo"

echo -e "\n${GREEN}✅ Example completed!${NC}"
