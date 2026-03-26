#!/bin/bash
# setup-aliases.sh - Add LLX aliases to shell configuration

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 LLX Alias Setup${NC}"
echo -e "${YELLOW}Adding LLX aliases to your shell configuration...${NC}"

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    echo "Detected ZSH shell"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    echo "Detected BASH shell"
else
    echo -e "${YELLOW}Unknown shell. Please manually add aliases to your shell config.${NC}"
    exit 1
fi

# Check if aliases already exist
if grep -q "llx-gen" "$SHELL_CONFIG" 2>/dev/null; then
    echo -e "${YELLOW}LLX aliases already exist in $SHELL_CONFIG${NC}"
    echo -e "Remove them first if you want to re-install:"
    echo -e "  nano $SHELL_CONFIG"
    exit 0
fi

# Add aliases
echo "" >> "$SHELL_CONFIG"
echo "# LLX Aliases - Added by setup-aliases.sh" >> "$SHELL_CONFIG"
echo "alias llx-gen='llx plan generate . --profile cheap --sprints 8'" >> "$SHELL_CONFIG"
echo "alias llx-code='llx plan code strategy.yaml ./my-api --profile cheap'" >> "$SHELL_CONFIG"
echo "alias llx-run='llx plan run ./my-api'" >> "$SHELL_CONFIG"
echo "alias llx-mon='llx plan monitor strategy.yaml'" >> "$SHELL_CONFIG"
echo "alias llx-api='cd my-api && uvicorn main:app --reload'" >> "$SHELL_CONFIG"
echo "alias llx-new='python3 -c \"import sys; sys.path.insert(0, \\\"/home/tom/github/semcod/llx\\\"); from llx.cli.app import app; app()\" plan generate . --profile cheap --sprints 8 --focus api'" >> "$SHELL_CONFIG"
echo "alias llx-all='llx plan all'" >> "$SHELL_CONFIG"

echo -e "${GREEN}✅ Aliases added to $SHELL_CONFIG${NC}"
echo
echo -e "${YELLOW}To use aliases immediately, run:${NC}"
echo -e "  source $SHELL_CONFIG"
echo
echo -e "${BLUE}Available aliases:${NC}"
echo -e "  llx-gen   - Generate strategy (8 sprints, cheap profile)"
echo -e "  llx-code  - Generate code from strategy"
echo -e "  llx-run   - Run the generated API"
echo -e "  llx-mon   - Monitor the running application"
echo -e "  llx-api   - Quick start API with uvicorn"
echo -e "  llx-new   - Generate new API strategy"
echo -e "  llx-all   - Complete workflow (strategy + code + run)"
