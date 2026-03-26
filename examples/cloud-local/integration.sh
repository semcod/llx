#!/bin/bash
# Cloud-Local Integration Script
# Automates workflows combining cloud LLMs with local tools

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Tool configurations
AIDER_AVAILABLE=false
CLAUDE_CODE_AVAILABLE=false
VSCODE_AVAILABLE=false

# Check tool availability
check_tools() {
    echo -e "${BLUE}🔧 Checking tool availability...${NC}"
    
    if command -v aider &> /dev/null; then
        AIDER_AVAILABLE=true
        echo -e "${GREEN}✅ Aider available${NC}"
    else
        echo -e "${YELLOW}⚠️  Aider not found${NC}"
    fi
    
    if command -v claude-code &> /dev/null || docker run --rm anthropic/claude-code --version &> /dev/null 2>&1; then
        CLAUDE_CODE_AVAILABLE=true
        echo -e "${GREEN}✅ Claude Code available${NC}"
    else
        echo -e "${YELLOW}⚠️  Claude Code not found${NC}"
    fi
    
    if command -v code &> /dev/null; then
        VSCODE_AVAILABLE=true
        echo -e "${GREEN}✅ VS Code available${NC}"
    else
        echo -e "${YELLOW}⚠️  VS Code not found${NC}"
    fi
}

# Tool selection based on task type
select_tool() {
    local task_type=$1
    local prompt=$2
    
    case $task_type in
        "implementation"|"coding"|"refactor")
            if [[ "$AIDER_AVAILABLE" == "true" ]]; then
                echo "aider"
            else
                echo "llx"
            fi
            ;;
        "architecture"|"design"|"complex")
            if [[ "$CLAUDE_CODE_AVAILABLE" == "true" ]]; then
                echo "claude-code"
            else
                echo "llx-premium"
            fi
            ;;
        "ui"|"frontend"|"interactive")
            if [[ "$VSCODE_AVAILABLE" == "true" ]]; then
                echo "vscode"
            else
                echo "llx"
            fi
            ;;
        "simple"|"quick"|"test"|"docs")
            echo "llx-local"
            ;;
        *)
            echo "llx"
            ;;
    esac
}

# Execute task with selected tool
execute_with_tool() {
    local tool=$1
    local prompt=$2
    local tier=$3
    local execute=$4
    
    echo -e "${CYAN}🔨 Using tool: $tool${NC}"
    
    case $tool in
        "aider")
            if [[ "$AIDER_AVAILABLE" == "true" ]]; then
                echo -e "${BLUE}🤖 Running Aider...${NC}"
                aider --message="$prompt" .
            else
                echo -e "${RED}❌ Aider not available, falling back to LLX${NC}"
                llx chat --model "${tier:-balanced}" --prompt "$prompt"
            fi
            ;;
        "claude-code")
            if [[ "$CLAUDE_CODE_AVAILABLE" == "true" ]]; then
                echo -e "${BLUE}🧠 Running Claude Code...${NC}"
                if command -v claude-code &> /dev/null; then
                    claude-code "$prompt"
                else
                    docker run -it --rm -v "$(pwd):/workspace" anthropic/claude-code "$prompt"
                fi
            else
                echo -e "${RED}❌ Claude Code not available, falling back to LLX${NC}"
                llx chat --model premium --prompt "$prompt"
            fi
            ;;
        "vscode")
            if [[ "$VSCODE_AVAILABLE" == "true" ]]; then
                echo -e "${BLUE}💻 Opening VS Code...${NC}"
                echo -e "${YELLOW}💡 Use RooCode extension for: $prompt${NC}"
                code .
                echo -e "${CYAN}Press Enter when VS Code work is complete...${NC}"
                read -r
            else
                echo -e "${RED}❌ VS Code not available, falling back to LLX${NC}"
                llx chat --model "${tier:-balanced}" --prompt "$prompt"
            fi
            ;;
        "llx-local")
            echo -e "${BLUE}🏠 Using local LLX...${NC}"
            llx chat --local --prompt "$prompt"
            ;;
        "llx-premium")
            echo -e "${BLUE}☁️  Using premium LLX...${NC}"
            llx chat --model premium --prompt "$prompt"
            ;;
        *)
            echo -e "${BLUE}🤖 Using LLX...${NC}"
            llx chat --model "${tier:-balanced}" --prompt "$prompt"
            ;;
    esac
}

# Classify task type
classify_task() {
    local prompt=$1
    local prompt_lower=$(echo "$prompt" | tr '[:upper:]' '[:lower:]')
    
    # Check for architecture/design keywords
    if [[ "$prompt_lower" =~ (architecture|design|system|scalable|complex|pattern) ]]; then
        echo "architecture"
    # Check for implementation keywords
    elif [[ "$prompt_lower" =~ (implement|code|function|class|method|refactor|fix|add|create|build) ]]; then
        echo "implementation"
    # Check for UI keywords
    elif [[ "$prompt_lower" =~ (ui|frontend|component|interface|visual|interactive|debug|explore) ]]; then
        echo "ui"
    # Check for simple tasks
    elif [[ "$prompt_lower" =~ (test|document|format|lint|simple|quick|minor|typo|comment) ]]; then
        echo "simple"
    else
        echo "general"
    fi
}

# Smart workflow execution
smart_execute() {
    local prompt=$1
    local force_tool=$2
    local force_tier=$3
    
    echo -e "${BLUE}🎯 Analyzing task...${NC}"
    
    # Classify task
    local task_type=$(classify_task "$prompt")
    echo -e "${CYAN}📋 Task type: $task_type${NC}"
    
    # Select tool
    local tool="${force_tool:-$(select_tool "$task_type" "$prompt")}"
    
    # Determine tier
    local tier="$force_tier"
    if [[ -z "$tier" ]]; then
        case $tool in
            "claude-code") tier="premium" ;;
            "llx-local") tier="local" ;;
            "llx-premium") tier="premium" ;;
            *) tier="balanced" ;;
        esac
    fi
    
    # Execute
    execute_with_tool "$tool" "$prompt" "$tier"
}

# Multi-tool workflow
multi_tool_workflow() {
    local prompt=$1
    
    echo -e "${BLUE}🔄 Multi-tool workflow${NC}"
    
    # Phase 1: Design/Planning (Premium)
    echo -e "\n${PURPLE}Phase 1: Design & Planning${NC}"
    execute_with_tool "claude-code" "Design and plan: $prompt" "premium"
    
    # Phase 2: Implementation (Aider)
    echo -e "\n${GREEN}Phase 2: Implementation${NC}"
    execute_with_tool "aider" "Implement based on design: $prompt" "balanced"
    
    # Phase 3: Testing (Local)
    echo -e "\n${YELLOW}Phase 3: Testing${NC}"
    execute_with_tool "llx-local" "Generate tests for: $prompt" "local"
    
    # Phase 4: Review (Premium)
    echo -e "\n${PURPLE}Phase 4: Review & Optimize${NC}"
    execute_with_tool "claude-code" "Review and optimize implementation" "premium"
}

# Development workflows
dev_workflow() {
    local workflow=$1
    shift
    local args=("$@")
    
    case $workflow in
        "fullstack")
            echo -e "${BLUE}🏗️  Full-Stack Development Workflow${NC}"
            
            # Architecture
            smart_execute "Design full-stack application architecture with React, Node.js, and PostgreSQL"
            
            # Backend implementation
            smart_execute "Implement Node.js backend with Express, authentication, and CRUD APIs" "aider"
            
            # Frontend implementation
            smart_execute "Create React frontend with routing, state management, and responsive design" "vscode"
            
            # Database setup
            smart_execute "Set up PostgreSQL database with migrations and seed data" "aider"
            
            # Testing
            smart_execute "Add comprehensive unit and integration tests" "llx-local"
            
            # Deployment
            smart_execute "Create Docker configuration and deployment scripts" "balanced"
            ;;
            
        "api")
            echo -e "${BLUE}🔌 REST API Development Workflow${NC}"
            
            smart_execute "Design REST API architecture with proper endpoints and data models" "claude-code"
            smart_execute "Implement FastAPI backend with SQLAlchemy and Pydantic" "aider"
            smart_execute "Add authentication, authorization, and security middleware" "aider"
            smart_execute "Generate OpenAPI documentation and interactive docs" "balanced"
            smart_execute "Create comprehensive test suite" "llx-local"
            smart_execute "Add logging, monitoring, and error handling" "balanced"
            ;;
            
        "mobile")
            echo -e "${BLUE}📱 Mobile App Development Workflow${NC}"
            
            smart_execute "Design mobile app architecture with React Native and Redux" "claude-code"
            smart_execute "Implement app navigation and UI components" "vscode"
            smart_execute "Add state management and data persistence" "aider"
            smart_execute "Integrate with backend APIs and handle offline mode" "aider"
            smart_execute "Add push notifications and background tasks" "balanced"
            smart_execute "Create build scripts and deployment configuration" "balanced"
            ;;
            
        "refactor")
            echo -e "${BLUE}🔧 Code Refactoring Workflow${NC}"
            
            smart_execute "Analyze codebase for refactoring opportunities and technical debt" "claude-code"
            smart_execute "Refactor code to improve maintainability and follow best practices" "aider"
            smart_execute "Extract common patterns into reusable components" "aider"
            smart_execute "Optimize performance and eliminate bottlenecks" "balanced"
            smart_execute "Update tests to work with refactored code" "llx-local"
            smart_execute "Update documentation and add migration guides" "llx-local"
            ;;
            
        "test")
            echo -e "${BLUE}🧪 Testing Workflow${NC}"
            
            smart_execute "Analyze existing code to identify test coverage gaps" "balanced"
            smart_execute "Generate unit tests for all functions and methods" "llx-local"
            smart_execute "Create integration tests for API endpoints and database operations" "balanced"
            smart_execute "Add end-to-end tests for critical user flows" "claude-code"
            smart_execute "Set up test automation and CI/CD pipeline" "aider"
            smart_execute "Add performance and load testing" "balanced"
            ;;
            
        *)
            echo -e "${RED}❌ Unknown workflow: $workflow${NC}"
            echo "Available: fullstack, api, mobile, refactor, test"
            return 1
            ;;
    esac
    
    echo -e "\n${GREEN}✅ Workflow completed!${NC}"
}

# Tool-specific commands
tool_command() {
    local tool=$1
    local command=$2
    shift 2
    local args=("$@")
    
    case $tool in
        "aider")
            case $command in
                "install")
                    echo -e "${BLUE}📦 Installing Aider...${NC}"
                    pip install aider-chat
                    ;;
                "setup")
                    echo -e "${BLUE}🔧 Setting up Aider...${NC}"
                    aider --help
                    ;;
                "run")
                    echo -e "${BLUE}🤖 Running Aider...${NC}"
                    aider "${args[@]}"
                    ;;
                *)
                    echo -e "${RED}❌ Unknown Aider command: $command${NC}"
                    echo "Available: install, setup, run"
                    ;;
            esac
            ;;
            
        "claude-code")
            case $command in
                "install")
                    echo -e "${BLUE}📦 Setting up Claude Code...${NC}"
                    echo "Claude Code requires Docker. Run: docker run -it --rm anthropic/claude-code"
                    ;;
                "setup")
                    echo -e "${BLUE}🔧 Testing Claude Code...${NC}"
                    docker run --rm anthropic/claude-code --version
                    ;;
                "run")
                    echo -e "${BLUE}🧠 Running Claude Code...${NC}"
                    docker run -it --rm -v "$(pwd):/workspace" anthropic/claude-code "${args[@]}"
                    ;;
                *)
                    echo -e "${RED}❌ Unknown Claude Code command: $command${NC}"
                    echo "Available: install, setup, run"
                    ;;
            esac
            ;;
            
        "vscode")
            case $command in
                "setup")
                    echo -e "${BLUE}🔧 Setting up VS Code for AI development...${NC}"
                    echo "Install these extensions:"
                    echo "  - RooCode (AI assistant)"
                    echo "  - GitHub Copilot"
                    echo "  - Python/TypeScript/React extensions"
                    ;;
                "open")
                    echo -e "${BLUE}💻 Opening VS Code...${NC}"
                    code .
                    ;;
                *)
                    echo -e "${RED}❌ Unknown VS Code command: $command${NC}"
                    echo "Available: setup, open"
                    ;;
            esac
            ;;
            
        *)
            echo -e "${RED}❌ Unknown tool: $tool${NC}"
            echo "Available tools: aider, claude-code, vscode"
            ;;
    esac
}

# Print usage
print_usage() {
    echo -e "${BLUE}Cloud-Local Integration Manager${NC}"
    echo -e "${CYAN}Optimized development with cloud LLMs and local tools${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS] <command> [args]"
    echo ""
    echo "Commands:"
    echo "  smart <prompt>              Execute with intelligent tool selection"
    echo "  multi <prompt>              Multi-tool workflow for complex tasks"
    echo "  workflow <type>             Run predefined development workflow"
    echo "  tool <tool> <command>       Tool-specific commands"
    echo "  check                       Check tool availability"
    echo ""
    echo "Workflows:"
    echo "  fullstack                   Complete application development"
    echo "  api                         REST API development"
    echo "  mobile                      Mobile app development"
    echo "  refactor                    Code refactoring"
    echo "  test                        Testing implementation"
    echo ""
    echo "Tool Commands:"
    echo "  tool aider install/setup/run  Manage Aider"
    echo "  tool claude-code install/setup/run  Manage Claude Code"
    echo "  tool vscode setup/open       Manage VS Code"
    echo ""
    echo "Options:"
    echo "  -t, --tool TOOL             Force specific tool (aider/claude-code/vscode/llx)"
    echo "  -T, --tier TIER             Force model tier (cheap/balanced/premium/local)"
    echo "  -v, --verbose               Verbose output"
    echo "  -h, --help                  Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 smart 'Implement user authentication'              # Auto-select tool"
    echo "  $0 smart 'Design system architecture' --tool claude-code  # Force tool"
    echo "  $0 multi 'Create e-commerce platform'                 # Multi-tool workflow"
    echo "  $0 workflow fullstack                                # Complete workflow"
    echo "  $0 tool aider install                                # Install Aider"
}

# Parse arguments
FORCE_TOOL=""
FORCE_TIER=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tool)
            FORCE_TOOL="$2"
            shift 2
            ;;
        -T|--tier)
            FORCE_TIER="$2"
            shift 2
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

# Execute command
case $COMMAND in
    "check")
        check_tools
        ;;
    "smart")
        if [[ -z "$1" ]]; then
            echo -e "${RED}❌ Missing prompt${NC}"
            exit 1
        fi
        smart_execute "$1" "$FORCE_TOOL" "$FORCE_TIER"
        ;;
    "multi")
        if [[ -z "$1" ]]; then
            echo -e "${RED}❌ Missing prompt${NC}"
            exit 1
        fi
        multi_tool_workflow "$1"
        ;;
    "workflow")
        if [[ -z "$1" ]]; then
            echo -e "${RED}❌ Missing workflow type${NC}"
            exit 1
        fi
        dev_workflow "$1" "$@"
        ;;
    "tool")
        if [[ -z "$1" || -z "$2" ]]; then
            echo -e "${RED}❌ Missing tool or command${NC}"
            exit 1
        fi
        tool_command "$1" "$2" "$@"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        print_usage
        exit 1
        ;;
esac
