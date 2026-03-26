#!/usr/bin/env bash
# Docker Environment Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Docker Usage Example Runner${NC}"
echo "=================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🐳 Demonstrating how to use llx in Docker...${NC}"
echo "You can mount your project directory into an llx container:"
echo "  docker run -v \$(pwd):/project -it llx/llx analyze /project --max-tier free"

echo -e "\n${BLUE}🔍 For now, analyzing the current directory natively...${NC}"
llx analyze . --max-tier free

echo -e "\n${GREEN}✅ Example completed!${NC}"
