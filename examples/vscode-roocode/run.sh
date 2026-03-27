#!/usr/bin/env bash
# examples/vscode-roocode/run.sh - Unified Flow

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-VS Code + Roo-Code integration demo}"

echo -e "${BOLD}🚀 LLX VSCode Roo-Code Example${NC}"
echo -e "${CYAN}─────────────────────────${NC}"

echo -e "\n${YELLOW}Creating VS Code extension project...${NC}"
echo -e "${CYAN}Will generate VS Code extension with Roo-Code integration${NC}"

# Use free profile for extension development
python3 -m llx plan wizard --description "$DESCRIPTION" --profile free

echo -e "\n${GREEN}✅ Done!${NC}"
