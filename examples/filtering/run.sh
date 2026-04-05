#!/usr/bin/env bash
# examples/filtering/run.sh - Unified Flow with Constraints
# This example demonstrates using the wizard with specific constraints.

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A project with strict filtering constraints}"

# Check for help flag
if [ "$DESCRIPTION" = "--help" ] || [ "$DESCRIPTION" = "-h" ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [description]"
    echo
    echo -e "${YELLOW}Example:${NC}"
    echo "  $0 \"A secure API with strict code quality constraints\""
    echo
    echo -e "${CYAN}This example demonstrates LLX filtering capabilities:${NC}"
    echo "  - Code quality constraints"
    echo "  - Dependency filtering"
    echo "  - Security requirements"
    exit 0
fi

echo -e "${BOLD}🚀 LLX Filtering Example${NC}"
echo -e "${CYAN}─────────────────────${NC}"

echo -e "\n${YELLOW}Creating project with filtering constraints...${NC}"
echo -e "${CYAN}Will apply strict code quality and dependency filters${NC}"

# Use free profile with constraints
python3 -m llx plan wizard --description "$DESCRIPTION" --profile free

echo -e "\n${GREEN}✅ Done!${NC}"
