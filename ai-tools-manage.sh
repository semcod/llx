#!/bin/bash
# AI Tools Management Script
# Manages AI tools container and provides convenient commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose-dev.yml"
PROJECT_NAME="llx-dev"
CONTAINER_NAME="llx-ai-tools-dev"

print_header() {
    echo -e "${BLUE}🤖 AI Tools Management${NC}"
    echo "=========================="
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Get docker-compose command
get_compose_cmd() {
    if docker compose version > /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# Check if container is running
is_running() {
    docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"
}

# Start AI tools
start_ai_tools() {
    print_header
    echo "Starting AI tools environment..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    # Start llx-api first if not running
    if ! docker ps --format "table {{.Names}}" | grep -q "llx-api-dev"; then
        echo "🔧 Starting llx API first..."
        $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME up -d llx-api
        
        # Wait for llx API to be ready
        echo "⏳ Waiting for llx API to be ready..."
        until curl -s http://localhost:4000/health > /dev/null 2>&1; do
            sleep 2
        done
        print_status "llx API is ready!"
    fi
    
    # Start AI tools
    echo "🔧 Starting AI tools container..."
    $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME up -d ai-tools
    
    # Wait for container to be ready
    echo "⏳ Waiting for AI tools to be ready..."
    sleep 5
    
    if is_running; then
        print_status "AI tools environment started!"
        echo ""
        echo "📋 Available commands:"
        echo "  ./ai-tools-manage.sh shell     - Access AI tools shell"
        echo "  ./ai-tools-manage.sh status     - Check status"
        echo "  ./ai-tools-manage.sh test       - Test connectivity"
        echo "  ./ai-tools-manage.sh logs       - View logs"
        echo "  ./ai-tools-manage.sh stop       - Stop AI tools"
        echo ""
        echo "🚀 Quick start:"
        echo "  ./ai-tools-manage.sh shell"
        echo "  aider-llx                    # Start Aider with llx API"
        echo "  ai-status                    # Check status"
    else
        print_error "Failed to start AI tools"
        echo ""
        echo "🔍 Check logs:"
        echo "  ./ai-tools-manage.sh logs"
        exit 1
    fi
}

# Stop AI tools
stop_ai_tools() {
    print_header
    echo "Stopping AI tools environment..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f $COMPOSE_FILE -p $PROJECT_NAME stop ai-tools
    
    print_status "AI tools stopped!"
}

# Access AI tools shell
shell() {
    print_header
    echo "Accessing AI tools shell..."
    
    if ! is_running; then
        print_error "AI tools container is not running"
        echo ""
        echo "🚀 Start it first:"
        echo "  ./ai-tools-manage.sh start"
        exit 1
    fi
    
    echo "🤖 Entering AI tools environment..."
    echo ""
    echo "📋 Available commands:"
    echo "  aider-llx      - Start Aider with llx API"
    echo "  aider-local     - Start Aider with local Ollama"
    echo "  claude-llx      - Start Claude Code with llx API"
    echo "  claude-local     - Start Claude Code with local Ollama"
    echo "  ai-status       - Check status"
    echo "  ai-test         - Test connectivity"
    echo "  ai-chat         - Quick chat test"
    echo ""
    echo "📁 Workspace: /workspace"
    echo "📁 Examples: /workspace/ai-tools-examples"
    echo ""
    
    docker exec -it $CONTAINER_NAME /bin/bash
}

# Check status
status() {
    print_header
    echo "AI Tools Status:"
    echo ""
    
    if is_running; then
        print_status "Container is running"
        
        echo ""
        echo "🔍 Service Status:"
        docker exec $CONTAINER_NAME ai-tools-status 2>/dev/null || {
            echo "⚠️  Status script not available, checking manually..."
            
            # Check llx API
            if docker exec $CONTAINER_NAME curl -s http://llx-api:4000/health > /dev/null 2>&1; then
                echo "  llx API: ✅ Running"
            else
                echo "  llx API: ❌ Down"
            fi
            
            # Check Ollama
            if docker exec $CONTAINER_NAME curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1; then
                echo "  Ollama: ✅ Running"
            else
                echo "  Ollama: ❌ Down"
            fi
        }
        
        echo ""
        echo "📦 Container Info:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "$CONTAINER_NAME"
        
    else
        print_error "Container is not running"
        echo ""
        echo "🚀 Start it with:"
        echo "  ./ai-tools-manage.sh start"
    fi
}

# Test connectivity
test() {
    print_header
    echo "Testing AI tools connectivity..."
    echo ""
    
    if ! is_running; then
        print_error "AI tools container is not running"
        echo ""
        echo "🚀 Start it first:"
        echo "  ./ai-tools-manage.sh start"
        exit 1
    fi
    
    echo "🧪 Running connectivity tests..."
    docker exec $CONTAINER_NAME ai-tools-test 2>/dev/null || {
        echo "⚠️  Test script not available, running manual tests..."
        
        # Test llx API
        echo "🔍 Testing llx API..."
        if docker exec $CONTAINER_NAME curl -s http://llx-api:4000/health > /dev/null 2>&1; then
            print_status "llx API reachable"
        else
            print_error "llx API not reachable"
        fi
        
        # Test Ollama
        echo "🔍 Testing Ollama..."
        if docker exec $CONTAINER_NAME curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1; then
            print_status "Ollama reachable"
        else
            print_error "Ollama not reachable"
        fi
        
        # Test Python packages
        echo "🔍 Testing Python packages..."
        packages=("aider" "claude_code")
        for package in "${packages[@]}"; do
            if docker exec $CONTAINER_NAME python -c "import $package" 2>/dev/null; then
                print_status "$package installed"
            else
                print_warning "$package not installed"
            fi
        done
    }
    
    echo ""
    echo "🎉 Test completed!"
}

# View logs
logs() {
    print_header
    echo "AI Tools Logs:"
    echo ""
    
    if is_running; then
        docker logs -f $CONTAINER_NAME
    else
        print_error "Container is not running"
        echo ""
        echo "🚀 Start it first:"
        echo "  ./ai-tools-manage.sh start"
        exit 1
    fi
}

# Restart AI tools
restart() {
    print_header
    echo "Restarting AI tools..."
    
    stop_ai_tools
    sleep 2
    start_ai_tools
}

# Quick chat test
quick_chat() {
    print_header
    echo "Quick Chat Test"
    echo "================"
    
    if ! is_running; then
        print_error "AI tools container is not running"
        echo ""
        echo "🚀 Start it first:"
        echo "  ./ai-tools-manage.sh start"
        exit 1
    fi
    
    local model="${1:-qwen2.5-coder:7b}"
    local message="${2:-Hello! Write a simple Python function.}"
    
    echo "🤖 Chat with $model"
    echo "Message: $message"
    echo ""
    echo "Response:"
    echo "--------"
    
    docker exec $CONTAINER_NAME ai-chat "$model" "$message" 2>/dev/null || {
        echo "❌ Chat test failed"
        echo ""
        echo "🔍 Try manual test:"
        echo "  ./ai-tools-manage.sh shell"
        echo "  ai-chat '$model' '$message'"
    }
}

# Show help
help() {
    print_header
    echo "AI Tools Management Commands:"
    echo ""
    echo "🚀 Start/Stop:"
    echo "  start              - Start AI tools environment"
    echo "  stop               - Stop AI tools environment"
    echo "  restart            - Restart AI tools"
    echo ""
    echo "🔧 Management:"
    echo "  shell              - Access AI tools shell"
    echo "  status             - Check status"
    echo "  logs               - View logs"
    echo "  test               - Test connectivity"
    echo ""
    echo "🧪 Testing:"
    echo "  chat [model] [msg] - Quick chat test"
    echo ""
    echo "ℹ️  Help:"
    echo "  help               - Show this help"
    echo ""
    echo "📋 Examples:"
    echo "  ./ai-tools-manage.sh start"
    echo "  ./ai-tools-manage.sh shell"
    echo "  ./ai-tools-manage.sh test"
    echo "  ./ai-tools-manage.sh chat qwen2.5-coder:7b 'Hello world'"
}

# Main command handling
case "${1:-help}" in
    "start")
        start_ai_tools
        ;;
    "stop")
        stop_ai_tools
        ;;
    "restart")
        restart
        ;;
    "shell")
        shell
        ;;
    "status")
        status
        ;;
    "logs")
        logs
        ;;
    "test")
        test
        ;;
    "chat")
        quick_chat "$2" "$3"
        ;;
    "help"|*)
        help
        ;;
esac
