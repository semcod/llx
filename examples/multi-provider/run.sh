#!/usr/bin/env bash
# Multi-Provider Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Multi-Provider Example Runner${NC}"
echo "======================================="

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

echo -e "\n${BLUE}🌐 Displaying models from multiple providers (filtering by OpenRouter)...${NC}"
llx models --provider openrouter

echo -e "\n${BLUE}🌐 Asking for a recommendation across all providers (free tier max)...${NC}"
llx select .

echo -e "\n${GREEN}✅ Example completed!${NC}"
