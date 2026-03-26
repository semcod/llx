#!/usr/bin/env bash
# CLI Tools Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx CLI Tools Example Runner${NC}"
echo "=================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🛠️ Running analysis with internal tools...${NC}"
llx analyze . --run --max-tier free

echo -e "\n${GREEN}✅ Example completed!${NC}"
