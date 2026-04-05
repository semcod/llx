#!/usr/bin/env bash
# examples/planfile/run.sh - Unified Flow

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A complex project to demonstrate LLX strategy-driven development}"

# Check for help flag
if [ "$DESCRIPTION" = "--help" ] || [ "$DESCRIPTION" = "-h" ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [description]"
    echo
    echo -e "${YELLOW}Example:${NC}"
    echo "  $0 \"A complex web application with microservices architecture\""
    echo
    echo -e "${CYAN}This example demonstrates LLX planfile capabilities:${NC}"
    echo "  - Strategy-driven development"
    echo "  - Comprehensive project planning"
    echo "  - Multi-sprint organization"
    exit 0
fi

echo -e "${BOLD}🚀 LLX Planfile Example${NC}"
echo -e "${CYAN}────────────────────${NC}"

echo -e "\n${YELLOW}Creating strategy-driven project...${NC}"
echo -e "${CYAN}Will generate comprehensive strategy.yaml and implementation plan${NC}"

# Use balanced profile for complex project
python3 -m llx plan wizard --description "$DESCRIPTION" --profile balanced

echo -e "\n${GREEN}✅ Done!${NC}"
