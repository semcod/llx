#!/usr/bin/env bash
# Aider Integration Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Aider Integration Example Runner${NC}"
echo "======================================="

echo -e "\n${BLUE}🔍 Assuming you have a project to analyze...${NC}"
llx analyze . --max-tier free

echo -e "\n${BLUE}🤖 Starting LiteLLM proxy in the background...${NC}"
# Use a free/local model via proxy if Aider uses it. For now, we just show commands.
echo "To use Aider with llx, you can start the proxy:"
echo "  llx proxy start"
echo ""
echo "Then run aider pointing to the local proxy:"
echo "  export OPENAI_API_BASE=http://localhost:4000"
echo "  export OPENAI_API_KEY=dummy"
echo "  aider --model openai/gpt-3.5-turbo"

echo -e "\n${GREEN}✅ Check out configuration details above!${NC}"
