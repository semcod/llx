#!/usr/bin/env bash
# Cloud Local Integration Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Cloud/Local Integration Example Runner${NC}"
echo "================================================"

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🔍 Checking predefined models allowing cloud/local seamless integration...${NC}"
llx info

echo -e "\n${BLUE}🧠 The router will automatically select local (if lightweight) or cloud depending on project metrics.${NC}"
llx select .

echo -e "\n${GREEN}✅ Example completed!${NC}"
