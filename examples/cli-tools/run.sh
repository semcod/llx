#!/usr/bin/env bash
# examples/cli-tools/run.sh - Unified Flow
DESCRIPTION="${1:-A CLI tool for system backup and restore}"
llx plan wizard --description "$DESCRIPTION"
