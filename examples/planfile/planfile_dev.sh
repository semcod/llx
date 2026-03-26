#!/bin/bash
# Planfile-Driven Strategic Refactoring Script
# Automates comprehensive refactoring using LLX planfile integration

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
DEFAULT_SPRINTS=3
DEFAULT_FOCUS="complexity"
DEFAULT_MODEL="auto"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PLANFILE_DIR="$PROJECT_ROOT/.llx/planfile"
METRICS_DIR="$PROJECT_ROOT/.code2llm"

# Ensure directories exist
mkdir -p "$PLANFILE_DIR"
mkdir -p "$METRICS_DIR"

# Helper function to run LLX with proper PYTHONPATH
run_llx() {
    if command -v llx &> /dev/null; then
        llx "$@"
    else
        PYTHONPATH=/home/tom/github/semcod/llx python3 -m llx "$@"
    fi
}

# Focus area mappings
declare -A FOCUS_DESCRIPTIONS=(
    ["complexity"]="Reduce cyclomatic complexity and improve code structure"
    ["duplication"]="Eliminate code duplication and improve reusability"
    ["tests"]="Improve test coverage and test quality"
    ["docs"]="Enhance documentation and code comments"
)

# Model recommendations by focus
declare -A FOCUS_MODELS=(
    ["complexity"]="claude-opus-4"
    ["duplication"]="claude-sonnet-4"
    ["tests"]="claude-sonnet-4"
    ["docs"]="qwen2.5-coder:7b"
)

# Helper functions
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          Planfile-Driven Strategic Refactoring             ║"
    echo "║                 Powered by LLX                             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo "  generate    Generate a refactoring strategy"
    echo "  review      Review strategy quality gates"
    echo "  apply       Execute a strategy"
    echo "  status      Show execution status"
    echo "  resume      Resume interrupted execution"
    echo "  clean       Clean generated files"
    echo ""
    echo -e "${YELLOW}Generate Options:${NC}"
    echo "  --focus AREA       Focus area: complexity, duplication, tests, docs"
    echo "  --sprints N        Number of sprints (default: 3)"
    echo "  --model MODEL      LLM model (default: auto-select)"
    echo "  --output FILE      Output file (default: strategy-<focus>-<timestamp>.yaml)"
    echo ""
    echo -e "${YELLOW}Apply Options:${NC}"
    echo "  --strategy FILE    Strategy file to apply"
    echo "  --sprint ID        Specific sprint to execute"
    echo "  --dry-run          Simulate execution"
    echo "  --task NAME        Execute specific task only"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 generate --focus complexity --sprints 4"
    echo "  $0 apply --strategy strategy-complexity.yaml"
    echo "  $0 apply --strategy strategy.yaml --sprint sprint-2 --dry-run"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate strategy
generate_strategy() {
    local focus="$1"
    local sprints="$2"
    local model="$3"
    local output="$4"
    
    log_info "Generating refactoring strategy..."
    echo "  Focus: ${FOCUS_DESCRIPTIONS[$focus]}"
    echo "  Sprints: $sprints"
    echo "  Model: $model"
    
    # Analyze current state first
    log_info "Analyzing current project state..."
    run_llx analyze "$PROJECT_ROOT" --toon-dir "$METRICS_DIR" --task "$focus" > "$PLANFILE_DIR/current-analysis.txt"
    
    # Select model if auto
    if [[ "$model" == "auto" ]]; then
        model="${FOCUS_MODELS[$focus]}"
        log_info "Auto-selected model: $model"
    fi
    
    # Generate strategy
    log_info "Generating strategy with LLM..."
    run_llx plan generate "$PROJECT_ROOT" \
        --model "$model" \
        --sprints "$sprints" \
        --focus "$focus" \
        --output "$output"
    
    log_success "Strategy generated: $output"
    
    # Show summary
    echo ""
    echo -e "${CYAN}Strategy Summary:${NC}"
    yq eval '.sprints | length' "$output" | xargs echo "  Sprints:"
    yq eval '.sprints[].task_patterns | length' "$output" | paste -sd+ | bc | xargs echo "  Total tasks:"
    yq eval '.description' "$output" | sed 's/^/  /'
}

# Review strategy
review_strategy() {
    local strategy_file="$1"
    
    if [[ ! -f "$strategy_file" ]]; then
        log_error "Strategy file not found: $strategy_file"
        exit 1
    fi
    
    log_info "Reviewing strategy quality gates..."
    
    # Show strategy overview
    echo ""
    echo -e "${CYAN}Strategy Overview:${NC}"
    yq eval '.description' "$strategy_file" | sed 's/^/  /'
    echo ""
    
    # Show sprints
    echo -e "${CYAN}Sprints:${NC}"
    yq eval '.sprints[] | "  - \(.id): \(.name) (\(.task_patterns | length) tasks)"' "$strategy_file"
    echo ""
    
    # Run quality gate review
    run_llx plan review "$strategy_file" "$PROJECT_ROOT"
    
    # Estimate execution cost
    echo ""
    log_info "Estimating execution cost..."
    local task_count=$(yq eval '.sprints[].task_patterns | length' "$strategy_file" | paste -sd+ | bc)
    echo "  Estimated tasks: $task_count"
    echo "  Estimated cost: \$$(echo "$task_count * 0.02" | bc -l) (rough estimate)"
}

# Apply strategy
apply_strategy() {
    local strategy_file="$1"
    local sprint_id="$2"
    local dry_run="$3"
    local task_name="$4"
    
    if [[ ! -f "$strategy_file" ]]; then
        log_error "Strategy file not found: $strategy_file"
        exit 1
    fi
    
    # Prepare apply command
    local cmd="llx plan apply $strategy_file $PROJECT_ROOT"
    
    if [[ -n "$sprint_id" ]]; then
        cmd="$cmd --sprint $sprint_id"
        log_info "Executing sprint: $sprint_id"
    fi
    
    if [[ "$dry_run" == "true" ]]; then
        cmd="$cmd --dry-run"
        log_warning "DRY RUN MODE - No changes will be made"
    fi
    
    # Create backup before execution
    if [[ "$dry_run" != "true" ]]; then
        log_info "Creating backup..."
        backup_dir="$PLANFILE_DIR/backups/$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$backup_dir"
        cp -r "$PROJECT_ROOT/src" "$backup_dir/" 2>/dev/null || true
        cp "$strategy_file" "$backup_dir/"
        log_success "Backup created: $backup_dir"
    fi
    
    # Execute strategy
    log_info "Executing strategy..."
    echo "  Command: $cmd"
    echo ""
    
    eval "$cmd"
    
    # Post-execution validation
    if [[ "$dry_run" != "true" ]]; then
        echo ""
        log_info "Post-execution validation..."
        
        # Analyze changes
        llx analyze "$PROJECT_ROOT" --toon-dir "$METRICS_DIR" > "$PLANFILE_DIR/post-execution-analysis.txt"
        
        # Compare metrics
        echo ""
        echo -e "${CYAN}Metrics Comparison:${NC}"
        echo "  Pre-execution: $(cat "$PLANFILE_DIR/current-analysis.txt" | grep -E "(CC|Files|Lines)" | head -3)"
        echo "  Post-execution: $(cat "$PLANFILE_DIR/post-execution-analysis.txt" | grep -E "(CC|Files|Lines)" | head -3)"
        
        # Run tests if available
        if [[ -f "$PROJECT_ROOT/pyproject.toml" ]] || [[ -f "$PROJECT_ROOT/package.json" ]]; then
            log_info "Running tests..."
            if command -v pytest &> /dev/null; then
                pytest "$PROJECT_ROOT" --tb=short || log_warning "Some tests failed"
            fi
        fi
        
        log_success "Strategy execution completed!"
    fi
}

# Show execution status
show_status() {
    echo -e "${CYAN}Execution Status:${NC}"
    echo ""
    
    # List strategies
    if [[ -n "$(find "$PLANFILE_DIR" -name "strategy-*.yaml" 2>/dev/null)" ]]; then
        echo "Generated Strategies:"
        find "$PLANFILE_DIR" -name "strategy-*.yaml" -exec basename {} \; | sort | sed 's/^/  - /'
        echo ""
    fi
    
    # Show recent executions
    if [[ -f "$PLANFILE_DIR/execution.log" ]]; then
        echo "Recent Executions:"
        tail -10 "$PLANFILE_DIR/execution.log" | sed 's/^/  /'
        echo ""
    fi
    
    # Current metrics
    if [[ -f "$PLANFILE_DIR/current-analysis.txt" ]]; then
        echo "Current Metrics:"
        grep -E "(CC|Files|Lines|Functions)" "$PLANFILE_DIR/current-analysis.txt" | sed 's/^/  /'
    fi
}

# Resume interrupted execution
resume_execution() {
    local strategy_file="$1"
    
    if [[ -z "$strategy_file" ]]; then
        # Find most recent strategy
        strategy_file=$(find "$PLANFILE_DIR" -name "strategy-*.yaml" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    fi
    
    if [[ ! -f "$strategy_file" ]]; then
        log_error "No strategy file found to resume"
        exit 1
    fi
    
    log_info "Resuming execution from: $strategy_file"
    
    # Find last completed sprint
    local last_sprint=""
    if [[ -f "$PLANFILE_DIR/execution-state.json" ]]; then
        last_sprint=$(jq -r '.last_sprint' "$PLANFILE_DIR/execution-state.json")
    fi
    
    # Find next sprint
    local next_sprint=$(yq eval ".sprints[] | select(.id > \"$last_sprint\") | .id" "$strategy_file" | head -1)
    
    if [[ -n "$next_sprint" ]]; then
        log_info "Resuming with sprint: $next_sprint"
        apply_strategy "$strategy_file" "$next_sprint" "false" ""
    else
        log_success "All sprints already completed"
    fi
}

# Clean generated files
clean_files() {
    echo -e "${YELLOW}This will remove all generated planfile files. Continue? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$PLANFILE_DIR"
        log_success "Cleaned generated files"
    fi
}

# Main execution
main() {
    print_banner
    
    # Parse command
    case "${1:-}" in
        "generate")
            shift
            focus="$DEFAULT_FOCUS"
            sprints="$DEFAULT_SPRINTS"
            model="$DEFAULT_MODEL"
            output=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --focus) focus="$2"; shift 2 ;;
                    --sprints) sprints="$2"; shift 2 ;;
                    --model) model="$2"; shift 2 ;;
                    --output) output="$2"; shift 2 ;;
                    *) log_error "Unknown option: $1"; exit 1 ;;
                esac
            done
            
            # Generate output filename if not provided
            if [[ -z "$output" ]]; then
                timestamp=$(date +%Y%m%d-%H%M%S)
                output="$PLANFILE_DIR/strategy-${focus}-${timestamp}.yaml"
            fi
            
            generate_strategy "$focus" "$sprints" "$model" "$output"
            ;;
            
        "review")
            shift
            strategy_file="$1"
            if [[ -z "$strategy_file" ]]; then
                strategy_file=$(find "$PLANFILE_DIR" -name "strategy-*.yaml" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
            fi
            review_strategy "$strategy_file"
            ;;
            
        "apply")
            shift
            strategy_file=""
            sprint_id=""
            dry_run="false"
            task_name=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --strategy) strategy_file="$2"; shift 2 ;;
                    --sprint) sprint_id="$2"; shift 2 ;;
                    --dry-run) dry_run="true"; shift ;;
                    --task) task_name="$2"; shift 2 ;;
                    *) log_error "Unknown option: $1"; exit 1 ;;
                esac
            done
            
            if [[ -z "$strategy_file" ]]; then
                strategy_file=$(find "$PLANFILE_DIR" -name "strategy-*.yaml" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
            fi
            
            apply_strategy "$strategy_file" "$sprint_id" "$dry_run" "$task_name"
            ;;
            
        "status")
            show_status
            ;;
            
        "resume")
            shift
            resume_execution "$1"
            ;;
            
        "clean")
            clean_files
            ;;
            
        "help"|"--help"|"-h"|"")
            print_usage
            ;;
            
        *)
            log_error "Unknown command: $1"
            print_usage
            exit 1
            ;;
    esac
}

# Log execution
log_execution() {
    local cmd="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $cmd" >> "$PLANFILE_DIR/execution.log"
}

# Execute main with logging
if [[ "$1" != "help" && "$1" != "--help" && "$1" != "-h" && -n "$1" ]]; then
    log_execution "$*"
fi

main "$@"
