#!/usr/bin/env bash
# Proxy Server Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Proxy Usage Example Runner${NC}"
echo "===================================="

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

echo -e "\n${BLUE}🛠️ Generating specific proxy configuration...${NC}"
llx proxy config -o proxy-test.yaml

echo -e "\n${BLUE}🚦 Checking proxy status...${NC}"
llx proxy status

echo -e "\n${BLUE}To start proxy manually, run: llx proxy start --fg${NC}"

echo -e "\n${GREEN}✅ Example completed!${NC}"
