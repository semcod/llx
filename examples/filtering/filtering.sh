#!/bin/bash
# LLX Advanced Filtering Demo - Bash version
# Demonstrates model selection based on constraints

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default values
INTERACTIVE=false
TASK=""
MAX_TIER=""
COST_LIMIT=""
PROVIDER=""
PREFER_LOCAL=false

# Help function
show_help() {
    cat << EOF
LLX Advanced Filtering Demo

Usage: $0 [OPTIONS]

Options:
    -i, --interactive       Run interactive demo
    -t, --task TASK         Task type (refactor/explain/quick_fix/review)
    -T, --tier TIER         Maximum model tier (cheap/balanced/premium)
    -c, --cost LIMIT        Cost limit in USD
    -p, --provider PROVIDER Force specific provider
    -l, --local             Prefer local models
    -h, --help              Show this help

Task Types:
    refactor      Code refactoring (uses balanced tier)
    explain       Code explanation (uses cheap tier)
    quick_fix     Quick fixes (uses cheap tier)
    review        Code review (uses premium tier)

Examples:
    $0 --interactive                    # Interactive mode
    $0 --task refactor --tier balanced  # Refactor with balanced model
    $0 --task explain --cost 0.01       # Explain with cost limit
    $0 --task review --local            # Review with local model

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -t|--task)
            TASK="$2"
            shift 2
            ;;
        -T|--tier)
            MAX_TIER="$2"
            shift 2
            ;;
        -c|--cost)
            COST_LIMIT="$2"
            shift 2
            ;;
        -p|--provider)
            PROVIDER="$2"
            shift 2
            ;;
        -l|--local)
            PREFER_LOCAL=true
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

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    echo -e "${RED}Error: LLX not found${NC}"
    exit 1
fi

# Determine model based on constraints
select_model() {
    local task="$1"
    local max_tier="$2"
    local cost_limit="$3"
    local provider="$4"
    local prefer_local="$5"
    
    local model_args=""
    
    # Prefer local if requested
    if [ "$prefer_local" = true ]; then
        echo "--local"
        return
    fi
    
    # Select based on task type
    case $task in
        refactor)
            if [ -n "$max_tier" ]; then
                model_args="--model $max_tier"
            else
                model_args="--model balanced"
            fi
            ;;
        explain|quick_fix)
            if [ -n "$cost_limit" ] && [ "$(echo "$cost_limit < 0.005" | bc -l)" -eq 1 ]; then
                model_args="--model openrouter/deepseek/deepseek-chat-v3-0324"
            else
                model_args="--model openrouter/deepseek/deepseek-chat-v3-0324"
            fi
            ;;
        review)
            if [ -n "$max_tier" ]; then
                model_args="--model $max_tier"
            else
                model_args="--model premium"
            fi
            ;;
        *)
            model_args="--model balanced"
            ;;
    esac
    
    # Note: provider is set via environment or config, not CLI flag
    echo "$model_args"
}

# Demo functions
demo_cost_filtering() {
    echo -e "${BLUE}🎯 Demo: Cost-based Filtering${NC}"
    echo
    
    prompts=(
        "Explain this Python function"
        "Refactor this module for better performance"
        "Add error handling to this code"
        "Write comprehensive tests"
    )
    
    costs=("0.001" "0.005" "0.01" "0.02")
    
    for i in "${!prompts[@]}"; do
        prompt="${prompts[$i]}"
        cost="${costs[$i]}"
        
        echo -e "${CYAN}Prompt: $prompt${NC}"
        echo -e "${CYAN}Cost limit: \$$cost${NC}"
        
        model_args=$(select_model "explain" "" "$cost" "" false)
        cmd="llx chat $model_args --task explain --prompt \"$prompt\""
        
        echo -e "${YELLOW}Command: $cmd${NC}"
        
        # Just show the command, don't execute
        echo
    done
}

demo_speed_priority() {
    echo -e "${BLUE}🚀 Demo: Speed Priority${NC}"
    echo
    
    echo -e "${CYAN}Small task (quick_fix):${NC}"
    cmd="llx chat --model cheap --task quick_fix --prompt \"Fix typo in README\""
    echo -e "${YELLOW}$cmd${NC}"
    echo
    
    echo -e "${CYAN}Large task (refactor):${NC}"
    cmd="llx chat --model balanced --task refactor --prompt \"Refactor entire module\""
    echo -e "${YELLOW}$cmd${NC}"
    echo
}

demo_provider_filter() {
    echo -e "${BLUE}🔌 Demo: Provider Filtering${NC}"
    echo
    
    providers=("anthropic" "openai" "openrouter" "ollama")
    
    for provider in "${providers[@]}"; do
        echo -e "${CYAN}Provider: $provider${NC}"
        cmd="llx chat --provider $provider --model balanced --task refactor --prompt \"Test task\""
        echo -e "${YELLOW}$cmd${NC}"
        echo
    done
}

interactive_demo() {
    echo -e "${BLUE}🎮 Interactive Filtering Demo${NC}"
    echo
    
    while true; do
        echo -e "${CYAN}Select demo:${NC}"
        echo "1) Cost-based filtering"
        echo "2) Speed priority"
        echo "3) Provider filtering"
        echo "4) Custom query"
        echo "5) Exit"
        read -p "Choice (1-5): " choice
        
        case $choice in
            1)
                demo_cost_filtering
                ;;
            2)
                demo_speed_priority
                ;;
            3)
                demo_provider_filter
                ;;
            4)
                read -p "Enter prompt: " prompt
                read -p "Task type (refactor/explain/quick_fix/review): " task_type
                read -p "Max tier (cheap/balanced/premium): " max_tier
                
                model_args=$(select_model "$task_type" "$max_tier" "" "" false)
                cmd="llx chat $model_args --task $task_type --prompt \"$prompt\""
                echo -e "${YELLOW}Executing: $cmd${NC}"
                eval "$cmd"
                ;;
            5)
                break
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                ;;
        esac
        
        echo
        echo -e "${BLUE}Press Enter to continue...${NC}"
        read
    done
}

# Main execution
main() {
    echo -e "${GREEN}LLX Advanced Filtering Demo${NC}"
    echo "=================================="
    echo
    
    if [ "$INTERACTIVE" = true ]; then
        interactive_demo
    elif [ -n "$TASK" ]; then
        # Single task execution
        model_args=$(select_model "$TASK" "$MAX_TIER" "$COST_LIMIT" "$PROVIDER" "$PREFER_LOCAL")
        
        echo -e "${CYAN}Task: $TASK${NC}"
        [ -n "$MAX_TIER" ] && echo -e "${CYAN}Max tier: $MAX_TIER${NC}"
        [ -n "$COST_LIMIT" ] && echo -e "${CYAN}Cost limit: \$$COST_LIMIT${NC}"
        [ -n "$PROVIDER" ] && echo -e "${CYAN}Provider: $PROVIDER${NC}"
        [ "$PREFER_LOCAL" = true ] && echo -e "${CYAN}Prefer local: yes${NC}"
        echo
        
        read -p "Enter prompt: " prompt
        
        cmd="llx chat $model_args --task $TASK --prompt \"$prompt\""
        echo -e "${YELLOW}Executing: $cmd${NC}"
        eval "$cmd"
    else
        # Run all demos
        demo_cost_filtering
        echo
        demo_speed_priority
        echo
        demo_provider_filter
    fi
}

# Check for bc command for cost comparison
if ! command -v bc &> /dev/null; then
    echo -e "${YELLOW}Warning: 'bc' not found. Cost comparisons may not work.${NC}"
fi

# Run main function
main
