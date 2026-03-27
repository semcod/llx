#!/usr/bin/env bash
# examples/python-api/run.sh
# Simplest possible workflow: Let LLX handle the lifecycle.

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

DESCRIPTION="${1:-Simple Python API}"
PROJECT="${2:-./my-api}"

echo -e "${BOLD}🚀 LLX Python API Example${NC}"
echo -e "${CYAN}──────────────────────${NC}"

if [ -n "$DESCRIPTION" ]; then
    echo -e "\n${YELLOW}Creating Python API project...${NC}"
    
    # Generate strategy and code in one command
    python3 -m llx plan wizard --description "$DESCRIPTION" --output strategy.yaml --profile free
    
    echo -e "\n${GREEN}✅ Project created!${NC}"
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  cd ${PROJECT}"
    echo -e "  python3 -m llx plan run ."
    echo -e "  python3 -m llx plan monitor strategy.yaml"
else
    echo -e "\n${YELLOW}Usage:${NC}"
    echo "  $0 \"Project description\" [directory]"
    echo
    echo -e "${YELLOW}Example:${NC}"
    echo "  $0 \"FastAPI REST API with user management\""
fi
