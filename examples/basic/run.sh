#!/usr/bin/env bash
# Basic llx Example Runner

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 llx Basic Usage Example Runner${NC}"
echo "=================================="

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

echo -e "\n${BLUE}🔍 Analyzing project (using free tier limitation)...${NC}"
llx analyze . --max-tier free

echo -e "\n${BLUE}🤖 Quick model selection...${NC}"
llx select .

echo -e "\n${GREEN}✅ Example completed!${NC}"
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  • Try asking a question: llx chat . -p 'Explain this project' --tier free"
