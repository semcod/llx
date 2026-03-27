#!/usr/bin/env bash
# examples/multi-provider/run.sh - Unified Flow
# This example demonstrates using multiple LLM providers via the wizard.

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A project using multiple LLM providers}"

echo -e "${BOLD}🚀 LLX Multi-Provider Example${NC}"
echo -e "${CYAN}────────────────────────${NC}"

echo -e "\n${YELLOW}Creating project with multi-provider support...${NC}"
echo -e "${CYAN}LLX will automatically handle failover between providers.${NC}"

# Use balanced profile for multi-provider reliability
python3 -m llx plan wizard --description "$DESCRIPTION" --profile balanced

echo -e "\n${GREEN}✅ Done!${NC}"
