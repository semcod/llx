#!/usr/bin/env bash
# examples/aider/run.sh - Unified Flow with Aider
# This example demonstrates handing over implementation to Aider.

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-An API to be implemented using Aider}"

# Set environment for Aider integration
export LLX_CODE_TOOL=aider

echo -e "${BOLD}🚀 LLX Aider Example${NC}"
echo -e "${CYAN}──────────────────${NC}"

echo -e "\n${YELLOW}Creating project for Aider implementation...${NC}"
echo -e "${CYAN}Will generate strategy and hand off to Aider for coding${NC}"

# Use balanced profile for Aider integration
python3 -m llx plan wizard --description "$DESCRIPTION" --profile balanced

echo -e "\n${GREEN}✅ Done!${NC}"
