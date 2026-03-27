#!/usr/bin/env bash
# examples/fullstack/run.sh - Unified Flow

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A full-stack application with FastAPI backend and React frontend}"

echo -e "${BOLD}🚀 LLX Fullstack Example${NC}"
echo -e "${CYAN}─────────────────────${NC}"

echo -e "\n${YELLOW}Creating fullstack application...${NC}"
echo -e "${CYAN}Will generate both backend and frontend code${NC}"

# Use balanced profile for fullstack development
python3 -m llx plan wizard --description "$DESCRIPTION" --profile balanced

echo -e "\n${GREEN}✅ Done!${NC}"
