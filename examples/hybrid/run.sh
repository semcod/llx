#!/usr/bin/env bash
# Hybrid Workflow Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Hybrid (Local+Cloud) Example Runner${NC}"
echo "========================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🔍 Analyzing current project and preferring local models when possible...${NC}"
llx select . --local

echo -e "\n${GREEN}✅ Example completed!${NC}"
