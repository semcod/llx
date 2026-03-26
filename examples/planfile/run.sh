#!/usr/bin/env bash
# examples/planfile/run.sh
# Strategy generation and dry-run execution

set -e

# Setup llx alias
if ! command -v llx &>/dev/null; then
    alias llx="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/.venv/bin/llx"
fi
shopt -s expand_aliases

echo "🚀 llx Planfile Example"
echo "──────────────────────"

echo "1. Generating strategy..."
llx plan generate . --profile free -o demo-strategy.yaml

echo -e "\n2. Applying strategy (dry run)..."
llx plan apply demo-strategy.yaml . --dry-run

echo -e "\n✅ Done!"
