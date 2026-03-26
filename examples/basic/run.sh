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

if ! command -v llx &> /dev/null; then
    echo -e "${RED}❌ Error: llx command not found. Please install llx.${NC}"
    exit 1
fi

echo -e "\n${BLUE}🔍 Analyzing project (using free tier limitation)...${NC}"
llx analyze . --max-tier free

echo -e "\n${BLUE}🤖 Quick model selection...${NC}"
llx select . --max-tier free

echo -e "\n${GREEN}✅ Example completed!${NC}"
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  • Try asking a question: llx chat . -p 'Explain this project' --tier free"
