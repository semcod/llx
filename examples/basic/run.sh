#!/usr/bin/env bash
# examples/basic/run.sh
# Basic usage of llx tools

set -e

# Setup llx alias
if ! command -v llx &>/dev/null; then
    alias llx="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/.venv/bin/llx"
fi
shopt -s expand_aliases

echo "🚀 llx Basic Example"
echo "───────────────────"

echo "1. Analyzing project..."
llx analyze . --max-tier free

echo -e "\n2. Selecting optimal model..."
llx select .

echo -e "\n✅ Done! Try: llx chat . 'Explain this code'"
