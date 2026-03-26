#!/bin/bash
# LLX Full-Stack App Generator - Simplified version
# Uses LLX directly instead of Python wrapper

set -e

# Default values
APP_TYPE=""
APP_NAME=""
TIER="balanced"
PROVIDER=""
USE_LOCAL=""
OUTPUT_DIR=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print functions
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Help function
show_help() {
    cat << EOF
LLX Full-Stack App Generator

Usage: $0 [OPTIONS] <app_type> <app_name>

App Types:
  react       React TypeScript app
  nextjs      Next.js full-stack app
  fastapi     FastAPI Python backend
  mern        MERN stack app
  python-cli  Python CLI tool
  electron    Electron desktop app
  flutter     Flutter mobile app
  go-api      Go REST API

Options:
  -t, --tier TIER       Model tier (cheap/balanced/premium) [default: balanced]
  -p, --provider PROVIDER LLM provider (anthropic/openai/openrouter)
  -l, --local           Use local model instead of cloud
  -o, --output DIR      Output directory [default: app_name]
  -h, --help            Show this help

Examples:
  $0 react my-app                    # React app with balanced model
  $0 -t premium nextjs blog           # Next.js app with premium model
  $0 -p anthropic fastapi my-api      # FastAPI with Anthropic
  $0 --local python-cli tool          # Python CLI with local model

EOF
}

# Parse command line arguments
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
            USE_LOCAL="--local"
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$APP_TYPE" ]; then
                APP_TYPE="$1"
            elif [ -z "$APP_NAME" ]; then
                APP_NAME="$1"
            else
                print_error "Unknown argument: $1"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Check arguments
if [ -z "$APP_TYPE" ] || [ -z "$APP_NAME" ]; then
    print_error "Missing required arguments"
    show_help
    exit 1
fi

# Set output directory
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="$APP_NAME"
fi

# Validate tier
if [[ ! "$TIER" =~ ^(cheap|balanced|premium|openrouter/.*)$ ]]; then
    print_error "Invalid tier. Must be: cheap, balanced, premium, or openrouter model"
    exit 1
fi

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    print_error "LLX is not installed or not in PATH"
    exit 1
fi

# App type prompts
get_app_prompt() {
    local app_type="$1"
    case $app_type in
        "react")
            echo "Create a React TypeScript application with:
            - TypeScript and ESLint
            - Tailwind CSS for styling
            - React Router for navigation
            - State management with Zustand
            - API integration with axios
            - Form handling with react-hook-form
            - Unit tests with Jest and React Testing Library
            - ESLint and Prettier configured
            - Build and deployment scripts
            - README with setup instructions"
            ;;
        "nextjs")
            echo "Create a full Next.js 14 application with:
            - TypeScript and ESLint
            - Tailwind CSS for styling
            - App Router structure
            - Server and client components
            - API routes for backend
            - Authentication with NextAuth.js
            - Prisma for database ORM
            - PostgreSQL database schema
            - Middleware for auth
            - Environment variables setup
            - Docker configuration
            - Vercel deployment ready"
            ;;
        "fastapi")
            echo "Create a complete FastAPI application with:
            - Python 3.11+ with type hints
            - SQLAlchemy ORM with Alembic migrations
            - PostgreSQL database models
            - Pydantic schemas for request/response
            - JWT authentication with bcrypt
            - Role-based access control
            - RESTful API endpoints
            - OpenAPI/Swagger documentation
            - CORS middleware
            - Request validation and error handling
            - Unit tests with pytest
            - Docker and docker-compose setup
            - Environment configuration"
            ;;
        "python-cli")
            echo "Create a Python CLI application with:
            - Click framework for CLI
            - Rich library for beautiful output
            - Configuration management with YAML
            - Logging with structlog
            - Async/await support
            - Command subcommands
            - Progress bars and spinners
            - Table output formatting
            - Error handling and validation
            - Unit tests with pytest
            - Setup.py for distribution
            - README with usage examples"
            ;;
        *)
            print_error "Unknown app type: $app_type"
            exit 1
            ;;
    esac
}

# Main generation logic
main() {
    print_status "Starting application generation..."
    echo -e "${CYAN}App Type: $APP_TYPE${NC}"
    echo -e "${CYAN}App Name: $APP_NAME${NC}"
    echo -e "${CYAN}Output Dir: $OUTPUT_DIR${NC}"
    echo -e "${CYAN}Model Tier: $TIER${NC}"
    
    # Get the prompt for app type
    prompt=$(get_app_prompt "$APP_TYPE")
    
    # Add execution instruction
    prompt="$prompt
    
    IMPORTANT: Generate all necessary files and directories. 
    Create a working application that can be run immediately.
    Include package.json/requirements.txt with all dependencies.
    Add clear setup and run instructions in README.md."
    
    echo
    print_status "Generating $APP_TYPE application: $APP_NAME"
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    cd "$OUTPUT_DIR"
    
    # Build LLX command
    if [ -n "$USE_LOCAL" ]; then
        llx_cmd="llx chat $USE_LOCAL --task refactor"
    else
        if [ "$TIER" = "openrouter/deepseek/deepseek-chat-v3-0324" ]; then
            llx_cmd="llx chat --model openrouter/deepseek/deepseek-chat-v3-0324 --task refactor"
        else
            llx_cmd="llx chat --model $TIER --task refactor"
        fi
    fi
    
    # Note: provider not supported in llx chat
    llx_cmd="$llx_cmd --prompt \"$prompt\""
    
    print_status "Executing: $llx_cmd"
    
    # Execute LLX command
    if eval "$llx_cmd" > generation_output.txt 2>&1; then
        print_success "Application generated successfully!"
        
        # Show what was created
        echo
        print_status "Generated files:"
        find . -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.json" -o -name "*.md" | head -20
        
        # Check for package manager files
        if [ -f "package.json" ]; then
            print_status "Installing Node.js dependencies..."
            npm install
        elif [ -f "requirements.txt" ]; then
            print_status "Installing Python dependencies..."
            pip install -r requirements.txt
        elif [ -f "go.mod" ]; then
            print_status "Installing Go modules..."
            go mod download
        fi
        
        print_success "Setup complete! Check README.md for run instructions."
    else
        print_error "Failed to generate application"
        cat generation_output.txt
        exit 1
    fi
    
    # Clean up
    rm -f generation_output.txt
}

# Run main function
main
