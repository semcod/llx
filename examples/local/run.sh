#!/usr/bin/env bash
# Local Models Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Local Models Example Runner${NC}"
echo "====================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🖥️  Analyzing and routing to local models explicitly...${NC}"
llx analyze . --local

echo -e "\n${BLUE}🤖 Example chatting with a local model...${NC}"
echo "Command to run: llx chat . -p 'Summarize this project' --local"
# Just showing the command to save time on execution
llx select . --local

echo -e "\n${GREEN}✅ Example completed!${NC}"
