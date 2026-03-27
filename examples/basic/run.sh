#!/usr/bin/env bash
# examples/basic/run.sh
# Simple LLX workflow - all logic handled by LLX

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Project configuration
DESCRIPTION="${1:-}"
PROJECT="${2:-./my-api}"

echo -e "${BOLD}🚀 LLX Basic Example${NC}"
echo -e "${CYAN}─────────────────${NC}"

# Use LLX for everything
if [ -n "$DESCRIPTION" ]; then
    echo -e "\n${YELLOW}Generating project...${NC}"
    python3 -m llx plan all "$DESCRIPTION" --output "$PROJECT" --profile free --no-run
    
    echo -e "\n${GREEN}✅ Done!${NC}"
    echo -e "${CYAN}To monitor, run in another terminal:${NC}"
    echo -e "  llx plan monitor strategy.yaml"
else
    echo -e "\n${YELLOW}Usage:${NC}"
    echo "  $0 \"Project description\" [directory]"
    echo
    echo -e "${YELLOW}Example:${NC}"
    echo "  $0 \"Simple REST API\""
    echo
    echo -e "${CYAN}Or use LLX directly:${NC}"
    echo "  llx plan all \"Description\" --run --monitor --profile free"
fi
