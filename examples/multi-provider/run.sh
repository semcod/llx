#!/usr/bin/env bash
# Multi-Provider Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Multi-Provider Example Runner${NC}"
echo "======================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🌐 Displaying models from multiple providers (filtering by OpenRouter)...${NC}"
llx models --provider openrouter

echo -e "\n${BLUE}🌐 Asking for a recommendation across all providers (free tier max)...${NC}"
llx select .

echo -e "\n${GREEN}✅ Example completed!${NC}"
