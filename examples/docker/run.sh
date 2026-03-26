#!/usr/bin/env bash
# examples/docker/run.sh - Unified Flow for Docker
# This example demonstrates planning and implementing a Docker-ready application.
export LLX_RUN_ENV=docker
llx plan wizard --description "${1:-A containerized microservice}"
