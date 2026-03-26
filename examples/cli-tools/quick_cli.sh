#!/bin/bash
# One-liner CLI tool generator using LLX

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Tool categories
declare -A TOOL_CATEGORIES=(
    ["system"]="System Administration Tools"
    ["dev"]="Development Tools"
    ["data"]="Data Processing Tools"
    ["network"]="Network Tools"
    ["security"]="Security Tools"
    ["automation"]="Automation Tools"
    ["utility"]="General Utilities"
    ["web"]="Web/API Tools"
)

# Pre-defined templates
declare -A TEMPLATES=(
    ["file-manager"]="A file manager with CRUD operations and search"
    ["log-analyzer"]="A log parser and analyzer with statistics"
    ["backup-tool"]="An automated backup tool with compression"
    ["process-monitor"]="A process monitoring and management tool"
    ["api-client"]="A REST API client with authentication"
    ["task-runner"]="A task runner with configuration file support"
    ["config-manager"]="A configuration file manager and validator"
    ["password-generator"]="A secure password generator with options"
)

print_usage() {
    echo -e "${BLUE}LLX CLI Tool Generator${NC}"
    echo -e "${CYAN}Generate command-line tools with a single command!${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS] <tool-type> <tool-name>"
    echo ""
    echo "Tool Types:"
    for category in "${!TOOL_CATEGORIES[@]}"; do
        echo -e "  ${YELLOW}$category${NC} - ${TOOL_CATEGORIES[$category]}"
    done
    echo ""
    echo "Templates (use with --template):"
    for template in "${!TEMPLATES[@]}"; do
        echo -e "  ${PURPLE}$template${NC} - ${TEMPLATES[$template]}"
    done
    echo ""
    echo "Options:"
    echo "  -t, --tier TIER        Model tier (cheap/balanced/premium) [default: balanced]"
    echo "  -p, --provider PROVIDER LLM provider (anthropic/openai/openrouter)"
    echo "  -l, --local            Use local models"
    echo "  --template TEMPLATE    Use predefined template"
    echo "  --gui                 Include GUI/TUI interface"
    echo "  --api                 Add API integration"
    echo "  --db                  Include database support"
    echo "  --test                Generate with tests"
    echo "  --docker              Include Docker configuration"
    echo "  -e, --execute         Execute/setup after generation"
    echo "  -h, --help            Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 system log-parser                    # System log parser"
    echo "  $0 dev api-client --api --test          # API client with tests"
    echo "  $0 --template file-manager my-files    # Use template"
    echo "  $0 data csv-processor --gui --db       # CSV tool with GUI and DB"
    echo "  $0 automation deployer --docker -e     # Deployment tool with Docker"
}

generate_tool() {
    local tool_type=$1
    local tool_name=$2
    local tier=${3:-"balanced"}
    local provider=${4:-""}
    local local_model=${5:-false}
    local template=${6:-""}
    local has_gui=${7:-false}
    local has_api=${8:-false}
    local has_db=${9:-false}
    local has_test=${10:-false}
    local has_docker=${11:-false}
    local execute=${12:-false}
    
    echo -e "${BLUE}🔧 Generating $tool_type tool: $tool_name${NC}"
    
    # Create directory
    mkdir -p "$tool_name"
    cd "$tool_name"
    
    # Build prompt based on type and options
    local prompt=""
    
    if [ -n "$template" ] && [ -n "${TEMPLATES[$template]}" ]; then
        prompt="Create ${TEMPLATES[$template]}"
    else
        case $tool_type in
            "system")
                prompt="Create a system administration CLI tool"
                ;;
            "dev")
                prompt="Create a development tool for programmers"
                ;;
            "data")
                prompt="Create a data processing CLI tool"
                ;;
            "network")
                prompt="Create a network management CLI tool"
                ;;
            "security")
                prompt="Create a security-focused CLI tool"
                ;;
            "automation")
                prompt="Create an automation CLI tool"
                ;;
            "utility")
                prompt="Create a general utility CLI tool"
                ;;
            "web")
                prompt="Create a web/API CLI tool"
                ;;
            *)
                prompt="Create a command-line tool"
                ;;
        esac
    fi
    
    # Add features based on options
    prompt="$prompt called '$tool_name' with:"
    prompt="$prompt
- Command-line interface with proper argument parsing
- Help documentation and usage examples
- Error handling and validation
- Colored output and progress indicators
- Configuration file support (YAML/TOML)
- Logging with different levels"
    
    if [ "$has_gui" = true ]; then
        prompt="$prompt
- GUI/TUI interface (use Rich for Python, ncurses for C/C++, or Inquirer.js for Node)"
    fi
    
    if [ "$has_api" = true ]; then
        prompt="$prompt
- REST API integration with authentication
- Request/response handling and error retry
- API key management and rate limiting"
    fi
    
    if [ "$has_db" = true ]; then
        prompt="$prompt
- Database support (SQLite for Python, Postgres recommended)
- ORM integration (SQLAlchemy for Python, Prisma for Node)"
    fi
    
    if [ "$has_test" = true ]; then
        prompt="$prompt
- Comprehensive unit tests
- Integration tests where applicable
- Test coverage reporting"
    fi
    
    if [ "$has_docker" = true ]; then
        prompt="$prompt
- Dockerfile for containerization
- docker-compose.yml for development
- Multi-stage builds for production"
    fi
    
    prompt="$prompt

Requirements:
1. Create a working, executable tool
2. Include all necessary files (requirements.txt, package.json, etc.)
3. Add clear setup and usage instructions in README.md
4. Make it production-ready with proper structure
5. Include examples and documentation
6. Ensure cross-platform compatibility if applicable"
    
    # Build LLX command
    local cmd=""
    
    if [ "$local_model" = true ]; then
        cmd="llx chat --local --task refactor"
    else
        cmd="llx chat --model "$tier" --task refactor"
    fi
    
    if [ -n "$provider" ]; then
        cmd="$cmd --provider $provider"
    fi
    
    cmd="$cmd --prompt \"$prompt\""
    
    # Execute generation
    echo -e "${CYAN}Executing: $cmd${NC}"
    
    if eval "$cmd" > generation.log 2>&1; then
        echo -e "${GREEN}✅ Tool generated successfully!${NC}"
        
        # Show generated files
        echo -e "${BLUE}Generated files:${NC}"
        find . -maxdepth 2 -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.sh" -o -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" \) | sort
        
        # Setup if requested
        if [ "$execute" = true ]; then
            setup_tool
        fi
        
        echo -e "${GREEN}🎉 Your CLI tool is ready in: $(pwd)${NC}"
    else
        echo -e "${RED}❌ Generation failed! Check generation.log${NC}"
        tail -20 generation.log
        exit 1
    fi
    
    rm -f generation.log
}

setup_tool() {
    echo -e "${BLUE}🔧 Setting up tool...${NC}"
    
    # Detect language and setup
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}Setting up Python environment...${NC}"
        python3 -m venv venv 2>/dev/null || python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        echo -e "${GREEN}✓ Python environment ready${NC}"
    elif [ -f "package.json" ]; then
        echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
        npm install
        echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
    elif [ -f "go.mod" ]; then
        echo -e "${YELLOW}Installing Go modules...${NC}"
        go mod download
        go build
        echo -e "${GREEN}✓ Go application built${NC}"
    elif [ -f "Cargo.toml" ]; then
        echo -e "${YELLOW}Building Rust application...${NC}"
        cargo build --release
        echo -e "${GREEN}✓ Rust application built${NC}"
    fi
    
    # Make executable if it's a script
    if [ -f "${PWD##*/}.sh" ]; then
        chmod +x "${PWD##*/}.sh"
        echo -e "${GREEN}✓ Script made executable${NC}"
    fi
    
    # Run tests if they exist
    if [ -f "requirements.txt" ] && [ -d "tests" ]; then
        echo -e "${YELLOW}Running tests...${NC}"
        source venv/bin/activate
        python -m pytest 2>/dev/null || echo "Tests completed (some may have failed)"
    fi
    
    echo -e "${GREEN}✅ Setup complete!${NC}"
}

# Quick generate common tools
quick_generate() {
    local tool=$1
    local name=$2
    
    case $tool in
        "json-processor")
            generate_tool "utility" "$name" "cheap" "" false "" false false false false false true
            ;;
        "file-watcher")
            generate_tool "utility" "$name" "balanced" "" false "" false false false false false true
            ;;
        "port-scanner")
            generate_tool "network" "$name" "cheap" "" false "" false false false false false true
            ;;
        "log-parser")
            generate_tool "system" "$name" "balanced" "" false "" false false false false false true
            ;;
        "api-tester")
            generate_tool "web" "$name" "balanced" "" false "" true false false false false true
            ;;
        "db-manager")
            generate_tool "data" "$name" "premium" "" false "" false true false false false true
            ;;
        "system-monitor")
            generate_tool "system" "$name" "balanced" "" false "" true false false false false true
            ;;
        "password-manager")
            generate_tool "security" "$name" "premium" "" false "" false true false false false true
            ;;
        *)
            echo -e "${RED}Unknown quick tool: $tool${NC}"
            echo "Available: json-processor, file-watcher, port-scanner, log-parser, api-tester, db-manager, system-monitor, password-manager"
            exit 1
            ;;
    esac
}

# Parse arguments
TIER="balanced"
PROVIDER=""
LOCAL=false
TEMPLATE=""
GUI=false
API=false
DB=false
TEST=false
DOCKER=false
EXECUTE=false

while [[ $# -gt 0 ]]; do
    case $1 in
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
        --template)
            TEMPLATE="$2"
            shift 2
            ;;
        --gui)
            GUI=true
            shift
            ;;
        --api)
            API=true
            shift
            ;;
        --db)
            DB=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        --docker)
            DOCKER=true
            shift
            ;;
        -e|--execute)
            EXECUTE=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Check for quick generation
if [ "$QUICK" = true ]; then
    if [ $# -lt 2 ]; then
        echo -e "${RED}Quick generation requires: --quick <tool-type> <name>${NC}"
        exit 1
    fi
    quick_generate "$2" "$3"
    exit 0
fi

# Validate arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Missing required arguments${NC}"
    print_usage
    exit 1
fi

TOOL_TYPE=$1
TOOL_NAME=$2

# Validate tool type
if [ -z "${TOOL_CATEGORIES[$TOOL_TYPE]}" ] && [ -z "$TEMPLATE" ]; then
    echo -e "${RED}Invalid tool type: $TOOL_TYPE${NC}"
    echo -e "${YELLOW}Valid types: ${!TOOL_CATEGORIES[*]}${NC}"
    exit 1
fi

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    echo -e "${RED}LLX is not installed or not in PATH${NC}"
    exit 1
fi

# Generate the tool
generate_tool "$TOOL_TYPE" "$TOOL_NAME" "$TIER" "$PROVIDER" "$LOCAL" "$TEMPLATE" "$GUI" "$API" "$DB" "$TEST" "$DOCKER" "$EXECUTE"

echo -e "\n${CYAN}Next steps:${NC}"
echo "1. cd $TOOL_NAME"
echo "2. Review the generated code"
echo "3. Customize as needed"
echo "4. Check README.md for usage instructions"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
