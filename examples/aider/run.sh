#!/usr/bin/env bash
# examples/aider/run.sh - Unified Flow with Aider
# This example demonstrates handing over implementation to Aider.
export LLX_CODE_TOOL=aider
llx plan wizard --description "${1:-An API to be implemented using Aider}"
