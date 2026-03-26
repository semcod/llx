#!/bin/bash
# One-liner full-stack application generator using LLX

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[LLX]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to generate app
generate_app() {
    local app_type=$1
    local app_name=$2
    local tier=${3:-"balanced"}
    local provider=${4:-""}
    
    print_status "Generating $app_type application: $app_name"
    
    # Create project directory
    mkdir -p "$app_name"
    cd "$app_name"
    
    # Build prompt based on app type
    case $app_type in
        "react")
            prompt="Create a complete React TypeScript application with: 
            - Modern React with hooks and functional components
            - TypeScript for type safety
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
            prompt="Create a full Next.js 14 application with:
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
            prompt="Create a complete FastAPI application with:
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
        "mern")
            prompt="Create a complete MERN stack application with:
            - MongoDB with Mongoose ODM
            - Express.js REST API
            - React frontend with TypeScript
            - Node.js backend with ES6+
            - JWT authentication system
            - User registration and login
            - CRUD operations for resources
            - File upload with Multer
            - React Router for navigation
            - Axios for API calls
            - Context API for state management
            - Bootstrap or Material-UI
            - Form validation
            - Error handling
            - Docker containers for each service
            - docker-compose for orchestration"
            ;;
        "python-cli")
            prompt="Create a Python CLI application with:
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
        "electron")
            prompt="Create an Electron desktop application with:
            - React frontend with TypeScript
            - Electron main and preload scripts
            - IPC communication between main and renderer
            - Native menu and tray
            - File system access
            - Auto-updater configuration
            - Code signing setup
            - Packaging for Windows/Mac/Linux
            - Modern build tools with Webpack
            - Hot reload for development
            - Application icon and branding"
            ;;
        "flutter")
            prompt="Create a complete Flutter mobile application with:
            - Material Design 3 UI
            - Clean architecture with BLoC pattern
            - REST API integration with Dio
            - Local storage with Hive
            - Authentication with JWT
            - Push notifications setup
            - Deep linking support
            - Internationalization (i18n)
            - Unit and widget tests
            - CI/CD with GitHub Actions
            - App Store deployment ready
            - Responsive design for tablets"
            ;;
        "go-api")
            prompt="Create a Go REST API with:
            - Clean architecture pattern
            - Gin web framework
            - GORM for database ORM
            - PostgreSQL database
            - JWT middleware
            - Graceful shutdown
            - Structured logging with logrus
            - Configuration management with Viper
            - Swagger documentation
            - Rate limiting
            - CORS middleware
            - Unit tests with testify
            - Docker multi-stage build
            - Makefile for common tasks"
            ;;
        *)
            print_error "Unknown app type: $app_type"
            exit 1
            ;;
    esac
    
    # Add execution instruction to prompt
    prompt="$prompt
    
    IMPORTANT: Generate all necessary files and directories. 
    Create a working application that can be run immediately.
    Include package.json/requirements.txt with all dependencies.
    Add clear setup and run instructions in README.md."
    
    # Build LLX command
    llx_cmd="llx chat --model "$tier" --task refactor"
    
    if [ -n "$provider" ]; then
        llx_cmd="$llx_cmd --provider $provider"
    fi
    
    llx_cmd="$llx_cmd --prompt \"$prompt\""
    
    print_status "Executing: $llx_cmd"
    
    # Execute LLX command
    if eval "$llx_cmd" > generation_output.txt 2>&1; then
        print_success "Application generated successfully!"
        
        # Show what was created
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

# Function to show usage
show_usage() {
    echo "LLX Full-Stack App Generator"
    echo "Usage: $0 [OPTIONS] <app_type> <app_name>"
    echo ""
    echo "App Types:"
    echo "  react       React TypeScript app"
    echo "  nextjs      Next.js full-stack app"
    echo "  fastapi     FastAPI Python backend"
    echo "  mern        MERN stack app"
    echo "  python-cli  Python CLI tool"
    echo "  electron    Electron desktop app"
    echo "  flutter     Flutter mobile app"
    echo "  go-api      Go REST API"
    echo ""
    echo "Options:"
    echo "  -t, --tier TIER       Model tier (cheap/balanced/premium) [default: balanced]"
    echo "  -p, --provider PROVIDER  LLM provider (anthropic/openai/openrouter)"
    echo "  -h, --help            Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 react my-app                    # React app with balanced model"
    echo "  $0 -t premium nextjs blog           # Next.js app with premium model"
    echo "  $0 -p anthropic fastapi my-api      # FastAPI with Anthropic"
    echo "  $0 mern ecommerce -t premium        # MERN stack with premium model"
}

# Parse command line arguments
TIER="balanced"
PROVIDER=""

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
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Check arguments
if [ $# -lt 2 ]; then
    print_error "Missing required arguments"
    show_usage
    exit 1
fi

APP_TYPE=$1
APP_NAME=$2

# Validate tier
if [[ ! "$TIER" =~ ^(cheap|balanced|premium)$ ]]; then
    print_error "Invalid tier. Must be: cheap, balanced, or premium"
    exit 1
fi

# Check if LLX is available
if ! command -v llx &> /dev/null; then
    print_error "LLX is not installed or not in PATH"
    exit 1
fi

# Start generation
print_status "Starting application generation..."
print_status "App Type: $APP_TYPE"
print_status "App Name: $APP_NAME"
print_status "Model Tier: $TIER"
if [ -n "$PROVIDER" ]; then
    print_status "Provider: $PROVIDER"
fi

generate_app "$APP_TYPE" "$APP_NAME" "$TIER" "$PROVIDER"

print_success "Done! Your application is ready in: $APP_NAME/"
