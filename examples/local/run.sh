#!/usr/bin/env bash
# examples/local/run.sh - Unified Flow for Local-only development

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A local-only analytics tool}"

echo -e "${BOLD}🚀 LLX Local Example${NC}"
echo -e "${CYAN}──────────────────${NC}"

echo -e "\n${YELLOW}Creating local-only project...${NC}"

# Force local model usage
python3 -m llx plan wizard --description "$DESCRIPTION" --profile local

echo -e "\n${GREEN}✅ Done!${NC}"
echo -e "${CYAN}All processing done locally with no API calls.${NC}"
