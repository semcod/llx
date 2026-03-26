#!/usr/bin/env bash
# Fullstack Application Generation Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Fullstack Project Example Runner${NC}"
echo "======================================="

if ! command -v llx &> /dev/null; then
    echo "❌ Error: llx command not found."
    exit 1
fi

echo -e "\n${BLUE}🏗️ Generating fullstack scaffolding strategy using free models...${NC}"
llx plan generate . --profile free -o fullstack-strategy.yaml

echo -e "\n${BLUE}🤖 Applying the generated plan (dry run)...${NC}"
llx plan apply fullstack-strategy.yaml . --dry-run

echo -e "\n${GREEN}✅ Example completed!${NC}"
