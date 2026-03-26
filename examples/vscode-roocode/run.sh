#!/usr/bin/env bash
# VSCode Roocode Integration Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx VSCode RooCode MCP Example Runner${NC}"
echo "==========================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🔌 To integrate llx into RooCode, add MCP configuration: ${NC}"
llx mcp config

echo -e "\n${BLUE}Available MCP Tools for RooCode:${NC}"
llx mcp tools

echo -e "\n${GREEN}✅ Example completed!${NC}"
