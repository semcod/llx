#!/usr/bin/env bash
# llx Docker Integration Example Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 llx Docker Integration Example Runner${NC}"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found. Please run from examples/docker directory${NC}"
    exit 1
fi

# Check Docker installation
echo -e "${BLUE}🔍 Checking Docker installation...${NC}"
if ! command -v docker > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker daemon first"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed and running${NC}"

# Check docker-compose
echo -e "${BLUE}🔍 Checking docker-compose...${NC}"
if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}❌ docker-compose is not installed${NC}"
    echo "Please install docker-compose first"
    exit 1
fi

echo -e "${GREEN}✓ docker-compose is available${NC}"

# Check if we're running in Docker
if [ -f "/.dockerenv" ]; then
    echo -e "${BLUE}📦 Running inside Docker container${NC}"
    IN_DOCKER=true
else
    echo -e "${BLUE}🖥️  Running on host machine${NC}"
    IN_DOCKER=false
fi

# Check if Docker services are running
echo -e "${BLUE}🔍 Checking Docker services...${NC}"

# Get docker-compose command
if docker compose version > /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Check for running containers
RUNNING_CONTAINERS=$(docker ps --format "table {{.Names}}" | grep -E "llx-|llx_" | wc -l)
if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $RUNNING_CONTAINERS llx containers running${NC}"
    
    # Show running containers
    echo -e "${BLUE}📋 Running containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "llx-|llx_" || true
else
    echo -e "${YELLOW}⚠️  No llx containers running${NC}"
    echo ""
    echo -e "${BLUE}💡 Start Docker services:${NC}"
    echo "  ./docker-manage.sh dev          # Start development stack"
    echo "  ./docker-manage.sh prod         # Start production stack"
    echo ""
    echo "Or start manually:"
    echo "  $COMPOSE_CMD -f docker-compose.yml up -d"
fi

# Check required services
echo -e "${BLUE}🔍 Checking required services...${NC}"

# Check llx API
if curl -s http://localhost:4000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ llx API is running (http://localhost:4000)${NC}"
else
    echo -e "${YELLOW}⚠️  llx API is not running on port 4000${NC}"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running (localhost:6379)${NC}"
else
    echo -e "${YELLOW}⚠️  Redis is not running on port 6379${NC}"
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running (http://localhost:11434)${NC}"
    OLLAMA_MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('models', [])))" 2>/dev/null || echo "0")
    echo -e "${BLUE}   📦 Available models: $OLLAMA_MODELS${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama is not running on port 11434${NC}"
fi

# Check WebUI
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ WebUI is running (http://localhost:3000)${NC}"
else
    echo -e "${YELLOW}⚠️  WebUI is not running on port 3000${NC}"
fi

# Check Grafana
if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is running (http://localhost:3001)${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana is not running on port 3001${NC}"
fi

# Load environment variables
if [ -f "../../.env" ]; then
    echo -e "${BLUE}📋 Loading environment variables...${NC}"
    set -a
    source ../../.env 2>/dev/null || true
    set +a
    echo "✓ Environment loaded"
elif [ -f ".env" ]; then
    echo -e "${BLUE}📋 Loading environment variables...${NC}"
    set -a
    source .env 2>/dev/null || true
    set +a
    echo "✓ Environment loaded"
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
fi

# Check Python dependencies
echo -e "${BLUE}🔍 Checking Python dependencies...${NC}"

PYTHON_CMD="python3"
if [ "$IN_DOCKER" = "true" ]; then
    # In Docker, use the installed Python
    PYTHON_CMD="python"
else
    # On host, try to use project virtual environment
    if [ -d "../../.venv" ]; then
        PYTHON_CMD="../../.venv/bin/python"
        echo -e "${BLUE}📦 Using project virtual environment${NC}"
    fi
fi

# Check for required packages
if ! $PYTHON_CMD -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing requests...${NC}"
    $PYTHON_CMD -m pip install requests
fi

if ! $PYTHON_CMD -c "import redis" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing redis...${NC}"
    $PYTHON_CMD -m pip install redis
fi

# Set PYTHONPATH
if [ "$IN_DOCKER" = "true" ]; then
    export PYTHONPATH="/app:$PYTHONPATH"
else
    export PYTHONPATH="$(pwd)/../..:$PYTHONPATH"
fi

# Run the example
echo -e "${BLUE}🏃 Running Docker integration example...${NC}"
echo ""

# Run with timeout to prevent hanging
timeout 30s $PYTHON_CMD main.py "$@" || {
    echo -e "${YELLOW}⚠️  Example timed out or failed${NC}"
    echo "This might be normal if services are not running"
}

echo ""
echo -e "${GREEN}✅ Example completed!${NC}"
echo ""
echo -e "${BLUE}💡 Docker Management Commands:${NC}"
echo "  ./docker-manage.sh dev              # Start development stack"
echo "  ./docker-manage.sh prod             # Start production stack"
echo "  ./docker-manage.sh status           # Check container status"
echo "  ./docker-manage.sh logs dev          # View development logs"
echo "  ./docker-manage.sh restart dev       # Restart services"
echo "  ./docker-manage.sh backup            # Create backups"
echo "  ./docker-manage.sh clean             # Clean up resources"
echo ""
echo -e "${BLUE}🔗 Service URLs:${NC}"
echo "  • llx API:        http://localhost:4000"
echo "  • WebUI:          http://localhost:3000"
echo "  • Grafana:        http://localhost:3001"
echo "  • Prometheus:     http://localhost:9090"
echo "  • VS Code:        http://localhost:8080"
echo "  • Ollama:         http://localhost:11434"
echo "  • Redis:          localhost:6379"
echo ""
echo -e "${BLUE}📚 Next steps:${NC}"
echo "  • Try other examples: cd ../basic && ./run.sh"
echo "  • Read Docker documentation: cat docker-compose.yml"
echo "  • Check service health: curl http://localhost:4000/health"
echo "  • View logs: ./docker-manage.sh logs dev"
