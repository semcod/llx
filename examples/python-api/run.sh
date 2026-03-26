#!/usr/bin/env bash
# examples/python-api/run.sh - Powered by LLX Wizard
# Simplest possible workflow: Let LLX handle the lifecycle.

DESCRIPTION="${1:-}"
PROJECT="${2:-./my-api}"

# Unified command for architecture, code, and guidance
llx plan wizard --description "$DESCRIPTION" --output strategy.yaml
