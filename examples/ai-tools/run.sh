#!/usr/bin/env bash
# AI Tools Example Runner

set -e

BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx AI Tools Example Runner${NC}"
echo "================================="

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

echo -e "\n${BLUE}🛠️  Showing available models and tools...${NC}"
llx info

echo -e "\n${BLUE}🤖 To use AI tools, start the llx proxy first:${NC}"
echo "   llx proxy start"
echo ""
echo "Then configure your favorite AI tool to use the local proxy (http://localhost:4000)."
echo "✅ Example completed!"
