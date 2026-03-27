#!/usr/bin/env bash
# examples/hybrid/run.sh - Unified Flow for Hybrid development

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A hybrid cloud-local application}"

echo -e "${BOLD}🚀 LLX Hybrid Example${NC}"
echo -e "${CYAN}───────────────────${NC}"

echo -e "\n${YELLOW}Creating hybrid project...${NC}"
echo -e "${CYAN}This will use local models for development and cloud for deployment.${NC}"

# Use balanced profile for hybrid (mix of local and cloud)
python3 -m llx plan wizard --description "$DESCRIPTION" --profile balanced

echo -e "\n${GREEN}✅ Done!${NC}"
