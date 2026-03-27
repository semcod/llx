#!/usr/bin/env bash
# examples/docker/run.sh - Unified Flow for Docker
# This example demonstrates planning and implementing a Docker-ready application.

set -e

# Set PYTHONPATH to include llx source
export PYTHONPATH="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")"):$PYTHONPATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DESCRIPTION="${1:-A containerized microservice}"

# Set environment for Docker-specific features
export LLX_RUN_ENV=docker

echo -e "${BOLD}🐳 LLX Docker Example${NC}"
echo -e "${CYAN}─────────────────${NC}"

echo -e "\n${YELLOW}Creating containerized application...${NC}"
echo -e "${CYAN}Will generate Dockerfile and docker-compose.yml${NC}"

# Use balanced profile for Docker deployment
python3 -m llx plan wizard --description "$DESCRIPTION" --profile balanced

echo -e "\n${GREEN}✅ Done!${NC}"
