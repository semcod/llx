#!/usr/bin/env bash
# examples/fullstack/run.sh - Unified Flow
DESCRIPTION="${1:-A full-stack application with FastAPI backend and React frontend}"
llx plan wizard --description "$DESCRIPTION"
