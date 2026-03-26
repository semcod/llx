#!/usr/bin/env bash
# Planfile Workflow Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Planfile Usage Example Runner${NC}"
echo "========================================="

if ! command -v llx &> /dev/null; then
    echo -e "${RED}❌ Error: llx command not found. Please install llx.${NC}"
    exit 1
fi

echo -e "\n${BLUE}🔍 Generating refactoring strategy using free model profile...${NC}"
llx plan generate . --profile free -o demo-strategy.yaml

if [ -f "demo-strategy.yaml" ]; then
    echo -e "\n${BLUE}🤖 Applying strategy (dry run)...${NC}"
    llx plan apply demo-strategy.yaml . --dry-run
    
    echo -e "\n${GREEN}✅ Example completed successfully!${NC}"
    echo -e "${BLUE}💡 To apply changes for real, drop the --dry-run flag:${NC}"
    echo "   llx plan apply demo-strategy.yaml ."
else
    echo -e "\n${RED}❌ Failed to generate strategy.${NC}"
    exit 1
fi
