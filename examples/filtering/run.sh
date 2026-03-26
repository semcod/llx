#!/usr/bin/env bash
# Filtering Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Filtering Usage Example Runner${NC}"
echo "======================================"

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🔍 Showing only free accessible models...${NC}"
llx models --tier free

echo -e "\n${GREEN}✅ Example completed!${NC}"
