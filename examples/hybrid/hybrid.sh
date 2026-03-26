#!/bin/bash
# LLX Hybrid Development Manager - Simple bash wrapper
# Intelligent cloud-local model selection for optimal development

set -e

# Default values
COMMAND=""
PROMPT=""
TIER=""
PROVIDER=""
LOCAL=false
EXECUTE=false
OUTPUT=""
BUDGET=""
TASK_FILE=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Help function
show_help() {
    cat << EOF
LLX Hybrid Development Manager

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    execute <prompt>        Execute a task with intelligent model selection
    queue <prompt>          Add task to queue for batch processing
    process [budget]        Process queued tasks with budget limit
    smart <prompt>          Execute with automatic optimization
    analyze                 Analyze usage patterns and costs
    optimize                Get optimization suggestions
    workflow <workflow>     Run predefined workflow

Workflows:
    fullstack               Generate full-stack application
    cli                     Generate CLI tool
    api                     Generate REST API
    mobile                  Generate mobile app
    refactor                Refactor existing code
    test                    Add comprehensive tests

Options:
    -t, --tier TIER         Force specific tier (cheap/balanced/premium/local)
    -p, --provider PROVIDER Force specific provider
    -l, --local             Prefer local models
    -e, --execute           Execute generated code
    -o, --output DIR        Output directory
    -b, --budget BUDGET     Budget limit for operations
    -q, --quiet             Quiet mode
    -v, --verbose           Verbose output
    -h, --help              Show this help

Examples:
    $0 execute 'Add user authentication'                    # Smart selection
    $0 execute 'Create API documentation' --local         # Force local
    $0 queue 'Fix login bug'                                # Add to queue
    $0 process 5.0                                         # Process with budget
    $0 smart 'Design microservices architecture'           # Auto-optimized
    $0 workflow fullstack                                  # Full-stack workflow

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        execute|queue|smart|analyze|optimize|workflow|process)
            COMMAND="$1"
            if [ "$1" != "analyze" ] && [ "$1" != "optimize" ] && [ "$1" != "process" ]; then
                shift
                PROMPT="$1"
            fi
            shift
            ;;
        -t|--tier)
            TIER="$2"
            shift 2
            ;;
        -p|--provider)
            PROVIDER="$2"
            shift 2
            ;;
        -l|--local)
            LOCAL=true
            shift
            ;;
        -e|--execute)
            EXECUTE=true
            shift
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -b|--budget)
            BUDGET="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET=true
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
            if [ -z "$PROMPT" ] && [ "$COMMAND" = "execute" ]; then
                PROMPT="$1"
            elif [ -z "$TASK_FILE" ] && [ "$COMMAND" = "queue" ]; then
                TASK_FILE="$1"
            elif [ -z "$BUDGET" ] && [ "$COMMAND" = "process" ]; then
                BUDGET="$1"
            else
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
            fi
            shift
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
    echo -e "${RED}Error: LLX not found${NC}"
    exit 1
fi

# Determine task type from prompt
determine_task_type() {
    local prompt="$1"
    if [[ "$prompt" =~ (test|spec|coverage) ]]; then
        echo "test"
    elif [[ "$prompt" =~ (refactor|clean|optimize) ]]; then
        echo "refactor"
    elif [[ "$prompt" =~ (api|endpoint|route) ]]; then
        echo "api"
    elif [[ "$prompt" =~ (ui|component|frontend) ]]; then
        echo "ui"
    elif [[ "$prompt" =~ (cli|tool|script) ]]; then
        echo "cli"
    else
        echo "boilerplate"
    fi
}

# Build LLX command
build_llx_cmd() {
    local cmd="llx chat"
    
    # Model selection
    if [ "$LOCAL" = true ]; then
        cmd="$cmd --local"
    elif [ -n "$TIER" ]; then
        cmd="$cmd --model $TIER"
    else
        # Smart selection based on task type
        task_type=$(determine_task_type "$PROMPT")
        case $task_type in
            test|boilerplate)
                cmd="$cmd --model cheap"
                ;;
            refactor|api)
                cmd="$cmd --model balanced"
                ;;
            ui|cli)
                cmd="$cmd --model balanced"
                ;;
            *)
                cmd="$cmd --model balanced"
                ;;
        esac
    fi
    
    # Provider
    [ -n "$PROVIDER" ] && cmd="$cmd --provider $PROVIDER"
    
    # Task type
    cmd="$cmd --task $task_type"
    
    # Prompt
    cmd="$cmd --prompt \"$PROMPT\""
    
    echo "$cmd"
}

# Execute command
case $COMMAND in
    execute)
        if [ -z "$PROMPT" ]; then
            echo -e "${RED}Error: No prompt provided${NC}"
            exit 1
        fi
        
        task_type=$(determine_task_type "$PROMPT")
        echo -e "${BLUE}🎯 Task Type:${NC} $task_type"
        
        if [ "$LOCAL" = true ]; then
            echo -e "${CYAN}🤖 Model Tier:${NC} local"
            echo -e "${CYAN}🔌 Provider:${NC} ollama"
        elif [ -n "$TIER" ]; then
            echo -e "${CYAN}🤖 Model Tier:${NC} $TIER"
        else
            echo -e "${CYAN}🤖 Model Tier:${NC} balanced"
        fi
        
        [ -n "$PROVIDER" ] && echo -e "${CYAN}🔌 Provider:${NC} $PROVIDER"
        echo -e "${CYAN}💰 Est. Cost:${NC} \$0.000"
        
        LLX_CMD=$(build_llx_cmd)
        if [ "$VERBOSE" = true ]; then
            echo -e "${YELLOW}Executing: $LLX_CMD${NC}"
        fi
        
        echo
        eval "$LLX_CMD"
        
        if [ "$EXECUTE" = true ] && [ -n "$OUTPUT" ]; then
            echo -e "${GREEN}🚀 Executing generated code...${NC}"
            # Here you would add execution logic
        fi
        ;;
        
    queue)
        if [ -z "$PROMPT" ]; then
            echo -e "${RED}Error: No prompt provided${NC}"
            exit 1
        fi
        echo "$PROMPT" >> .llx_queue.txt
        echo -e "${GREEN}✅ Task queued${NC}"
        ;;
        
    process)
        if [ ! -f .llx_queue.txt ]; then
            echo -e "${YELLOW}No tasks in queue${NC}"
            exit 0
        fi
        
        echo -e "${BLUE}Processing queue...${NC}"
        [ -n "$BUDGET" ] && echo -e "${CYAN}Budget limit: \$${BUDGET}${NC}"
        
        while IFS= read -r task; do
            echo -e "${GREEN}Processing: $task${NC}"
            PROMPT="$task"
            LLX_CMD=$(build_llx_cmd)
            eval "$LLX_CMD"
            echo
        done < .llx_queue.txt
        
        rm .llx_queue.txt
        echo -e "${GREEN}✅ Queue processed${NC}"
        ;;
        
    smart)
        if [ -z "$PROMPT" ]; then
            echo -e "${RED}Error: No prompt provided${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}🧠 Smart optimization enabled${NC}"
        # Auto-detect best settings
        if [[ "$PROMPT" =~ (simple|quick|small) ]]; then
            TIER="cheap"
        elif [[ "$PROMPT" =~ (complex|architecture|design) ]]; then
            TIER="premium"
        else
            TIER="balanced"
        fi
        
        COMMAND="execute"
        $0 "$COMMAND" "$PROMPT" --tier "$TIER" ${LOCAL:+--local} ${VERBOSE:+--verbose}
        ;;
        
    workflow)
        if [ -z "$PROMPT" ]; then
            echo -e "${RED}Error: No workflow specified${NC}"
            exit 1
        fi
        
        case $PROMPT in
            fullstack)
                echo -e "${BLUE}🏗️  Full-stack workflow${NC}"
                llx plan generate --local fullstack_strategy.yaml --profile local
                llx plan apply fullstack_strategy.yaml . --dry-run
                ;;
            cli)
                echo -e "${BLUE}🔧 CLI workflow${NC}"
                $0 execute "Generate a CLI tool with Click and Rich" --local
                ;;
            api)
                echo -e "${BLUE}🌐 API workflow${NC}"
                $0 execute "Create REST API with FastAPI" --local
                ;;
            refactor)
                echo -e "${BLUE}🔄 Refactor workflow${NC}"
                llx analyze .
                $0 execute "Refactor code to improve maintainability" --balanced
                ;;
            test)
                echo -e "${BLUE}🧪 Test workflow${NC}"
                $0 execute "Add comprehensive unit tests" --cheap
                ;;
            *)
                echo -e "${RED}Unknown workflow: $PROMPT${NC}"
                exit 1
                ;;
        esac
        ;;
        
    analyze)
        echo -e "${BLUE}📊 Analyzing usage patterns...${NC}"
        if [ -f .llx_history.json ]; then
            echo "Usage analysis available in .llx_history.json"
        else
            echo "No usage history found"
        fi
        ;;
        
    optimize)
        echo -e "${BLUE}💡 Optimization suggestions:${NC}"
        echo "• Use local models for simple tasks"
        echo "• Batch similar tasks together"
        echo "• Set budget limits to control costs"
        echo "• Use predefined workflows for common patterns"
        ;;
esac
