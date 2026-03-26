#!/bin/bash
# Hybrid Cloud-Local Development Script
# Optimizes LLX usage by intelligently choosing between cloud and local models

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
DEFAULT_BUDGET=10.0
USAGE_LOG="$HOME/.llx/usage.log"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TASK_QUEUE="$PROJECT_ROOT/.llx/task_queue.txt"

# Ensure directories exist
mkdir -p "$(dirname "$USAGE_LOG")"
mkdir -p "$(dirname "$TASK_QUEUE")"

# Task classification patterns
declare -A TASK_PATTERNS=(
    ["boilerplate"]="create generate scaffold template setup initialize structure skeleton"
    ["simple_fix"]="fix bug error typo lint format simple quick minor small"
    ["documentation"]="document readme comment explain describe manual guide tutorial"
    ["unit_test"]="test spec pytest jest coverage tdd testing"
    ["refactoring"]="refactor improve optimize clean restructure reorganize simplify"
    ["feature"]="implement add feature functionality capability build develop"
    ["integration"]="integrate connect api service database external third-party"
    ["architecture"]="architecture design system structure pattern microservices scalable"
    ["security"]="security auth authentication authorization encrypt secure vulnerability audit"
    ["performance"]="performance optimize speed memory cpu efficient fast scalable benchmark"
    ["algorithm"]="algorithm complex mathematical computational machine learning ai"
)

# Tier mapping for tasks
declare -A TASK_TIERS=(
    ["boilerplate"]="cheap"
    ["simple_fix"]="cheap"
    ["documentation"]="cheap"
    ["unit_test"]="cheap"
    ["refactoring"]="balanced"
    ["feature"]="balanced"
    ["integration"]="balanced"
    ["architecture"]="premium"
    ["security"]="premium"
    ["performance"]="premium"
    ["algorithm"]="premium"
)

# Provider preferences
declare -A PROVIDER_PREFS=(
    ["cheap"]="openrouter"
    ["balanced"]="anthropic"
    ["premium"]="anthropic"
    ["local"]="ollama"
)

print_usage() {
    echo -e "${BLUE}LLX Hybrid Development Manager${NC}"
    echo -e "${CYAN}Intelligent cloud-local model selection for optimal development${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS] <command> [args]"
    echo ""
    echo "Commands:"
    echo "  execute <prompt>        Execute a task with intelligent model selection"
    echo "  queue <prompt>          Add task to queue for batch processing"
    echo "  process [budget]        Process queued tasks with budget limit"
    echo "  smart <prompt>          Execute with automatic optimization"
    echo "  analyze                 Analyze usage patterns and costs"
    echo "  optimize                Get optimization suggestions"
    echo "  workflow <workflow>     Run predefined workflow"
    echo ""
    echo "Options:"
    echo "  -t, --tier TIER         Force specific tier (cheap/balanced/premium/local)"
    echo "  -p, --provider PROVIDER Force specific provider"
    echo "  -l, --local             Prefer local models"
    echo "  -e, --execute           Execute generated code"
    echo "  -o, --output DIR        Output directory"
    echo "  -b, --budget BUDGET     Budget limit for operations"
    echo "  -q, --quiet             Quiet mode"
    echo "  -v, --verbose           Verbose output"
    echo "  -h, --help              Show this help"
    echo ""
    echo "Workflows:"
    echo "  fullstack               Generate full-stack application"
    echo "  cli                     Generate CLI tool"
    echo "  api                     Generate REST API"
    echo "  mobile                  Generate mobile app"
    echo "  refactor                Refactor existing code"
    echo "  test                    Add comprehensive tests"
    echo ""
    echo "Examples:"
    echo "  $0 execute 'Add user authentication'                    # Smart selection"
    echo "  $0 execute 'Create API documentation' --local         # Force local"
    echo "  $0 queue 'Fix login bug'                                # Add to queue"
    echo "  $0 process 5.0                                         # Process with $5 budget"
    echo "  $0 smart 'Design microservices architecture'           # Auto-optimized"
    echo "  $0 workflow fullstack                                  # Full-stack workflow"
}

log_usage() {
    local timestamp=$(date -Iseconds)
    local task_type=$1
    local tier=$2
    local provider=$3
    local cost=$4
    local success=$5
    
    echo "$timestamp,$task_type,$tier,$provider,$cost,$success" >> "$USAGE_LOG"
}

classify_task() {
    local prompt=$1
    local prompt_lower=$(echo "$prompt" | tr '[:upper:]' '[:lower:]')
    local best_match=""
    local best_score=0
    
    for task_type in "${!TASK_PATTERNS[@]}"; do
        local score=0
        local patterns="${TASK_PATTERNS[$task_type]}"
        
        for pattern in $patterns; do
            if [[ "$prompt_lower" == *"$pattern"* ]]; then
                ((score++))
            fi
        done
        
        if ((score > best_score)); then
            best_score=$score
            best_match=$task_type
        fi
    done
    
    echo "${best_match:-feature}"
}

estimate_cost() {
    local tier=$1
    local provider=$2
    
    # Base costs per 1k tokens
    case $tier in
        "free"|"local") echo "0.000" ;;
        "cheap") echo "0.002" ;;
        "balanced") echo "0.010" ;;
        "premium") echo "0.050" ;;
        *) echo "0.010" ;;
    esac
}

execute_task() {
    local prompt=$1
    local force_tier=$2
    local force_provider=$3
    local prefer_local=$4
    local execute_code=$5
    local output_dir=$6
    local quiet=$7
    
    # Classify task
    local task_type=$(classify_task "$prompt")
    
    # Determine optimal tier
    local tier="${force_tier:-${TASK_TIERS[$task_type]}}"
    
    # Check if local is preferred and suitable
    if [[ "$prefer_local" == "true" ]] && [[ "$tier" == "cheap" || "$tier" == "free" ]]; then
        tier="local"
    fi
    
    # Select provider
    local provider="${force_provider:-${PROVIDER_PREFS[$tier]}}"
    
    # Estimate cost
    local cost=$(estimate_cost "$tier" "$provider")
    
    if [[ "$quiet" != "true" ]]; then
        echo -e "${BLUE}🎯 Task Type:${NC} $task_type"
        echo -e "${PURPLE}🤖 Model Tier:${NC} $tier"
        echo -e "${CYAN}🔌 Provider:${NC} $provider"
        echo -e "${YELLOW}💰 Est. Cost:${NC} \$$cost"
    fi
    
    # Build LLX command
    local cmd="llx chat --model "$tier" --task refactor"
    
    if [[ "$provider" != "ollama" ]]; then
        cmd="$cmd --provider $provider"
    fi
    
    if [[ "$tier" == "local" ]]; then
        cmd="$cmd --local"
    fi
    
    if [[ -n "$output_dir" ]]; then
        cmd="$cmd --output $output_dir"
    fi
    
    cmd="$cmd --prompt \"$prompt\""
    
    # Execute
    local start_time=$(date +%s)
    
    if eval "$cmd" > /tmp/llx_output.log 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [[ "$quiet" != "true" ]]; then
            echo -e "${GREEN}✅ Task completed in ${duration}s${NC}"
        fi
        
        # Log usage
        log_usage "$task_type" "$tier" "$provider" "$cost" "true"
        
        # Execute code if requested
        if [[ "$execute_code" == "true" && -n "$output_dir" ]]; then
            execute_generated_code "$output_dir"
        fi
        
        return 0
    else
        if [[ "$quiet" != "true" ]]; then
            echo -e "${RED}❌ Task failed${NC}"
            if [[ "$verbose" == "true" ]]; then
                cat /tmp/llx_output.log
            fi
        fi
        
        # Try fallback
        if [[ "$tier" != "local" ]]; then
            if [[ "$quiet" != "true" ]]; then
                echo -e "${YELLOW}🔄 Trying local model fallback...${NC}"
            fi
            execute_task "$prompt" "local" "" "true" "$execute_code" "$output_dir" "$quiet"
            return $?
        fi
        
        # Log failure
        log_usage "$task_type" "$tier" "$provider" "$cost" "false"
        
        return 1
    fi
}

execute_generated_code() {
    local output_dir=$1
    
    if [[ -d "$output_dir" ]]; then
        cd "$output_dir"
        
        # Detect project type and setup
        if [[ -f "package.json" ]]; then
            echo -e "${BLUE}📦 Setting up Node.js project...${NC}"
            npm install
        elif [[ -f "requirements.txt" ]]; then
            echo -e "${BLUE}🐍 Setting up Python project...${NC}"
            if [[ -f "pyproject.toml" ]]; then
                pip install .
            else
                pip install -r requirements.txt
            fi
        elif [[ -f "go.mod" ]]; then
            echo -e "${BLUE}🏗️  Building Go project...${NC}"
            go mod download
            go build
        elif [[ -f "Cargo.toml" ]]; then
            echo -e "${BLUE}🦀 Building Rust project...${NC}"
            cargo build
        fi
        
        # Run tests if available
        if [[ -f "package.json" ]] && npm run test >/dev/null 2>&1; then
            echo -e "${GREEN}🧪 Running tests...${NC}"
            npm test
        elif [[ -f "requirements.txt" ]] && python -m pytest >/dev/null 2>&1; then
            echo -e "${GREEN}🧪 Running tests...${NC}"
            python -m pytest
        fi
    fi
}

queue_task() {
    local prompt=$1
    echo "$prompt" >> "$TASK_QUEUE"
    echo -e "${GREEN}✅ Task queued${NC}"
}

process_queue() {
    local budget=${1:-$DEFAULT_BUDGET}
    local total_cost=0
    local task_count=0
    local success_count=0
    
    if [[ ! -f "$TASK_QUEUE" ]]; then
        echo -e "${YELLOW}⚠️  No tasks in queue${NC}"
        return 0
    fi
    
    echo -e "${BLUE}📋 Processing queue with budget: \$$budget${NC}"
    
    while IFS= read -r task && (( $(bc -l <<< "$total_cost < $budget") )); do
        ((task_count++))
        
        echo -e "\n${CYAN}Task $task_count:${NC} $task"
        echo -e "${YELLOW}Current spend: \$$total_cost${NC}"
        
        if execute_task "$task" "" "" "" "" "" "false"; then
            ((success_count++))
            # Update cost
            local last_cost=$(tail -1 "$USAGE_LOG" | cut -d',' -f5)
            total_cost=$(bc -l <<< "$total_cost + $last_cost")
        fi
    done < "$TASK_QUEUE"
    
    echo -e "\n${GREEN}📊 Queue processing complete${NC}"
    echo -e "${CYAN}Tasks processed: $task_count${NC}"
    echo -e "${GREEN}Successful: $success_count${NC}"
    echo -e "${YELLOW}Total cost: \$$total_cost${NC}"
    
    # Clear queue
    > "$TASK_QUEUE"
}

smart_execute() {
    local prompt=$1
    
    # Analyze project context
    local project_size=$(find . -name "*.py" -o -name "*.js" -o -name "*.ts" | wc -l)
    
    # Adjust strategy based on project
    if ((project_size > 100)); then
        # Large project - prefer balanced for most tasks
        echo -e "${BLUE}📊 Large project detected (${project_size} files)${NC}"
        execute_task "$prompt" "balanced" "" "false"
    elif ((project_size > 20)); then
        # Medium project - mixed approach
        echo -e "${BLUE}📊 Medium project detected (${project_size} files)${NC}"
        execute_task "$prompt" "" "" "false"
    else
        # Small project - prefer local for speed
        echo -e "${BLUE}📊 Small project detected (${project_size} files)${NC}"
        execute_task "$prompt" "" "" "true"
    fi
}

analyze_usage() {
    if [[ ! -f "$USAGE_LOG" ]]; then
        echo -e "${YELLOW}⚠️  No usage data available${NC}"
        return 0
    fi
    
    echo -e "${BLUE}📊 Usage Analysis${NC}"
    echo -e "${CYAN}==================${NC}"
    
    # Calculate stats
    local total_tasks=$(wc -l < "$USAGE_LOG")
    local total_cost=$(awk -F',' '{sum += $5} END {print sum}' "$USAGE_LOG")
    local success_rate=$(awk -F',' '$6 == "true" {good++} END {print good/NR*100}' "$USAGE_LOG")
    
    echo -e "${GREEN}Total tasks:${NC} $total_tasks"
    echo -e "${GREEN}Total cost:${NC} \$$total_cost"
    echo -e "${GREEN}Success rate:${NC} ${success_rate}%"
    
    # Task distribution
    echo -e "\n${CYAN}Task Distribution:${NC}"
    awk -F',' '{counts[$2]++} END {for (task in counts) print "  " task ": " counts[task]}' "$USAGE_LOG" | sort -k2 -nr
    
    # Tier distribution
    echo -e "\n${CYAN}Tier Distribution:${NC}"
    awk -F',' '{counts[$3]++} END {for (tier in counts) print "  " tier ": " counts[tier]}' "$USAGE_LOG" | sort -k2 -nr
    
    # Recent activity
    echo -e "\n${CYAN}Recent Activity (last 10):${NC}"
    tail -10 "$USAGE_LOG" | while IFS=',' read -r timestamp task tier provider cost success; do
        local status_icon="✅"
        if [[ "$success" != "true" ]]; then
            status_icon="❌"
        fi
        echo "  $status_icon $task ($tier) - \$$cost"
    done
}

optimize_workflow() {
    echo -e "${BLUE}🔧 Workflow Optimization${NC}"
    echo -e "${CYAN}=======================${NC}"
    
    if [[ ! -f "$USAGE_LOG" ]]; then
        echo -e "${YELLOW}⚠️  No usage data available for optimization${NC}"
        return 0
    fi
    
    # Analyze patterns
    local premium_usage=$(awk -F',' '$3 == "premium" {count++} END {print count+0}' "$USAGE_LOG")
    local total_tasks=$(wc -l < "$USAGE_LOG")
    local premium_ratio=$(echo "scale=2; $premium_usage / $total_tasks * 100" | bc)
    
    local total_cost=$(awk -F',' '{sum += $5} END {print sum}' "$USAGE_LOG")
    local avg_cost=$(echo "scale=4; $total_cost / $total_tasks" | bc)
    
    # Suggestions
    echo -e "${YELLOW}💡 Optimization Suggestions:${NC}"
    
    if (( $(echo "$premium_ratio > 30" | bc -l) )); then
        echo -e "  • Consider using balanced tier for non-critical tasks (premium usage: ${premium_ratio}%)"
    fi
    
    if (( $(echo "$avg_cost > 0.02" | bc -l) )); then
        echo -e "  • Average cost is high (\$$avg_cost), try using more local models"
    fi
    
    # Check most common tasks
    local most_common=$(awk -F',' '{counts[$2]++} END {max=0; task=""; for (t in counts) if (counts[t] > max) {max=counts[t]; task=t} print task}' "$USAGE_LOG")
    echo -e "  • Most common task type: $most_common - consider creating templates"
    
    # Check failure rate
    local failure_rate=$(awk -F',' '$6 == "false" {bad++} END {print bad/NR*100}' "$USAGE_LOG")
    if (( $(echo "$failure_rate > 20" | bc -l) )); then
        echo -e "  • High failure rate (${failure_rate}%) - try breaking down complex tasks"
    fi
}

run_workflow() {
    local workflow=$1
    
    echo -e "${BLUE}🔄 Running workflow: $workflow${NC}"
    
    case $workflow in
        "fullstack")
            echo -e "${CYAN}Generating full-stack application...${NC}"
            execute_task "Design full-stack architecture with React frontend, Node.js backend, PostgreSQL database, and Docker deployment" "premium" "" "" "true" "fullstack-app"
            execute_task "Implement React frontend with TypeScript, routing, and state management" "balanced" "" "" "true" "fullstack-app/frontend"
            execute_task "Create Node.js Express API with authentication and CRUD operations" "balanced" "" "" "true" "fullstack-app/backend"
            execute_task "Add comprehensive tests and documentation" "cheap" "" "" "true" "fullstack-app"
            ;;
        "cli")
            echo -e "${CYAN}Generating CLI tool...${NC}"
            execute_task "Create a Python CLI tool with Click framework, configuration management, and comprehensive help" "balanced" "" "" "true" "cli-tool"
            execute_task "Add unit tests and integration tests" "cheap" "" "" "true" "cli-tool"
            execute_task "Create documentation and usage examples" "cheap" "" "" "true" "cli-tool"
            ;;
        "api")
            echo -e "${CYAN}Generating REST API...${NC}"
            execute_task "Design REST API architecture with proper endpoints, authentication, and error handling" "balanced" "" "" "true" "rest-api"
            execute_task "Implement FastAPI backend with SQLAlchemy ORM and Pydantic models" "balanced" "" "" "true" "rest-api"
            execute_task "Add comprehensive API documentation with OpenAPI/Swagger" "balanced" "" "" "true" "rest-api"
            execute_task "Create database migrations and seed data" "cheap" "" "" "true" "rest-api"
            ;;
        "mobile")
            echo -e "${CYAN}Generating mobile app...${NC}"
            execute_task "Design mobile app architecture with Flutter, state management, and API integration" "premium" "" "" "true" "mobile-app"
            execute_task "Implement Flutter UI with responsive design and navigation" "balanced" "" "" "true" "mobile-app"
            execute_task "Add local storage, notifications, and offline support" "balanced" "" "" "true" "mobile-app"
            ;;
        "refactor")
            echo -e "${CYAN}Running refactoring workflow...${NC}"
            execute_task "Analyze codebase for refactoring opportunities and technical debt" "balanced" "" "" "false"
            execute_task "Refactor code to improve maintainability and follow best practices" "premium" "" "" "true"
            execute_task "Add comprehensive tests for refactored code" "balanced" "" "" "true"
            ;;
        "test")
            echo -e "${CYAN}Adding comprehensive tests...${NC}"
            execute_task "Analyze existing code to identify test coverage gaps" "balanced" "" "" "false"
            execute_task "Generate unit tests for all functions and methods" "balanced" "" "" "true"
            execute_task "Add integration tests for API endpoints and database operations" "balanced" "" "" "true"
            execute_task "Create end-to-end tests for critical user flows" "premium" "" "" "true"
            ;;
        *)
            echo -e "${RED}❌ Unknown workflow: $workflow${NC}"
            echo "Available: fullstack, cli, api, mobile, refactor, test"
            return 1
            ;;
    esac
    
    echo -e "${GREEN}✅ Workflow completed!${NC}"
}

# Parse arguments
FORCE_TIER=""
FORCE_PROVIDER=""
PREFER_LOCAL=false
EXECUTE_CODE=false
OUTPUT_DIR=""
BUDGET=""
QUIET=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tier)
            FORCE_TIER="$2"
            shift 2
            ;;
        -p|--provider)
            FORCE_PROVIDER="$2"
            shift 2
            ;;
        -l|--local)
            PREFER_LOCAL=true
            shift
            ;;
        -e|--execute)
            EXECUTE_CODE=true
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
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
            print_usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Check command
COMMAND=${1:-""}
shift || true

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    echo -e "${RED}❌ LLX is not installed or not in PATH${NC}"
    exit 1
fi

# Execute command
case $COMMAND in
    "execute")
        if [[ -z "$1" ]]; then
            echo -e "${RED}❌ Missing prompt${NC}"
            exit 1
        fi
        execute_task "$1" "$FORCE_TIER" "$FORCE_PROVIDER" "$PREFER_LOCAL" "$EXECUTE_CODE" "$OUTPUT_DIR" "$QUIET"
        ;;
    "queue")
        if [[ -z "$1" ]]; then
            echo -e "${RED}❌ Missing prompt${NC}"
            exit 1
        fi
        queue_task "$1"
        ;;
    "process")
        process_queue "${BUDGET:-$DEFAULT_BUDGET}"
        ;;
    "smart")
        if [[ -z "$1" ]]; then
            echo -e "${RED}❌ Missing prompt${NC}"
            exit 1
        fi
        smart_execute "$1"
        ;;
    "analyze")
        analyze_usage
        ;;
    "optimize")
        optimize_workflow
        ;;
    "workflow")
        if [[ -z "$1" ]]; then
            echo -e "${RED}❌ Missing workflow name${NC}"
            exit 1
        fi
        run_workflow "$1"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        print_usage
        exit 1
        ;;
esac
