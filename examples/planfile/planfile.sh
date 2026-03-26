#!/bin/bash
# LLX Planfile Manager - Simple bash wrapper
# Replaces planfile_manager.py with direct LLX commands

set -e

# Default values
COMMAND=""
STRATEGY_FILE="strategy.yaml"
PROJECT_PATH="."
FOCUS=""
MODEL=""
SPRINTS=3
DRY_RUN=false
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    cat << EOF
LLX Planfile Manager - Simple bash wrapper

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    generate    Generate a new strategy
    review      Review existing strategy
    execute     Execute strategy tasks
    monitor     Monitor execution progress
    status      Show current status

Options:
    -f, --file FILE      Strategy file (default: strategy.yaml)
    -p, --path PATH      Project path (default: .)
    -m, --model MODEL    Model to use
    -s, --sprints NUM    Number of sprints (default: 3)
    -F, --focus FOCUS    Focus area (complexity/duplication/tests/docs)
    -d, --dry-run        Dry run mode
    -v, --verbose        Verbose output
    -h, --help           Show this help

Examples:
    $0 generate --focus complexity --local
    $0 execute --dry-run
    $0 review --file my_strategy.yaml
    $0 status --verbose

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        generate|review|execute|monitor|status)
            COMMAND="$1"
            shift
            ;;
        -f|--file)
            STRATEGY_FILE="$2"
            shift 2
            ;;
        -p|--path)
            PROJECT_PATH="$2"
            shift 2
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -s|--sprints)
            SPRINTS="$2"
            shift 2
            ;;
        -F|--focus)
            FOCUS="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if command provided
if [ -z "$COMMAND" ]; then
    echo -e "${RED}Error: No command specified${NC}"
    show_help
    exit 1
fi

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    echo -e "${RED}Error: LLX not found. Install with: pip install llx${NC}"
    exit 1
fi

# Build LLX command
build_llx_cmd() {
    local cmd="llx"
    
    case $COMMAND in
        generate)
            cmd="$cmd plan generate"
            cmd="$cmd --sprints $SPRINTS"
            [ -n "$MODEL" ] && cmd="$cmd --model $MODEL"
            [ -n "$FOCUS" ] && cmd="$cmd --focus $FOCUS"
            ;;
        review)
            cmd="$cmd plan review"
            ;;
        execute)
            cmd="$cmd plan apply"
            [ "$DRY_RUN" = true ] && cmd="$cmd --dry-run"
            ;;
        monitor|status)
            cmd="$cmd plan status"
            ;;
    esac
    
    cmd="$cmd $STRATEGY_FILE $PROJECT_PATH"
    echo "$cmd"
}

# Execute command
echo -e "${BLUE}LLX Planfile Manager${NC}"
echo -e "${BLUE}Command: $COMMAND${NC}"
echo

# Show what will be executed
LLX_CMD=$(build_llx_cmd)
if [ "$VERBOSE" = true ]; then
    echo -e "${YELLOW}Executing: $LLX_CMD${NC}"
    echo
fi

# Run the command
case $COMMAND in
    generate)
        echo -e "${GREEN}Generating strategy...${NC}"
        if [ -n "$MODEL" ] && [[ "$MODEL" == "--local" || "$MODEL" == *"--local"* ]]; then
            $LLX_CMD --local
        else
            $LLX_CMD
        fi
        ;;
    review)
        echo -e "${GREEN}Reviewing strategy...${NC}"
        $LLX_CMD
        ;;
    execute)
        if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}Dry run mode - no changes will be made${NC}"
        fi
        echo -e "${GREEN}Executing strategy...${NC}"
        $LLX_CMD
        ;;
    monitor|status)
        echo -e "${GREEN}Checking status...${NC}"
        # Check if strategy file exists
        if [ -f "$STRATEGY_FILE" ]; then
            echo -e "${BLUE}Strategy file: $STRATEGY_FILE${NC}"
            # Show basic info
            if command -v yq &> /dev/null; then
                echo -e "${BLUE}Sprints: $(yq e '.sprints | length' "$STRATEGY_FILE")${NC}"
                echo -e "${BLUE}Project: $(yq e '.name' "$STRATEGY_FILE")${NC}"
            else
                echo "Install yq for detailed status"
            fi
        else
            echo -e "${RED}Strategy file not found: $STRATEGY_FILE${NC}"
        fi
        ;;
esac

echo
echo -e "${GREEN}Done!${NC}"
