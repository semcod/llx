#!/usr/bin/env bash
# Fullstack Application Generation Example Runner

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}🚀 llx Fullstack Project Example Runner${NC}"
echo "======================================="

# Try to find llx command or fallback to local repo
if ! command -v llx &> /dev/null; then
    LLX_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    if [ -x "$LLX_PATH/.venv/bin/llx" ]; then
        shopt -s expand_aliases
        alias llx="$LLX_PATH/.venv/bin/llx"
    else
        export PYTHONPATH="$LLX_PATH"
        shopt -s expand_aliases
        alias llx="$LLX_PATH/.venv/bin/python3 -m llx"
    fi
fi

echo -e "\n${BLUE}🏗️ Generating fullstack scaffolding strategy using free models...${NC}"
llx plan generate . --profile free -o fullstack-strategy.yaml

echo -e "\n${BLUE}🤖 Applying the generated plan (dry run)...${NC}"
llx plan apply fullstack-strategy.yaml . --dry-run

echo -e "\n${GREEN}✅ Example completed!${NC}"
