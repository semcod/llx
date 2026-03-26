#!/usr/bin/env bash
# examples/planfile/run.sh - Unified Flow
DESCRIPTION="${1:-A complex project to demonstrate LLX strategy-driven development}"
llx plan wizard --description "$DESCRIPTION"
