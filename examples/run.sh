#!/bin/bash
# LLX Examples Launcher
# Universal launcher for all LLX examples

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$SCRIPT_DIR"

# Available examples
declare -A EXAMPLES=(
    ["basic"]="Basic LLX usage - analyze, select, chat"
    ["filtering"]="Advanced filtering with constraints"
    ["fullstack"]="Generate full-stack applications"
    ["planfile"]="Strategy-driven refactoring"
    ["hybrid"]="Hybrid cloud-local development"
    ["docker"]="Docker integration demo"
    ["aider"]="Aider AI pair programming"
    ["cli-tools"]="CLI tool generator"
    ["cloud-local"]="Cloud-local integration"
    ["local"]="Local-only development"
    ["multi-provider"]="Multiple LLM providers"
    ["ai-tools"]="AI tools orchestration"
    ["proxy"]="Proxy configuration demo"
    ["vscode-roocode"]="VS Code + RoCode integration"
)

# Help function
show_help() {
    echo -e "${BOLD}LLX Examples Launcher${NC}"
    echo "========================"
    echo
    echo "Available examples:"
    echo
    
    for example in "${!EXAMPLES[@]}"; do
        description="${EXAMPLES[$example]}"
        if [ -f "$EXAMPLES_DIR/$example/run.sh" ] || [ -f "$EXAMPLES_DIR/$example/$example.sh" ]; then
            echo -e "  ${GREEN}$example${NC} - $description"
        else
            echo -e "  $example - $description"
        fi
    done
    
    echo
    echo "Usage:"
    echo "  $0 [EXAMPLE] [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help"
    echo "  -l, --list     List all examples with status"
    echo "  -v, --verbose  Verbose output"
    echo
    echo "Examples:"
    echo "  $0 basic                    # Run basic example"
    echo "  $0 fullstack --local       # Run fullstack with local model"
    echo "  $0 planfile generate       # Run planfile with generate command"
    echo
}

# List examples with status
list_examples() {
    echo -e "${BOLD}LLX Examples Status${NC}"
    echo "====================="
    echo
    
    for example in "${!EXAMPLES[@]}"; do
        description="${EXAMPLES[$example]}"
        
        if [ -d "$EXAMPLES_DIR/$example" ]; then
            # Check for run scripts
            if [ -f "$EXAMPLES_DIR/$example/run.sh" ]; then
                status="${GREEN}✓ run.sh${NC}"
            elif [ -f "$EXAMPLES_DIR/$example/$example.sh" ]; then
                status="${GREEN}✓ $example.sh${NC}"
            elif [ -f "$EXAMPLES_DIR/$example/demo.sh" ]; then
                status="${GREEN}✓ demo.sh${NC}"
            elif [ -f "$EXAMPLES_DIR/$example/generate.sh" ]; then
                status="${GREEN}✓ generate.sh${NC}"
            else
                status="${YELLOW}○ Python files${NC}"
            fi
            
            # Check if it's been refactored
            if [ -f "$EXAMPLES_DIR/$example/$example.sh" ] || [ -f "$EXAMPLES_DIR/$example/run.sh" ]; then
                refactored="${GREEN}[Refactored]${NC}"
            else
                refactored="${YELLOW}[Original]${NC}"
            fi
            
            printf "  %-15s %s %s\n" "$example" "$status" "$refactored"
            printf "  %-15s %s\n" "" "${CYAN}$description${NC}"
            echo
        fi
    done
}

# Run example
run_example() {
    local example="$1"
    shift
    local args=("$@")
    
    if [ ! -d "$EXAMPLES_DIR/$example" ]; then
        echo -e "${RED}Error: Example '$example' not found${NC}"
        echo
        echo "Available examples:"
        for ex in "${!EXAMPLES[@]}"; do
            echo "  - $ex"
        done
        exit 1
    fi
    
    echo -e "${BLUE}Running example: $example${NC}"
    echo -e "${CYAN}${EXAMPLES[$example]}${NC}"
    echo
    
    # Change to example directory
    cd "$EXAMPLES_DIR/$example"
    
    # Try different scripts in order of preference
    if [ -f "run.sh" ]; then
        echo -e "${YELLOW}Executing: ./run.sh ${args[*]}${NC}"
        ./run.sh "${args[@]}"
    elif [ -f "$example.sh" ]; then
        echo -e "${YELLOW}Executing: ./$example.sh ${args[*]}${NC}"
        ./"$example.sh" "${args[@]}"
    elif [ -f "demo.sh" ]; then
        echo -e "${YELLOW}Executing: ./demo.sh ${args[*]}${NC}"
        ./demo.sh "${args[@]}"
    elif [ -f "generate.sh" ]; then
        echo -e "${YELLOW}Executing: ./generate.sh ${args[*]}${NC}"
        ./generate.sh "${args[@]}"
    elif [ -f "main.py" ]; then
        echo -e "${YELLOW}Executing: python main.py ${args[*]}${NC}"
        python main.py "${args[@]}"
    else
        echo -e "${RED}Error: No runnable script found in $example${NC}"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    local missing=()
    
    # Check in current PATH and virtual environment
    if ! command -v llx &> /dev/null && ! python -c "import llx" 2>/dev/null; then
        missing+=("llx")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}Error: Missing dependencies:${NC}"
        for dep in "${missing[@]}"; do
            echo "  - $dep"
        done
        echo
        echo -e "${CYAN}Install LLX with: pip install llx${NC}"
        exit 1
    fi
}

# Parse arguments
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    -l|--list)
        list_examples
        exit 0
        ;;
    -v|--verbose)
        VERBOSE=true
        shift
        ;;
esac

# Check dependencies
check_dependencies

# Run the example
run_example "$@"
