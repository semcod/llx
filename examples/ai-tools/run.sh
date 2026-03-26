#!/usr/bin/env bash
# AI Tools Example Runner

set -e

BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx AI Tools Example Runner${NC}"
echo "================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🛠️  Showing available models and tools...${NC}"
llx info

echo -e "\n${BLUE}🤖 To use AI tools, start the llx proxy first:${NC}"
echo "   llx proxy start"
echo ""
echo "Then configure your favorite AI tool to use the local proxy (http://localhost:4000)."
echo "✅ Example completed!"
