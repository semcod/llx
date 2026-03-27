#!/usr/bin/env bash
# examples/proxy/run.sh - Unified Flow for Proxy

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A project requiring proxy configuration}"

echo -e "${BOLD}🚀 LLX Proxy Example${NC}"
echo -e "${CYAN}──────────────────${NC}"

echo -e "\n${YELLOW}Creating project with proxy support...${NC}"
echo -e "${CYAN}Will configure LiteLLM proxy for model routing${NC}"

# Use balanced profile for proxy setup
python3 -m llx plan wizard --description "$DESCRIPTION" --profile balanced

echo -e "\n${GREEN}✅ Done!${NC}"
