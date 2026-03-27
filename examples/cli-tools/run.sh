#!/usr/bin/env bash
# examples/cli-tools/run.sh - Unified Flow

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A CLI tool for system backup and restore}"

echo -e "${BOLD}🚀 LLX CLI Tools Example${NC}"
echo -e "${CYAN}──────────────────────${NC}"

echo -e "\n${YELLOW}Creating CLI tool project...${NC}"

# Use free profile for cost-effective development
python3 -m llx plan wizard --description "$DESCRIPTION" --profile free

echo -e "\n${GREEN}✅ Done!${NC}"
